"""
Itinerary Builder API
Enhanced itinerary generator that not only matches packages but also fills detailed itineraries
using Hotels, Activities, Meals, Transportation, and Transfer doctypes
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Import existing itinerary generator functions
from crm.api.itinerary_generator import (
    analyze_trip_package_match, 
    prepare_trip_data,
    get_active_packages
)

# Import the LLM utils for AI analysis
from frappe_ai.utils.llm_utils import run_llm_completion

class ItineraryBuilder:
    """
    AI-powered itinerary builder that can search and select from actual doctypes
    Similar to MCP server pattern with get_document functionality
    """
    
    def __init__(self):
        self.available_tools = {
            "get_hotels": self.get_hotels,
            "get_activities": self.get_activities, 
            "get_meals": self.get_meals,
            "get_transportation": self.get_transportation,
            "get_transfers": self.get_transfers,
            "analyze_requirements": self.analyze_requirements
        }
    
    def get_hotels(self, city: str = None, star_rating: str = None, limit: int = 10, filters: dict = None) -> List[Dict]:
        """Get hotels from Hotel doctype with filtering capabilities"""
        base_filters = {"status": "Active"}
        
        if city:
            base_filters["city"] = city
        if star_rating:
            base_filters["star_rating"] = star_rating
        if filters:
            base_filters.update(filters)
            
        hotels = frappe.get_list(
            "Hotel",
            fields=[
                "name", "hotel_name", "star_rating", "city", "address", 
                "latitude", "longitude", "base_price", "currency",
                "amenities", "property_type", "check_in_time", "check_out_time"
            ],
            filters=base_filters,
            limit=limit
        )
        return hotels
    
    def get_activities(self, city: str = None, activity_type: str = None, limit: int = 20, filters: dict = None) -> List[Dict]:
        """Get activities from Activity doctype with filtering capabilities"""
        base_filters = {"status": "Active"}
        
        if city:
            base_filters["city"] = city
        if activity_type:
            base_filters["activity_type"] = activity_type
        if filters:
            base_filters.update(filters)
            
        activities = frappe.get_list(
            "Activity",
            fields=[
                "name", "activity_name", "activity_type", "city", "address",
                "duration_hours", "duration_minutes", "adult_price", "currency",
                "description", "highlights", "inclusions", "min_participants", "max_participants"
            ],
            filters=base_filters,
            limit=limit
        )
        return activities
    
    def get_meals(self, city: str = None, meal_type: str = None, cuisine_type: str = None, limit: int = 15, filters: dict = None) -> List[Dict]:
        """Get meals from Meal doctype with filtering capabilities"""
        base_filters = {"status": "Active"}
        
        if city:
            base_filters["city"] = city
        if meal_type:
            base_filters["meal_type"] = meal_type
        if cuisine_type:
            base_filters["cuisine_type"] = cuisine_type
        if filters:
            base_filters.update(filters)
            
        meals = frappe.get_list(
            "Meal",
            fields=[
                "name", "meal_name", "meal_type", "cuisine_type", "city", 
                "address", "adult_price", "currency", "description",
                "menu_highlights", "dietary_options", "duration_hours", "duration_minutes"
            ],
            filters=base_filters,
            limit=limit
        )
        return meals
    
    def get_transportation(self, arrival_city: str = None, transport_class: str = None, limit: int = 10, filters: dict = None) -> List[Dict]:
        """Get transportation from Transportation doctype with filtering capabilities"""
        base_filters = {"status": "Confirmed"}
        
        if arrival_city:
            base_filters["arrival_city"] = arrival_city
        if transport_class:
            base_filters["service_class"] = transport_class
        if filters:
            base_filters.update(filters)
            
        transportation = frappe.get_list(
            "Transportation",
            fields=[
                "name", "transportation_name", "transportation_type", "mode_of_transport",
                "service_class", "departure_city", "arrival_city", "adult_price", "currency",
                "journey_duration_hours", "journey_duration_minutes", "carrier_name"
            ],
            filters=base_filters,
            limit=limit
        )
        return transportation
    
    def get_transfers(self, city: str = None, transfer_type: str = None, limit: int = 10, filters: dict = None) -> List[Dict]:
        """Get transfers from Transfer doctype with filtering capabilities"""
        base_filters = {"status": "Confirmed"}
        
        if city:
            # Search in both pickup and dropoff cities
            base_filters["pickup_city"] = city
        if transfer_type:
            base_filters["transfer_type"] = transfer_type
        if filters:
            base_filters.update(filters)
            
        transfers = frappe.get_list(
            "Transfer",
            fields=[
                "name", "transfer_name", "transfer_type", "pickup_city", "dropoff_city",
                "vehicle_type", "base_price", "currency", "estimated_duration_hours",
                "estimated_duration_minutes", "max_passengers"
            ],
            filters=base_filters,
            limit=limit
        )
        return transfers
    
    def analyze_requirements(self, trip_data: Dict, package_data: Dict) -> Dict:
        """Analyze trip requirements vs package to identify customization needs"""
        gaps = []
        recommendations = []
        
        # Check hotel requirements
        if trip_data.get("preferred_hotel_star_rating") and package_data.get("hotel_category"):
            trip_stars = int(trip_data["preferred_hotel_star_rating"].split()[0])
            package_stars = int(package_data["hotel_category"])
            
            if trip_stars > package_stars:
                gaps.append(f"Customer prefers {trip_stars}-star hotels but package has {package_stars}-star")
                recommendations.append(f"Upgrade hotels to {trip_stars}-star rating")
        
        # Check meal preferences
        if trip_data.get("preferred_meal_types"):
            meal_prefs = trip_data["preferred_meal_types"].lower()
            recommendations.append(f"Find meals matching: {meal_prefs}")
        
        # Check activity preferences  
        if trip_data.get("preferred_activity_types"):
            activity_prefs = trip_data["preferred_activity_types"].lower()
            recommendations.append(f"Include activities: {activity_prefs}")
        
        # Check transport class
        if trip_data.get("preferred_transport_class"):
            transport_class = trip_data["preferred_transport_class"]
            recommendations.append(f"Arrange {transport_class} transportation")
        
        return {
            "gaps": gaps,
            "customization_recommendations": recommendations,
            "requires_customization": len(gaps) > 0 or len(recommendations) > 0
        }

@frappe.whitelist()
def build_detailed_itinerary(trip_name: str, package_name: str = None, use_ai_selection: bool = True) -> Dict[str, Any]:
    """
    Build a detailed itinerary by selecting actual hotels, activities, meals, transport, and transfers
    
    Args:
        trip_name: Name/ID of the Trip document
        package_name: Optional specific package to use (if not provided, will auto-select best match)
        use_ai_selection: Whether to use AI for intelligent selection of services
    
    Returns:
        Dict containing detailed itinerary with actual service selections
    """
    try:
        builder = ItineraryBuilder()
        
        # Get the trip document
        trip = frappe.get_doc("Trip", trip_name)
        trip_data = prepare_trip_data(trip)
        
        # Get or select package
        if not package_name:
            # Auto-select best matching package
            match_result = analyze_trip_package_match(trip_name)
            if not match_result["success"]:
                return {
                    "success": False,
                    "message": "Could not find suitable package",
                    "error": match_result.get("message")
                }
            selected_package = match_result["selected_package"]
            package_name = selected_package["name"]
        
        package = frappe.get_doc("Standard Package", package_name)
        
        # Analyze requirements vs package
        requirements_analysis = builder.analyze_requirements(trip_data, package.as_dict())
        
        # Get destinations from trip
        destinations = []
        if trip.destination_city:
            destinations = [dest.destination for dest in trip.destination_city if hasattr(dest, 'destination')]
        
        if not destinations:
            return {
                "success": False,
                "message": "No destinations specified in trip"
            }
        
        # Build itinerary using AI if requested
        if use_ai_selection:
            itinerary_result = build_ai_powered_itinerary(
                trip_data, package.as_dict(), destinations, builder, requirements_analysis
            )
        else:
            itinerary_result = build_basic_itinerary(
                trip_data, package.as_dict(), destinations, builder
            )
        
        return {
            "success": True,
            "trip_name": trip_name,
            "package_name": package_name,
            "destinations": destinations,
            "requirements_analysis": requirements_analysis,
            "detailed_itinerary": itinerary_result["itinerary"],
            "selected_services": itinerary_result["services"],
            "total_cost_breakdown": itinerary_result["cost_breakdown"],
            "ai_reasoning": itinerary_result.get("ai_reasoning"),
            "recommendations": itinerary_result.get("recommendations", [])
        }
        
    except Exception as e:
        frappe.log_error(f"Error in build_detailed_itinerary: {str(e)}", "Itinerary Builder")
        return {
            "success": False,
            "error": str(e),
            "message": "An error occurred while building the itinerary"
        }

def build_ai_powered_itinerary(trip_data: Dict, package_data: Dict, destinations: List[str], builder: ItineraryBuilder, requirements: Dict) -> Dict:
    """Use AI to intelligently select services for the itinerary"""
    
    # Create AI prompt for service selection
    tools_description = {
        "get_hotels": "Search hotels by city, star_rating, and other filters",
        "get_activities": "Search activities by city, activity_type, and other filters", 
        "get_meals": "Search meals by city, meal_type, cuisine_type, and other filters",
        "get_transportation": "Search transportation by arrival_city, service_class, and other filters",
        "get_transfers": "Search transfers by city, transfer_type, and other filters"
    }
    
    # Get available services for each destination
    all_services = {"hotels": [], "activities": [], "meals": [], "transportation": [], "transfers": []}
    
    for destination in destinations:
        all_services["hotels"].extend(builder.get_hotels(city=destination))
        all_services["activities"].extend(builder.get_activities(city=destination))  
        all_services["meals"].extend(builder.get_meals(city=destination))
        all_services["transportation"].extend(builder.get_transportation(arrival_city=destination))
        all_services["transfers"].extend(builder.get_transfers(city=destination))
    
    # Create AI prompt for service selection
    prompt = f"""
