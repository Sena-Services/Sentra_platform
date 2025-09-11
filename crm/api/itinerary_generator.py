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

@frappe.whitelist()
def build_detailed_itinerary(trip_name: str, fill_itinerary: bool = True, use_ai_selection: bool = True) -> Dict[str, Any]:
    """
    Enhanced API that can both analyze package match AND create actual Itinerary doctype records
    
    Args:
        trip_name: Name/ID of the Trip document
        fill_itinerary: If True, will create actual Itinerary doctype with selected services
        use_ai_selection: Whether to use AI for intelligent service selection
    
    Returns:
        Dict containing package analysis + created Itinerary record
    """
    
    print(f"\n🚀 =============================================================")
    print(f"🚀 STARTING ENHANCED ITINERARY GENERATOR")
    print(f"🚀 Trip: {trip_name}")
    print(f"🚀 Fill Itinerary: {fill_itinerary}")  
    print(f"🚀 Use AI: {use_ai_selection}")
    print(f"🚀 =============================================================")
    
    try:
        # Step 1: Get package matching analysis
        print(f"\n📊 STEP 1: Analyzing package match for trip {trip_name}")
        match_result = analyze_trip_package_match(trip_name)
        
        print(f"✅ Package analysis completed:")
        print(f"   - Success: {match_result.get('success')}")
        if match_result.get('success'):
            pkg = match_result["selected_package"]
            print(f"   - Selected Package: {pkg['package_name']} (ID: {pkg['name']})")
            print(f"   - Match Score: {match_result['match_score']:.1f}%")
        else:
            print(f"   - Error: {match_result.get('message')}")
            
        if not match_result["success"]:
            print(f"❌ Cannot proceed without successful package match")
            return match_result
            
        if not fill_itinerary:
            print(f"ℹ️ fill_itinerary=False, returning package analysis only")
            return match_result
        
        # Step 2: Load trip and package data  
        print(f"\n📋 STEP 2: Loading trip and package data")
        trip = frappe.get_doc("Trip", trip_name)
        selected_package = match_result["selected_package"]
        
        print(f"✅ Trip loaded: {trip.title}")
        print(f"   - Customer: {trip.customer}")
        print(f"   - Budget: {trip.budget}")
        print(f"   - PAX: {trip.pax}")
        
        # Get destinations from trip
        destinations = []
        if trip.destination_city:
            destinations = [dest.destination for dest in trip.destination_city if hasattr(dest, 'destination')]
        print(f"   - Destinations: {destinations}")
        
        if not destinations:
            error_msg = "No destinations specified in trip"
            print(f"❌ {error_msg}")
            match_result["itinerary_error"] = error_msg
            return match_result
        
        # Step 3: Build detailed itinerary with service selection
        print(f"\n🏗️ STEP 3: Building detailed itinerary with service selection")
        print(f"   - Using {'AI-powered' if use_ai_selection else 'rule-based'} selection")
        
        itinerary_result = _build_itinerary_with_services(
            trip, selected_package, destinations, use_ai_selection
        )
        
        print(f"✅ Service selection completed:")
        services = itinerary_result.get("services", {})
        for service_type, service_list in services.items():
            print(f"   - {service_type.title()}: {len(service_list)} selected")
            if service_list:
                print(f"     {service_list[:3]}")  # Show first 3
        
        cost = itinerary_result.get("cost_breakdown", {})
        print(f"   - Total Cost: {cost.get('total', 0):.2f}")
        
        # Step 4: Create actual Itinerary doctype record
        print(f"\n💾 STEP 4: Creating Itinerary doctype record")
        
        itinerary_doc = _create_itinerary_doctype(
            trip=trip,
            package_info=selected_package,
            itinerary_data=itinerary_result,
            match_result=match_result
        )
        
        print(f"✅ Itinerary record created: {itinerary_doc.name}")
        print(f"   - Name: {itinerary_doc.itinerary_name}")
        print(f"   - Code: {itinerary_doc.itinerary_code}")
        print(f"   - Status: {itinerary_doc.status}")
        
        # Step 5: Update response
        print(f"\n📤 STEP 5: Preparing final response")
        match_result.update({
            "itinerary_created": True,
            "itinerary_name": itinerary_doc.name,
            "itinerary_id": itinerary_doc.name,
            "itinerary_code": itinerary_doc.itinerary_code,
            "detailed_itinerary": itinerary_result["itinerary"],
            "selected_services": itinerary_result["services"], 
            "total_cost_breakdown": itinerary_result["cost_breakdown"],
            "ai_itinerary_reasoning": itinerary_result.get("ai_reasoning"),
            "service_recommendations": itinerary_result.get("recommendations", [])
        })
        
        print(f"\n🎉 =============================================================")
        print(f"🎉 ITINERARY GENERATION COMPLETED SUCCESSFULLY!")
        print(f"🎉 Created Itinerary: {itinerary_doc.name}")
        print(f"🎉 Total Services: {sum(len(v) for v in services.values())}")
        print(f"🎉 Total Cost: {cost.get('total', 0):.2f}")
        print(f"🎉 =============================================================")
        
        return match_result
        
    except Exception as e:
        error_msg = f"Error in build_detailed_itinerary: {str(e)}"
        print(f"\n❌ FATAL ERROR: {error_msg}")
        frappe.log_error(error_msg, "Enhanced Itinerary Generator")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "message": "An error occurred while building the detailed itinerary"
        }

