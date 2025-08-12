"""
Itinerary Generator API
Matches trips with standard packages and analyzes alignment using AI
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Import the LLM utils
from frappe_ai.utils.llm_utils import analyze_trip_package_alignment

@frappe.whitelist()
def analyze_trip_package_match(trip_name: str) -> Dict[str, Any]:
    """
    Analyzes a trip against available standard packages and returns the best match
    with AI-powered requirement analysis.
    
    Args:
        trip_name: Name/ID of the Trip document
    
    Returns:
        Dict containing:
        - selected_package: Best matching package details
        - match_score_breakdown: Detailed scoring for each criterion
        - ai_analysis: LLM analysis of requirement alignment
        - recommendations: Actionable recommendations
    """
    try:
        # Validate and fetch the trip
        if not trip_name:
            frappe.throw(_("Trip name is required"))
        
        trip = frappe.get_doc("Trip", trip_name)
        
        # Get all active standard packages
        packages = get_active_packages()
        
        if not packages:
            return {
                "success": False,
                "message": "No active standard packages found",
                "selected_package": None,
                "ai_analysis": None
            }
        
        # Score and rank packages
        scored_packages = []
        for package in packages:
            score, breakdown = calculate_package_score(trip, package)
            scored_packages.append({
                "package": package,
                "total_score": score,
                "score_breakdown": breakdown
            })
        
        # Sort by total score (highest first)
        scored_packages.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Log for debugging
        frappe.log_error(
            f"Trip {trip_name} - Top 3 packages:\n" + 
            "\n".join([f"{i+1}. {p['package'].package_name} - Score: {p['total_score']:.1f} (Dest: {p['score_breakdown']['destination']['percentage']:.0f}%)" 
                      for i, p in enumerate(scored_packages[:3])]),
            "Package Scoring Debug"
        )
        
        # Filter packages that have at least some destination match (if trip has destinations)
        if trip.destination_city and len(trip.destination_city) > 0:
            # Keep only packages with >0% destination match
            packages_with_dest_match = [p for p in scored_packages if p["score_breakdown"]["destination"]["percentage"] > 0]
            
            if packages_with_dest_match:
                best_match = packages_with_dest_match[0]
            else:
                # No packages match the destination - this is a critical issue
                frappe.log_error(
                    f"No packages match destination for trip {trip_name}. Trip requires: {[d.destination for d in trip.destination_city if hasattr(d, 'destination')]}",
                    "No Destination Match"
                )
                # Still select best overall but flag it
                best_match = scored_packages[0] if scored_packages else None
        else:
            # No destination requirement, use best overall score
            best_match = scored_packages[0] if scored_packages else None
        
        if not best_match or best_match["total_score"] < 10:  # Minimum threshold
            return {
                "success": False,
                "message": "No suitable package found for the trip requirements",
                "selected_package": None,
                "ai_analysis": None,
                "all_scores": scored_packages[:3] if scored_packages else []
            }
        
        # Prepare data for AI analysis
        trip_data = prepare_trip_data(trip)
        package_data = prepare_package_data(best_match["package"])
        
        # Get AI analysis
        ai_result = analyze_trip_package_alignment(
            trip_data=trip_data,
            package_data=package_data
        )
        
        # Check if there's a destination mismatch
        has_destination_mismatch = (
            trip.destination_city and 
            len(trip.destination_city) > 0 and 
            best_match["score_breakdown"]["destination"]["percentage"] == 0
        )
        
        # Format the response
        response = {
            "success": True,
            "selected_package": {
                "name": best_match["package"].name,
                "package_name": best_match["package"].package_name,
                "package_code": best_match["package"].package_code,
                "description": best_match["package"].description,
                "base_cost": best_match["package"].base_cost,
                "currency": best_match["package"].currency,
                "dmc": best_match["package"].dmc,
                "hotel_category": best_match["package"].hotel if hasattr(best_match["package"], "hotel") else None,
                "no_of_days": best_match["package"].no_of_days if hasattr(best_match["package"], "no_of_days") else None,
                "no_of_nights": best_match["package"].no_of_nights if hasattr(best_match["package"], "no_of_nights") else None
            },
            "match_score": best_match["total_score"],
            "match_score_breakdown": best_match["score_breakdown"],
            "destination_mismatch_warning": has_destination_mismatch,
            "ai_analysis": ai_result.get("parsed_content") if ai_result.get("success") else None,
            "ai_analysis_raw": ai_result.get("content") if not ai_result.get("parsed_content") else None,
            "ai_error": ai_result.get("error") if not ai_result.get("success") else None,
            "alternative_packages": [
                {
                    "name": p["package"].name,
                    "package_name": p["package"].package_name,
                    "score": p["total_score"],
                    "main_gaps": identify_main_gaps(p["score_breakdown"])
                }
                for p in scored_packages[1:4] if p["total_score"] > 10
            ]
        }
        
        # Add recommendations based on AI analysis
        if ai_result.get("success") and ai_result.get("parsed_content"):
            response["recommendations"] = format_recommendations(
                ai_result["parsed_content"],
                best_match["score_breakdown"]
            )
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Error in analyze_trip_package_match: {str(e)}", "Itinerary Generator")
        return {
            "success": False,
            "error": str(e),
            "message": "An error occurred while analyzing the trip"
        }

def get_active_packages() -> List[frappe._dict]:
    """Fetches all active standard packages."""
    packages = frappe.get_all(
        "Standard Package",
        filters={"status": "Active"},
        fields=[
            "name", "package_name", "package_code", "description",
            "valid_from", "valid_to", "min_group_size", "max_group_size",
            "currency", "dmc", "itinerary_data",
            "markup_percentage", "base_cost", "notes", "terms_and_conditions",
            "no_of_days", "no_of_nights", "hotel"
        ]
    )
    
    # Fetch child table data for each package
    for package in packages:
        # Get destinations child table
        package["destinations"] = frappe.get_all(
            "Trip Destination",
            filters={"parent": package.name, "parenttype": "Standard Package"},
            fields=["destination"]
        )
        
        # Debug logging for Singapore package
        if "Singapore" in package.package_name:
            frappe.log_error(
                f"Singapore package {package.name}: destinations = {package['destinations']}",
                "Singapore Package Debug"
            )
        
        # Get activities child table
        package["activities"] = frappe.get_all(
            "Activity Child Table",
            filters={"parent": package.name, "parenttype": "Standard Package"},
            fields=["activity"]
        )
        
        # Get package inclusions child table
        package["package_inclusions"] = frappe.get_all(
            "Package Inclusion Child Table",
            filters={"parent": package.name, "parenttype": "Standard Package"},
            fields=["*"]
        )
        
        # Get package exclusions child table
        package["package_exclusions"] = frappe.get_all(
            "Package Exclusion Child Table",
            filters={"parent": package.name, "parenttype": "Standard Package"},
            fields=["*"]
        )
        
        # Get target audience child table
        package["target_audience"] = frappe.get_all(
            "Target Audience Child Table",
            filters={"parent": package.name, "parenttype": "Standard Package"},
            fields=["*"]
        )
        
        # Get exclusion criteria child table
        package["exclusion_criteria"] = frappe.get_all(
            "Exclusion Criteria Child Table",
            filters={"parent": package.name, "parenttype": "Standard Package"},
            fields=["*"]
        )
    
    return packages

def calculate_package_score(trip: Any, package: frappe._dict) -> Tuple[float, Dict[str, Any]]:
    """
    Calculates a matching score between a trip and a package.
    
    Returns:
        Tuple of (total_score, score_breakdown)
    """
    score_breakdown = {}
    weights = {
        "destination": 30,
        "dates": 25,
        "activities": 20,
        "group_size": 15,
        "budget": 10
    }
    
    # Calculate group size from passenger_details
    group_size = len(trip.passenger_details) if trip.passenger_details else (trip.pax if trip.pax else 0)
    
    # 1. Destination Match (30 points)
    destination_score = calculate_destination_match(trip, package)
    score_breakdown["destination"] = {
        "score": destination_score * weights["destination"],
        "max_score": weights["destination"],
        "percentage": destination_score * 100
    }
    
    # 2. Date Compatibility (25 points)
    date_score = calculate_date_compatibility(trip, package)
    score_breakdown["dates"] = {
        "score": date_score * weights["dates"],
        "max_score": weights["dates"],
        "percentage": date_score * 100
    }
    
    # 3. Activity Match (20 points)
    activity_score = calculate_activity_match(trip, package)
    score_breakdown["activities"] = {
        "score": activity_score * weights["activities"],
        "max_score": weights["activities"],
        "percentage": activity_score * 100
    }
    
    # 4. Group Size Compatibility (15 points)
    group_score = calculate_group_size_compatibility(trip, package, group_size)
    score_breakdown["group_size"] = {
        "score": group_score * weights["group_size"],
        "max_score": weights["group_size"],
        "percentage": group_score * 100,
        "group_size": group_size
    }
    
    # 5. Budget Alignment (10 points)
    budget_score = calculate_budget_alignment(trip, package, group_size)
    score_breakdown["budget"] = {
        "score": budget_score * weights["budget"],
        "max_score": weights["budget"],
        "percentage": budget_score * 100
    }
    
    # Calculate total score
    total_score = sum(item["score"] for item in score_breakdown.values())
    
    return total_score, score_breakdown

def calculate_destination_match(trip: Any, package: frappe._dict) -> float:
    """Calculates destination matching score (0-1)."""
    if not trip.destination_city:
        return 0
    
    trip_destinations = []
    for dest in trip.destination_city:
        if isinstance(dest, dict):
            trip_destinations.append(dest.get("destination", "").lower())
        elif hasattr(dest, 'destination'):
            trip_destinations.append(dest.destination.lower())
    
    if not trip_destinations:
        return 0
    
    # Parse package destinations
    package_destinations = []
    
    # Get from destinations field (already fetched as list)
    if package.get("destinations"):
        for dest in package["destinations"]:
            if isinstance(dest, dict):
                package_destinations.append(dest.get("destination", "").lower())
            elif hasattr(dest, 'destination'):
                package_destinations.append(dest.destination.lower())
    
    # Also check itinerary_data for destinations
    if package.get("itinerary_data"):
        try:
            itinerary = json.loads(package.itinerary_data) if isinstance(package.itinerary_data, str) else package.itinerary_data
            if isinstance(itinerary, list):
                for day in itinerary:
                    if isinstance(day, dict) and day.get("destination"):
                        package_destinations.append(day["destination"].lower())
        except:
            pass
    
    # Debug logging for Singapore packages
    if "singapore" in package.get("package_name", "").lower():
        frappe.log_error(
            f"Singapore package matching:\nPackage: {package.name}\nPackage destinations: {package_destinations}\nTrip destinations: {trip_destinations}\nMatch result: {sum(1 for dest in trip_destinations if dest in package_destinations)} / {len(trip_destinations)}",
            "Singapore Package Matching Debug"
        )
    
    if not package_destinations:
        return 0
    
    # Calculate match percentage
    matches = sum(1 for dest in trip_destinations if dest in package_destinations)
    return matches / len(trip_destinations) if trip_destinations else 0

def calculate_date_compatibility(trip: Any, package: frappe._dict) -> float:
    """Calculates date compatibility score (0-1) considering date flexibility."""
    if not trip.start_date or not trip.end_date:
        return 0.5  # Neutral score if no dates specified
    
    if not package.valid_from or not package.valid_to:
        return 0.5  # Neutral score if package has no date restrictions
    
    trip_start = datetime.strptime(str(trip.start_date), "%Y-%m-%d") if isinstance(trip.start_date, str) else trip.start_date
    trip_end = datetime.strptime(str(trip.end_date), "%Y-%m-%d") if isinstance(trip.end_date, str) else trip.end_date
    package_start = datetime.strptime(str(package.valid_from), "%Y-%m-%d") if isinstance(package.valid_from, str) else package.valid_from
    package_end = datetime.strptime(str(package.valid_to), "%Y-%m-%d") if isinstance(package.valid_to, str) else package.valid_to
    
    # Get date flexibility
    flexibility = trip.flexible_days if hasattr(trip, 'flexible_days') else "Exact dates"
    
    # Apply flexibility to trip dates
    if flexibility == "Within the week":
        # Allow +/- 3 days flexibility
        trip_start_flex = trip_start - timedelta(days=3)
        trip_end_flex = trip_end + timedelta(days=3)
    elif flexibility == "Within the month":
        # Allow +/- 15 days flexibility
        trip_start_flex = trip_start - timedelta(days=15)
        trip_end_flex = trip_end + timedelta(days=15)
    elif flexibility == "Fully flexible":
        # Just check if package is available at all
        return 1.0 if package_start and package_end else 0.5
    else:  # "Exact dates"
        trip_start_flex = trip_start
        trip_end_flex = trip_end
    
    # Check if flexible trip dates fall within package validity
    if trip_start_flex >= package_start and trip_end_flex <= package_end:
        return 1.0
    
    # Check for partial overlap with flexibility
    if trip_start_flex <= package_end and trip_end_flex >= package_start:
        # Calculate overlap percentage
        overlap_start = max(trip_start_flex, package_start)
        overlap_end = min(trip_end_flex, package_end)
        overlap_days = (overlap_end - overlap_start).days + 1
        trip_days = (trip_end_flex - trip_start_flex).days + 1
        return min(1.0, overlap_days / trip_days) if trip_days > 0 else 0
    
    return 0

def calculate_activity_match(trip: Any, package: frappe._dict) -> float:
    """Calculates activity matching score (0-1) by checking itinerary_data."""
    if not trip.activity:
        return 0.5  # Neutral if no specific activities requested
    
    trip_activities = []
    for activity in trip.activity:
        if isinstance(activity, dict):
            trip_activities.append(activity.get("activity", "").lower())
    
    if not trip_activities:
        return 0.5
    
    package_activities = []
    
    # Parse activities from itinerary_data JSON
    if package.itinerary_data:
        try:
            itinerary = json.loads(package.itinerary_data) if isinstance(package.itinerary_data, str) else package.itinerary_data
            if isinstance(itinerary, list):
                for day in itinerary:
                    if isinstance(day, dict):
                        # Check for activities in various possible fields
                        if day.get("activities"):
                            if isinstance(day["activities"], list):
                                for act in day["activities"]:
                                    if isinstance(act, str):
                                        package_activities.append(act.lower())
                                    elif isinstance(act, dict) and act.get("name"):
                                        package_activities.append(act["name"].lower())
                        # Also check description for activity mentions
                        if day.get("description"):
                            desc = day["description"].lower()
                            package_activities.append(desc)
                        # Check for activity field directly
                        if day.get("activity"):
                            package_activities.append(day["activity"].lower())
        except:
            pass
    
    # Also check the activities child table if it exists
    if package.activities:
        for activity in package.activities:
            if isinstance(activity, dict):
                package_activities.append(activity.get("activity", "").lower())
    
    if not package_activities:
        return 0  # No activities found in package
    
    # Calculate match percentage - check if trip activity is mentioned anywhere
    matches = 0
    for trip_act in trip_activities:
        for pack_act in package_activities:
            if trip_act in pack_act or pack_act in trip_act:
                matches += 1
                break  # Count each trip activity only once
    
    return matches / len(trip_activities) if trip_activities else 0

def calculate_group_size_compatibility(trip: Any, package: frappe._dict, group_size: int) -> float:
    """Calculates group size compatibility score (0-1)."""
    if group_size == 0:
        return 0.5  # Neutral if no group size specified
    
    min_size = int(package.min_group_size) if package.min_group_size else 1
    max_size = int(package.max_group_size) if package.max_group_size else 999
    
    if min_size <= group_size <= max_size:
        return 1.0
    elif group_size < min_size:
        # Slightly below minimum - might be negotiable
        gap = min_size - group_size
        if gap <= 2:
            return 0.7
        elif gap <= 5:
            return 0.4
        else:
            return 0.1
    else:
        # Above maximum - harder to accommodate
        gap = group_size - max_size
        if gap <= 2:
            return 0.6
        elif gap <= 5:
            return 0.3
        else:
            return 0

def calculate_budget_alignment(trip: Any, package: frappe._dict, group_size: int) -> float:
    """Calculates budget alignment score (0-1) using base_cost per pax."""
    if not trip.budget:
        return 0.5  # Neutral if budget not specified
    
    # Use base_cost if available, otherwise use net_price
    package_price_per_pax = float(package.base_cost) if package.base_cost else (float(package.net_price) if package.net_price else 0)
    
    if not package_price_per_pax:
        return 0.5  # Neutral if no price specified
    
    trip_budget = float(trip.budget)
    
    # Calculate total package cost for the group
    # If group_size is 0, use 1 as default
    actual_group_size = group_size if group_size > 0 else 1
    total_package_cost = package_price_per_pax * actual_group_size
    
    if total_package_cost <= trip_budget:
        # Within budget
        utilization = total_package_cost / trip_budget
        if utilization >= 0.7:  # Good budget utilization
            return 1.0
        elif utilization >= 0.5:
            return 0.8
        else:
            return 0.6  # Too far under budget might indicate mismatch
    else:
        # Over budget
        overage = (total_package_cost - trip_budget) / trip_budget
        if overage <= 0.1:  # 10% over - might be negotiable
            return 0.7
        elif overage <= 0.2:  # 20% over
            return 0.4
        else:
            return 0.1

def prepare_trip_data(trip: Any) -> Dict[str, Any]:
    """Prepares trip data for AI analysis."""
    # Calculate actual group size from passenger details
    group_size = len(trip.passenger_details) if trip.passenger_details else (trip.pax if trip.pax else 0)
    
    data = {
        "title": trip.title,
        "customer": trip.customer,
        "start_date": str(trip.start_date) if trip.start_date else None,
        "end_date": str(trip.end_date) if trip.end_date else None,
        "flexible_days": trip.flexible_days if hasattr(trip, 'flexible_days') else "Exact dates",
        "group_size": group_size,
        "pax": trip.pax,  # Keep for backward compatibility
        "budget": trip.budget,
        "budget_per_person": trip.budget / group_size if (trip.budget and group_size > 0) else trip.budget,
        "priority": trip.priority,
        "category": trip.category,
        "no_of_rooms": trip.no_of_rooms,
        "departure": trip.departure,
        "destination_city": [],
        "activity": [],
        "service_type": [],
        "passenger_details": []
    }
    
    # Process child tables
    if trip.destination_city:
        for dest in trip.destination_city:
            if isinstance(dest, dict):
                data["destination_city"].append(dest)
            else:
                data["destination_city"].append({"destination": dest.destination if hasattr(dest, 'destination') else str(dest)})
    
    if trip.activity:
        for act in trip.activity:
            if isinstance(act, dict):
                data["activity"].append(act)
            else:
                data["activity"].append({"activity": act.activity if hasattr(act, 'activity') else str(act)})
    
    if trip.service_type:
        for svc in trip.service_type:
            if isinstance(svc, dict):
                data["service_type"].append(svc)
            else:
                data["service_type"].append({"service": svc.service if hasattr(svc, 'service') else str(svc)})
    
    if trip.passenger_details:
        for passenger in trip.passenger_details:
            if isinstance(passenger, dict):
                data["passenger_details"].append(passenger)
    
    return data

def prepare_package_data(package: frappe._dict) -> Dict[str, Any]:
    """Prepares package data for AI analysis."""
    data = {
        "package_name": package.package_name,
        "package_code": package.package_code,
        "description": package.description,
        "valid_from": str(package.valid_from) if package.valid_from else None,
        "valid_to": str(package.valid_to) if package.valid_to else None,
        "min_group_size": package.min_group_size,
        "max_group_size": package.max_group_size,
        "net_price": package.get("net_price"),  # Handle missing field
        "currency": package.currency,
        "dmc": package.dmc,
        "base_cost": package.get("base_cost"),
        "markup_percentage": package.get("markup_percentage")
    }
    
    # Handle child tables (already fetched as lists)
    data["destinations"] = package.get("destinations", [])
    data["activities"] = package.get("activities", [])
    data["package_inclusions"] = package.get("package_inclusions", [])
    data["package_exclusions"] = package.get("package_exclusions", [])
    data["target_audience"] = package.get("target_audience", [])
    data["exclusion_criteria"] = package.get("exclusion_criteria", [])
    
    # Parse JSON fields (only itinerary_data is JSON)
    if package.get("itinerary_data"):
        if isinstance(package.itinerary_data, str):
            try:
                data["itinerary_data"] = json.loads(package.itinerary_data)
            except:
                data["itinerary_data"] = package.itinerary_data
        else:
            data["itinerary_data"] = package.itinerary_data
    else:
        data["itinerary_data"] = []
    
    return data

def identify_main_gaps(score_breakdown: Dict[str, Any]) -> List[str]:
    """Identifies main gaps based on score breakdown."""
    gaps = []
    for criterion, scores in score_breakdown.items():
        if scores["percentage"] < 50:
            gaps.append(f"{criterion}: {scores['percentage']:.0f}% match")
    return gaps

def format_recommendations(ai_analysis: Dict[str, Any], score_breakdown: Dict[str, Any]) -> List[str]:
    """Formats recommendations based on AI analysis and scores."""
    recommendations = []
    
    # Add AI recommendations if available
    if ai_analysis and ai_analysis.get("customization_recommendations"):
        recommendations.extend(ai_analysis["customization_recommendations"])
    
    # Add score-based recommendations
    for criterion, scores in score_breakdown.items():
        if scores["percentage"] < 30:
            if criterion == "destination":
                recommendations.append(f"Consider adding more destinations to match the trip requirements")
            elif criterion == "dates":
                recommendations.append(f"Review date flexibility or consider alternative packages for the travel period")
            elif criterion == "activities":
                recommendations.append(f"Add custom activities to meet specific requirements")
            elif criterion == "budget":
                recommendations.append(f"Discuss budget adjustments or consider package modifications")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_recommendations = []
    for rec in recommendations:
        if rec not in seen:
            seen.add(rec)
            unique_recommendations.append(rec)
    
    return unique_recommendations[:5]  # Return top 5 recommendations