You are an expert travel planner. Based on the following trip requirements and available services, select the best options to create a detailed itinerary.

TRIP REQUIREMENTS:
{json.dumps(trip_data, indent=2)}

PACKAGE BASELINE:
{json.dumps(package_data, indent=2)}

REQUIREMENTS ANALYSIS:
{json.dumps(requirements, indent=2)}

AVAILABLE SERVICES:
{json.dumps(all_services, indent=2)}

Please select appropriate services and create a day-by-day itinerary. Consider:
1. Customer preferences (hotel star rating, meal types, activity types, transport class)
2. Budget constraints 
3. Group size and special requirements
4. Logical flow and timing between services
5. Value for money

Respond with a JSON object containing:
- "selected_services": Dict with arrays of selected service IDs by type
- "daily_itinerary": Array of days with scheduled services
- "cost_breakdown": Total costs by service type
- "reasoning": Your selection reasoning
- "recommendations": Additional suggestions

Format:
{
    "selected_services": {
        "hotels": ["HTL-2025-0001"],
        "activities": ["ACT-2025-0001", "ACT-2025-0002"],
        "meals": ["MEAL-2025-0001"],
        "transportation": ["TRANS-2025-0001"],
        "transfers": ["TRF-2025-0001"]
    },
    "daily_itinerary": [
        {
            "day": 1,
            "date": "2025-03-15",
            "city": "London",
            "services": [
                {"type": "transportation", "id": "TRANS-2025-0001", "time": "09:00"},
                {"type": "transfer", "id": "TRF-2025-0001", "time": "10:30"},
                {"type": "hotel", "id": "HTL-2025-0001", "time": "12:00"},
                {"type": "meal", "id": "MEAL-2025-0001", "time": "13:00"},
                {"type": "activity", "id": "ACT-2025-0001", "time": "15:00"}
            ]
        }
    ],
    "cost_breakdown": {
        "hotels": 500,
        "activities": 200,
        "meals": 150,
        "transportation": 800,
        "transfers": 100,
        "total": 1750
    },
    "reasoning": "Selected 4-star hotels to match customer preference...",
    "recommendations": ["Consider adding spa services", "Upgrade to business class flights"]
}
"""

    try:
        # Call AI for service selection
        ai_result = run_llm_completion(
            prompt=prompt,
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        if ai_result.get("success") and ai_result.get("content"):
            ai_response = json.loads(ai_result["content"])
            
            return {
                "itinerary": ai_response.get("daily_itinerary", []),
                "services": ai_response.get("selected_services", {}),
                "cost_breakdown": ai_response.get("cost_breakdown", {}),
                "ai_reasoning": ai_response.get("reasoning", ""),
                "recommendations": ai_response.get("recommendations", [])
            }
        else:
            # Fallback to basic itinerary if AI fails
            frappe.log_error(f"AI itinerary generation failed: {ai_result.get('error')}", "AI Itinerary Builder")
            return build_basic_itinerary(trip_data, package_data, destinations, builder)
            
    except Exception as e:
        frappe.log_error(f"Error in AI itinerary generation: {str(e)}", "AI Itinerary Builder")
        return build_basic_itinerary(trip_data, package_data, destinations, builder)

def build_basic_itinerary(trip_data: Dict, package_data: Dict, destinations: List[str], builder: ItineraryBuilder) -> Dict:
    """Build a basic itinerary using simple selection rules"""
    
    selected_services = {"hotels": [], "activities": [], "meals": [], "transportation": [], "transfers": []}
    daily_itinerary = []
    cost_breakdown = {"hotels": 0, "activities": 0, "meals": 0, "transportation": 0, "transfers": 0}
    
    # Simple selection logic for each destination
    for i, destination in enumerate(destinations):
        # Select hotels (prefer star rating from customer preferences)
        star_rating = None
        if trip_data.get("preferred_hotel_star_rating"):
            star_rating = trip_data["preferred_hotel_star_rating"].split()[0]
        
        hotels = builder.get_hotels(city=destination, star_rating=star_rating, limit=3)
        if hotels:
            selected_hotel = hotels[0]  # Select first match
            selected_services["hotels"].append(selected_hotel["name"])
            cost_breakdown["hotels"] += selected_hotel.get("base_price", 0)
        
        # Select activities (2-3 per destination)
        activities = builder.get_activities(city=destination, limit=5)
        for activity in activities[:3]:
            selected_services["activities"].append(activity["name"])
            cost_breakdown["activities"] += activity.get("adult_price", 0)
        
        # Select meals (1-2 per destination)  
        meals = builder.get_meals(city=destination, limit=3)
        for meal in meals[:2]:
            selected_services["meals"].append(meal["name"])
            cost_breakdown["meals"] += meal.get("adult_price", 0)
        
        # Select transportation (for arrival)
        if i == 0:  # Only for first destination
            transport = builder.get_transportation(arrival_city=destination, limit=2)
            if transport:
                selected_services["transportation"].append(transport[0]["name"])
                cost_breakdown["transportation"] += transport[0].get("adult_price", 0)
        
        # Select transfers
        transfers = builder.get_transfers(city=destination, limit=2)
        if transfers:
            selected_services["transfers"].append(transfers[0]["name"])
            cost_breakdown["transfers"] += transfers[0].get("base_price", 0)
    
    # Create basic daily itinerary
    if trip_data.get("start_date"):
        start_date = datetime.strptime(str(trip_data["start_date"]), "%Y-%m-%d")
        for day in range(1, (trip_data.get("no_of_days", 3) + 1)):
            current_date = start_date + timedelta(days=day-1)
            daily_itinerary.append({
                "day": day,
                "date": current_date.strftime("%Y-%m-%d"),
                "city": destinations[(day-1) % len(destinations)],
                "services": []  # Would need more logic to schedule services by time
            })
    
    cost_breakdown["total"] = sum(cost_breakdown.values())
    
    return {
        "itinerary": daily_itinerary,
        "services": selected_services,
        "cost_breakdown": cost_breakdown,
        "recommendations": ["Basic itinerary generated", "Consider using AI-powered selection for better optimization"]
    }

@frappe.whitelist() 
def get_available_services(destination: str = None) -> Dict[str, Any]:
    """Get summary of available services for itinerary building"""
    builder = ItineraryBuilder()
    
    services = {}
    if destination:
        services["hotels"] = builder.get_hotels(city=destination)
        services["activities"] = builder.get_activities(city=destination)
        services["meals"] = builder.get_meals(city=destination)
        services["transportation"] = builder.get_transportation(arrival_city=destination)
        services["transfers"] = builder.get_transfers(city=destination)
    else:
        services["hotels"] = builder.get_hotels()
        services["activities"] = builder.get_activities()
        services["meals"] = builder.get_meals()
        services["transportation"] = builder.get_transportation()
        services["transfers"] = builder.get_transfers()
    
    return {
        "success": True,
        "destination": destination,
        "services": services,
        "summary": {
            "hotels_count": len(services["hotels"]),
            "activities_count": len(services["activities"]),
            "meals_count": len(services["meals"]),
            "transportation_count": len(services["transportation"]),
            "transfers_count": len(services["transfers"])
        }
    }