def _create_itinerary_doctype(trip, package_info: Dict, itinerary_data: Dict, match_result: Dict) -> Any:
    """Create actual Itinerary doctype record"""
    
    print(f"\n📝 Creating Itinerary doctype with the following data:")
    print(f"   - Trip: {trip.name}")
    print(f"   - Package: {package_info['name']}")
    
    try:
        # Create new Itinerary document
        itinerary = frappe.new_doc("Itinerary")
        
        # Basic info
        itinerary.trip = trip.name
        itinerary.package = package_info['name']
        # Create unique itinerary name and code with incremental numbering
        existing_count = frappe.db.count("Itinerary", {"trip": trip.name})
        itinerary_number = existing_count + 1
        
        itinerary.itinerary_name = f"{trip.title} - Itinerary {itinerary_number}"
        itinerary.itinerary_code = f"{trip.name}-ITIN-{itinerary_number:02d}"
        itinerary.status = "Draft"
        itinerary.description = f"AI-generated itinerary based on {package_info['package_name']}"
        
        # Copy package details
        itinerary.dmc = package_info.get('dmc', 'AI Generated')
        itinerary.currency = package_info.get('currency', 'USD')
        itinerary.base_cost = itinerary_data['cost_breakdown'].get('total', package_info.get('base_cost', 0))
        itinerary.markup_percentage = 20  # Default markup
        itinerary.hotel = package_info.get('hotel_category', '4')
        
        # Dates from trip
        itinerary.valid_from = trip.start_date
        itinerary.valid_to = trip.end_date
        itinerary.min_group_size = 1
        itinerary.max_group_size = trip.pax or 10
        
        # Add destinations with nights calculation
        print(f"   - Adding destinations...")
        total_nights = (trip.end_date - trip.start_date).days if trip.end_date and trip.start_date else 3
        nights_per_dest = max(1, total_nights // len(trip.destination_city)) if trip.destination_city else 1
        
        for i, dest in enumerate(trip.destination_city):
            # For the last destination, give it any remaining nights
            nights = nights_per_dest
            if i == len(trip.destination_city) - 1:
                nights = total_nights - (nights_per_dest * i)
            
            itinerary.append("destinations", {
                "destination": dest.destination,
                "nights": nights,
                "sequence": i + 1
            })
            print(f"     * {dest.destination}: {nights} nights")
        
        # Store detailed itinerary data as JSON
        print(f"   - Storing itinerary data as JSON...")
        itinerary.itinerary_data = json.dumps(itinerary_data['itinerary'])
        
        # Add notes with service details
        services = itinerary_data.get('services', {})
        notes = [
            f"AI-Generated Itinerary",
            f"Base Package: {package_info['package_name']}",
            f"Match Score: {match_result.get('match_score', 0):.1f}%",
            "",
            "Selected Services:",
        ]
        
        for service_type, service_list in services.items():
            notes.append(f"- {service_type.title()}: {len(service_list)} items")
            for service in service_list[:3]:  # Show first 3
                notes.append(f"  * {service}")
            if len(service_list) > 3:
                notes.append(f"  * ... and {len(service_list)-3} more")
        
        if itinerary_data.get('ai_reasoning'):
            notes.extend([
                "",
                "AI Selection Reasoning:",
                itinerary_data['ai_reasoning'][:500] + "..." if len(itinerary_data['ai_reasoning']) > 500 else itinerary_data['ai_reasoning']
            ])
        
        itinerary.notes = "\n".join(notes)
        
        # Save the document
        print(f"   - Saving Itinerary document...")
        itinerary.insert()
        
        print(f"✅ Itinerary doctype created successfully:")
        print(f"   - ID: {itinerary.name}")
        print(f"   - Name: {itinerary.itinerary_name}")
        print(f"   - Cost: {itinerary.currency} {itinerary.base_cost}")
        
        frappe.db.commit()
        return itinerary
        
    except Exception as e:
        error_msg = f"Failed to create Itinerary doctype: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise Exception(error_msg)

def _build_itinerary_with_services(trip: Any, selected_package: Dict, destinations: List[str], use_ai: bool) -> Dict:
    """Build itinerary using actual Hotels, Activities, Meals, Transportation, Transfer services"""
    
    print(f"\n🔍 Collecting available services for destinations: {destinations}")
    
    # Service selection functions with logging
    def get_hotels(city: str = None, star_rating: str = None, limit: int = 10):
        filters = {"status": "Active"}
        if city:
            filters["city"] = city
        if star_rating:
            filters["star_rating"] = star_rating
        
        print(f"🏨 Searching hotels: {filters}")
        results = frappe.get_list("Hotel", fields=[
            "name", "hotel_name", "star_rating", "city", "currency"
        ], filters=filters, limit=limit)
        # Add default base_price if not present
        for hotel in results:
            if "base_price" not in hotel:
                # Assign default price based on star rating
                star_prices = {"5": 250, "4": 150, "3": 100, "2": 75, "1": 50}
                hotel["base_price"] = star_prices.get(hotel.get("star_rating", "3"), 100)
        print(f"   Found {len(results)} hotels")
        return results
    
    def get_activities(city: str = None, limit: int = 20):
        filters = {"status": "Active"}
        if city:
            filters["city"] = city
        
        print(f"🎯 Searching activities: {filters}")
        results = frappe.get_list("Activity", fields=[
            "name", "activity_name", "activity_type", "city", "adult_price", "currency", "duration_hours"
        ], filters=filters, limit=limit)
        print(f"   Found {len(results)} activities")
        return results
    
    def get_meals(city: str = None, limit: int = 15):
        filters = {"status": "Active"}
        if city:
            filters["city"] = city
            
        print(f"🍽️ Searching meals: {filters}")
        results = frappe.get_list("Meal", fields=[
            "name", "meal_name", "meal_type", "city", "adult_price", "currency"
        ], filters=filters, limit=limit)
        print(f"   Found {len(results)} meals")
        return results
    
    def get_transportation(arrival_city: str = None, limit: int = 10):
        filters = {"status": "Confirmed"}
        if arrival_city:
            filters["arrival_city"] = arrival_city
            
        print(f"✈️ Searching transportation: {filters}")
        results = frappe.get_list("Transportation", fields=[
            "name", "transportation_name", "service_class", "arrival_city", "adult_price", "currency"
        ], filters=filters, limit=limit)
        print(f"   Found {len(results)} transportation options")
        return results
    
    def get_transfers(city: str = None, limit: int = 10):
        filters = {"status": "Confirmed"}
        if city:
            filters["pickup_city"] = city
            
        print(f"🚗 Searching transfers: {filters}")
        results = frappe.get_list("Transfer", fields=[
            "name", "transfer_name", "transfer_type", "pickup_city", "base_price", "currency"
        ], filters=filters, limit=limit)
        print(f"   Found {len(results)} transfers")
        return results
    
    # Collect available services for all destinations
    all_services = {"hotels": [], "activities": [], "meals": [], "transportation": [], "transfers": []}
    
    print(f"\n📦 Collecting services for each destination:")
    for destination in destinations:
        print(f"\n   Processing destination: {destination}")
        
        hotels = get_hotels(city=destination)
        activities = get_activities(city=destination)
        meals = get_meals(city=destination)
        transportation = get_transportation(arrival_city=destination)
        transfers = get_transfers(city=destination)
        
        all_services["hotels"].extend(hotels)
        all_services["activities"].extend(activities)
        all_services["meals"].extend(meals)
        all_services["transportation"].extend(transportation)
        all_services["transfers"].extend(transfers)
        
        print(f"     Added: {len(hotels)} hotels, {len(activities)} activities, {len(meals)} meals, {len(transportation)} transport, {len(transfers)} transfers")
    
    print(f"\n📊 Total services collected:")
    for service_type, service_list in all_services.items():
        print(f"   - {service_type.title()}: {len(service_list)} total")
    
    # AI-only approach - no rule-based fallback
    print(f"🤖 Using AI-powered service selection...")
    return _build_ai_itinerary(trip, selected_package, destinations, all_services)

def _build_ai_itinerary(trip: Any, package: Dict, destinations: List[str], services: Dict) -> Dict:
    """Use AI to build itinerary with intelligent service selection"""
    
    # Prepare trip requirements
    trip_requirements = {
        "destinations": destinations,
        "budget": trip.budget,
        "group_size": len(trip.passenger_details) if trip.passenger_details else (trip.pax or 2),
        "preferred_hotel_star_rating": getattr(trip, "preferred_hotel_star_rating", None),
        "preferred_meal_types": getattr(trip, "preferred_meal_types", None),
        "preferred_activity_types": getattr(trip, "preferred_activity_types", None),
        "preferred_transport_class": getattr(trip, "preferred_transport_class", None),
        "special_requirements": getattr(trip, "special_requirements", None),
        "no_of_days": package.get("no_of_days", 4)
    }
    
    # Create AI prompt
    prompt = f"""
You are a travel planning expert. Create a detailed day-by-day itinerary using the available services.

TRIP REQUIREMENTS:
{json.dumps(trip_requirements, indent=2)}

SELECTED PACKAGE BASELINE:
{json.dumps(package, indent=2)}

AVAILABLE SERVICES:
{json.dumps(services, indent=2)}

Select the best services and create a {trip_requirements['no_of_days']}-day itinerary. Consider:
1. Customer preferences (hotel stars, meal types, activities, transport class)
2. Budget constraints and group size
3. Logical daily flow and timing
4. Value for money

Respond with JSON:
{{
    "selected_services": {{
        "hotels": ["service_name_1"],
        "activities": ["service_name_1", "service_name_2"],
        "meals": ["service_name_1"],
        "transportation": ["service_name_1"],
        "transfers": ["service_name_1"]
    }},
    "daily_itinerary": [
        {{
            "day": 1,
            "date": "2025-03-15",
            "city": "{destinations[0]}",
            "services": [
                {{"type": "transportation", "service_name": "service_name", "time": "09:00"}},
                {{"type": "hotel", "service_name": "service_name", "time": "12:00"}},
                {{"type": "meal", "service_name": "service_name", "time": "13:00"}},
                {{"type": "activity", "service_name": "service_name", "time": "15:00"}}
            ]
        }}
    ],
    "cost_breakdown": {{
        "hotels": 500,
        "activities": 200,
        "meals": 150,
        "transportation": 800,
        "transfers": 100,
        "total": 1750
    }},
    "reasoning": "Selection explanation..."
}}
"""

    try:
        # Use the correct AI function from frappe_ai
        from frappe_ai.utils.llm_utils import analyze_with_llm
        
        print(f"🤖 Calling AI with analyze_with_llm...")
        
        # Prepare context with all available services - handle missing fields gracefully
        context_data = {
            "trip_requirements": trip_requirements,
            "available_services": {
                "hotels": [{"name": h["name"], "hotel_name": h.get("hotel_name", "Unknown"), "star_rating": h.get("star_rating", "3"), "city": h.get("city", ""), "base_price": h.get("base_price", 100)} for h in services["hotels"]],
                "activities": [{"name": a["name"], "activity_name": a.get("activity_name", "Unknown"), "city": a.get("city", ""), "adult_price": a.get("adult_price", 50), "duration_hours": a.get("duration_hours", 2)} for a in services["activities"]],
                "meals": [{"name": m["name"], "meal_name": m.get("meal_name", "Unknown"), "meal_type": m.get("meal_type", "Lunch"), "city": m.get("city", ""), "adult_price": m.get("adult_price", 30)} for m in services["meals"]],
                "transportation": [{"name": t["name"], "transportation_name": t.get("transportation_name", "Unknown"), "arrival_city": t.get("arrival_city", ""), "adult_price": t.get("adult_price", 100)} for t in services["transportation"]],
                "transfers": [{"name": tf["name"], "transfer_name": tf.get("transfer_name", "Unknown"), "pickup_city": tf.get("pickup_city", ""), "base_price": tf.get("base_price", 50)} for tf in services["transfers"]]
            }
        }
        
        context = json.dumps(context_data, indent=2)
        
        ai_result = analyze_with_llm(
            context=context,
            query=prompt,
            system_prompt="You are a travel planning expert. Create detailed day-by-day itineraries using the available services. Respond with valid JSON only.",
            model="gpt-4o-mini",
            json_response=True
        )
        
        print(f"   AI Success: {ai_result.get('success')}")
        if ai_result.get("content"):
            print(f"   AI Content Length: {len(ai_result['content'])} chars")
        
        if ai_result.get("success") and ai_result.get("content"):
            ai_response = json.loads(ai_result["content"])
            daily_itinerary = ai_response.get("daily_itinerary", [])
            
            print(f"   AI returned {len(daily_itinerary)} days")
            
            # Check if AI populated services in daily itinerary
            has_populated_services = any(
                day.get("services") and len(day["services"]) > 0 
                for day in daily_itinerary
            )
            
            print(f"   AI populated services: {has_populated_services}")
            
            # If AI didn't populate services properly, create from selected services
            if not has_populated_services and ai_response.get("selected_services"):
                print("🔧 AI didn't populate daily services - creating from selected services...")
                daily_itinerary = _create_daily_itinerary_from_services(
                    ai_response.get("selected_services", {}), 
                    destinations, 
                    package.get("no_of_days", 4),
                    services
                )
            
            print(f"✅ AI itinerary generation completed successfully")
            return {
                "itinerary": daily_itinerary,
                "services": ai_response.get("selected_services", {}),
                "cost_breakdown": ai_response.get("cost_breakdown", {}),
                "ai_reasoning": ai_response.get("reasoning", ""),
                "recommendations": []
            }
        else:
            error_msg = f"AI failed to generate response: {ai_result.get('error', 'Unknown error')}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"AI itinerary generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "AI Itinerary")
        raise Exception(error_msg)

def _create_daily_itinerary_from_services(selected_services: Dict, destinations: List[str], num_days: int, all_services: Dict) -> List[Dict]:
    """Helper function to create daily itinerary structure from selected services"""
    
    # Get service details for each selected service - handle missing fields
    hotel_services = []
    for hotel_name in selected_services.get("hotels", []):
        hotel_data = next((h for h in all_services["hotels"] if h["name"] == hotel_name), None)
        if hotel_data:
            hotel_services.append({
                "type": "hotel", 
                "service_name": hotel_data.get("hotel_name", "Unknown Hotel"),
                "service_id": hotel_name,
                "time": "Check-in",
                "cost": hotel_data.get("base_price", 100),
                "city": hotel_data.get("city", "")
            })
    
    activity_services = []
    for activity_name in selected_services.get("activities", []):
        activity_data = next((a for a in all_services["activities"] if a["name"] == activity_name), None)
        if activity_data:
            activity_services.append({
                "type": "activity",
                "service_name": activity_data.get("activity_name", "Unknown Activity"), 
                "service_id": activity_name,
                "time": "09:00",
                "cost": activity_data.get("adult_price", 50),
                "duration": activity_data.get("duration_hours", 2),
                "city": activity_data.get("city", "")
            })
    
    meal_services = []
    for meal_name in selected_services.get("meals", []):
        meal_data = next((m for m in all_services["meals"] if m["name"] == meal_name), None)
        if meal_data:
            meal_services.append({
                "type": "meal",
                "service_name": meal_data.get("meal_name", "Unknown Meal"),
                "service_id": meal_name, 
                "time": "12:00" if meal_data.get("meal_type") == "Lunch" else "19:00",
                "cost": meal_data.get("adult_price", 30),
                "city": meal_data.get("city", "")
            })
    
    # Create daily itinerary
    daily_itinerary = []
    for day in range(1, num_days + 1):
        day_city = destinations[(day-1) % len(destinations)] if destinations else "TBD"
        day_services = []
        
        # Add hotel for each day
        day_hotel = next((h for h in hotel_services if h["city"] == day_city), None)
        if day_hotel:
            day_services.append(day_hotel)
        
        # Distribute activities across days
        day_activities = [a for a in activity_services if a["city"] == day_city]
        if day_activities:
            activities_per_day = max(1, len(day_activities) // num_days)
            start_idx = (day-1) * activities_per_day
            end_idx = min(start_idx + activities_per_day, len(day_activities))
            day_services.extend(day_activities[start_idx:end_idx])
        
        # Distribute meals across days
        day_meals = [m for m in meal_services if m["city"] == day_city]
        if day_meals:
            meals_per_day = max(1, len(day_meals) // num_days)
            start_idx = (day-1) * meals_per_day
            end_idx = min(start_idx + meals_per_day, len(day_meals))
            day_services.extend(day_meals[start_idx:end_idx])
        
        daily_itinerary.append({
            "day": day,
            "city": day_city,
            "services": sorted(day_services, key=lambda x: x["time"])
        })
    
    return daily_itinerary

