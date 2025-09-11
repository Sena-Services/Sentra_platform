# inventory.py - Unified API for inventory items across all travel doctypes

import frappe
from frappe import _
from typing import List, Dict, Any, Optional

@frappe.whitelist()
def get_inventory_items(category: str = None, search_term: str = None, destination: str = None, 
                       page: int = 1, page_size: int = 50, sort_by: str = "modified desc") -> Dict[str, Any]:
    """
    Unified endpoint to fetch inventory items from all travel doctypes
    Returns standardized format for frontend consumption
    
    Args:
        category: Filter by category (accommodation, activity, dining, transportation, all)
        search_term: Search in names and descriptions
        destination: Filter by destination/city
        page: Page number (1-based)
        page_size: Number of items per page
        sort_by: Sort order
        
    Returns:
        {
            "items": [...],
            "total": int,
            "categories": {...}
        }
    """
    try:
        items = []
        total_count = 0
        
        # Calculate offset for pagination
        offset = (int(page) - 1) * int(page_size)
        
        # Fetch from each doctype based on category
        if not category or category == "all" or category == "accommodation":
            hotels = fetch_hotels(search_term, destination, offset, page_size, sort_by)
            items.extend(transform_hotels_to_inventory(hotels))
        
        if not category or category == "all" or category == "activity":
            activities = fetch_activities(search_term, destination, offset, page_size, sort_by)
            items.extend(transform_activities_to_inventory(activities))
            
        if not category or category == "all" or category == "dining":
            meals = fetch_meals(search_term, destination, offset, page_size, sort_by)
            items.extend(transform_meals_to_inventory(meals))
            
        if not category or category == "all" or category == "transportation":
            transfers = fetch_transfers(search_term, destination, offset, page_size, sort_by)
            items.extend(transform_transfers_to_inventory(transfers))
            
            transportations = fetch_transportations(search_term, destination, offset, page_size, sort_by)
            items.extend(transform_transportations_to_inventory(transportations))
        
        # Sort and paginate final results
        if category == "all":
            # For "all" category, we need to sort and paginate the combined results
            if sort_by == "name asc":
                items.sort(key=lambda x: x.get("name", ""))
            elif sort_by == "price asc":
                items.sort(key=lambda x: x.get("price", 0))
            elif sort_by == "price desc":
                items.sort(key=lambda x: x.get("price", 0), reverse=True)
            elif sort_by == "rating desc":
                items.sort(key=lambda x: x.get("rating", 0), reverse=True)
            
            # Apply pagination to combined results
            total_count = len(items)
            items = items[offset:offset + int(page_size)]
        else:
            total_count = len(items)
        
        # Get category counts
        category_counts = get_category_counts(search_term, destination)
        
        return {
            "success": True,
            "items": items,
            "total": total_count,
            "page": int(page),
            "page_size": int(page_size),
            "categories": category_counts,
            "message": f"Retrieved {len(items)} inventory items"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_inventory_items: {str(e)}")
        return {
            "success": False,
            "items": [],
            "total": 0,
            "categories": {},
            "error": str(e),
            "message": "Failed to retrieve inventory items"
        }

def fetch_hotels(search_term: str = None, destination: str = None, 
                offset: int = 0, page_size: int = 50, sort_by: str = "modified desc") -> List[Dict]:
    """Fetch hotels with filters"""
    filters = {"docstatus": 0}  # Only fetch saved documents
    
    # Add status filter if field exists
    try:
        meta = frappe.get_meta("Hotel")
        if "status" in [f.fieldname for f in meta.fields]:
            filters["status"] = ["!=", "Archived"]
    except:
        pass
    
    if destination:
        filters["city"] = ["like", f"%{destination}%"]
    
    fields = [
        "name", "hotel_name", "hotel_chain", "star_rating", "category", 
        "city", "address_line_1", "total_rooms", "check_in_time", "check_out_time",
        "facilities", "currency", "modified"
    ]
    
    # Add search filter
    if search_term:
        hotels = frappe.db.sql("""
            SELECT {fields}
            FROM `tabHotel`
            WHERE docstatus = 0
            AND (hotel_name LIKE %(search)s OR city LIKE %(search)s OR hotel_chain LIKE %(search)s)
            {destination_filter}
            ORDER BY {sort_by}
            LIMIT {offset}, {page_size}
        """.format(
            fields=", ".join(fields),
            destination_filter="AND city LIKE %(destination)s" if destination else "",
            sort_by=sort_by,
            offset=offset,
            page_size=page_size
        ), {
            "search": f"%{search_term}%",
            "destination": f"%{destination}%" if destination else None
        }, as_dict=True)
    else:
        hotels = frappe.get_all("Hotel", 
                              filters=filters,
                              fields=fields,
                              order_by=sort_by,
                              start=offset,
                              page_length=page_size)
    
    return hotels

def fetch_activities(search_term: str = None, destination: str = None,
                    offset: int = 0, page_size: int = 50, sort_by: str = "modified desc") -> List[Dict]:
    """Fetch activities with filters"""
    filters = {"docstatus": 0}
    
    try:
        meta = frappe.get_meta("Activity")
        if "status" in [f.fieldname for f in meta.fields]:
            filters["status"] = ["!=", "Archived"]
    except:
        pass
    
    if destination:
        filters["city"] = ["like", f"%{destination}%"]
    
    fields = [
        "name", "activity_name", "activity_type", "duration_hours", "duration_minutes",
        "city", "venue_name", "minimum_age", "maximum_age", "adult_price", "child_price",
        "currency", "description", "highlights", "modified"
    ]
    
    if search_term:
        activities = frappe.db.sql("""
            SELECT {fields}
            FROM `tabActivity`
            WHERE docstatus = 0
            AND (activity_name LIKE %(search)s OR city LIKE %(search)s OR activity_type LIKE %(search)s)
            {destination_filter}
            ORDER BY {sort_by}
            LIMIT {offset}, {page_size}
        """.format(
            fields=", ".join(fields),
            destination_filter="AND city LIKE %(destination)s" if destination else "",
            sort_by=sort_by,
            offset=offset,
            page_size=page_size
        ), {
            "search": f"%{search_term}%",
            "destination": f"%{destination}%" if destination else None
        }, as_dict=True)
    else:
        activities = frappe.get_all("Activity",
                                   filters=filters,
                                   fields=fields,
                                   order_by=sort_by,
                                   start=offset,
                                   page_length=page_size)
    
    return activities

def fetch_meals(search_term: str = None, destination: str = None,
               offset: int = 0, page_size: int = 50, sort_by: str = "modified desc") -> List[Dict]:
    """Fetch meals with filters"""
    filters = {"docstatus": 0}
    
    try:
        meta = frappe.get_meta("Meal")
        if "status" in [f.fieldname for f in meta.fields]:
            filters["status"] = ["!=", "Archived"]
    except:
        pass
    
    if destination:
        filters["city"] = ["like", f"%{destination}%"]
    
    fields = [
        "name", "meal_name", "meal_type", "cuisine_type", "venue_name", "restaurant_name",
        "city", "adult_price", "child_price", "currency", "description", "menu_highlights",
        "dietary_options", "duration_hours", "duration_minutes", "modified"
    ]
    
    if search_term:
        meals = frappe.db.sql("""
            SELECT {fields}
            FROM `tabMeal`
            WHERE docstatus = 0
            AND (meal_name LIKE %(search)s OR city LIKE %(search)s OR cuisine_type LIKE %(search)s)
            {destination_filter}
            ORDER BY {sort_by}
            LIMIT {offset}, {page_size}
        """.format(
            fields=", ".join(fields),
            destination_filter="AND city LIKE %(destination)s" if destination else "",
            sort_by=sort_by,
            offset=offset,
            page_size=page_size
        ), {
            "search": f"%{search_term}%",
            "destination": f"%{destination}%" if destination else None
        }, as_dict=True)
    else:
        meals = frappe.get_all("Meal",
                              filters=filters,
                              fields=fields,
                              order_by=sort_by,
                              start=offset,
                              page_length=page_size)
    
    return meals

def fetch_transfers(search_term: str = None, destination: str = None,
                   offset: int = 0, page_size: int = 50, sort_by: str = "modified desc") -> List[Dict]:
    """Fetch transfers with filters"""
    filters = {"docstatus": 0}
    
    try:
        meta = frappe.get_meta("Transfer")
        if "status" in [f.fieldname for f in meta.fields]:
            filters["status"] = ["!=", "Archived"]
    except:
        pass
    
    if destination:
        # Search in both pickup and dropoff cities
        filters_with_destination = []
        filters_with_destination.append(["pickup_city", "like", f"%{destination}%"])
        filters_with_destination.append(["dropoff_city", "like", f"%{destination}%"])
    
    fields = [
        "name", "transfer_name", "transfer_type", "vehicle_type", "pickup_location",
        "dropoff_location", "pickup_city", "dropoff_city", "estimated_duration_hours",
        "estimated_duration_minutes", "seating_capacity", "base_price", "currency", "modified"
    ]
    
    if search_term:
        transfers = frappe.db.sql("""
            SELECT {fields}
            FROM `tabTransfer`
            WHERE docstatus = 0
            AND (transfer_name LIKE %(search)s OR pickup_city LIKE %(search)s OR dropoff_city LIKE %(search)s)
            {destination_filter}
            ORDER BY {sort_by}
            LIMIT {offset}, {page_size}
        """.format(
            fields=", ".join(fields),
            destination_filter="AND (pickup_city LIKE %(destination)s OR dropoff_city LIKE %(destination)s)" if destination else "",
            sort_by=sort_by,
            offset=offset,
            page_size=page_size
        ), {
            "search": f"%{search_term}%",
            "destination": f"%{destination}%" if destination else None
        }, as_dict=True)
    else:
        transfers = frappe.get_all("Transfer",
                                  filters=filters,
                                  fields=fields,
                                  order_by=sort_by,
                                  start=offset,
                                  page_length=page_size)
    
    return transfers

def fetch_transportations(search_term: str = None, destination: str = None,
                         offset: int = 0, page_size: int = 50, sort_by: str = "modified desc") -> List[Dict]:
    """Fetch transportations with filters"""
    filters = {"docstatus": 0}
    
    try:
        meta = frappe.get_meta("Transportation")
        if "status" in [f.fieldname for f in meta.fields]:
            filters["status"] = ["!=", "Archived"]
    except:
        pass
    
    if destination:
        # Search in both departure and arrival cities
        filters_with_destination = []
        filters_with_destination.append(["departure_city", "like", f"%{destination}%"])
        filters_with_destination.append(["arrival_city", "like", f"%{destination}%"])
    
    fields = [
        "name", "transportation_name", "transportation_type", "mode_of_transport",
        "departure_city", "arrival_city", "departure_location", "arrival_location",
        "journey_duration_hours", "journey_duration_minutes", "carrier_name",
        "adult_price", "child_price", "currency", "modified"
    ]
    
    if search_term:
        transportations = frappe.db.sql("""
            SELECT {fields}
            FROM `tabTransportation`
            WHERE docstatus = 0
            AND (transportation_name LIKE %(search)s OR departure_city LIKE %(search)s OR arrival_city LIKE %(search)s)
            {destination_filter}
            ORDER BY {sort_by}
            LIMIT {offset}, {page_size}
        """.format(
            fields=", ".join(fields),
            destination_filter="AND (departure_city LIKE %(destination)s OR arrival_city LIKE %(destination)s)" if destination else "",
            sort_by=sort_by,
            offset=offset,
            page_size=page_size
        ), {
            "search": f"%{search_term}%",
            "destination": f"%{destination}%" if destination else None
        }, as_dict=True)
    else:
        transportations = frappe.get_all("Transportation",
                                        filters=filters,
                                        fields=fields,
                                        order_by=sort_by,
                                        start=offset,
                                        page_length=page_size)
    
    return transportations

# Data transformation functions
def transform_hotels_to_inventory(hotels: List[Dict]) -> List[Dict]:
    """Transform hotel data to inventory format"""
    return [{
        "id": f"hotel_{h.get('name')}",
        "name": h.get("hotel_name") or h.get("name"),
        "category": "accommodation",
        "price": extract_base_price(h, ["base_display_price", "standard_rate"]),
        "rating": h.get("rating") or h.get("star_rating") or 4.0,
        "description": generate_hotel_description(h),
        "doctype": "Hotel",
        "docname": h.get("name"),
        "destination": h.get("city"),
        "duration": None,
        "metadata": {
            "star_rating": h.get("star_rating"),
            "total_rooms": h.get("total_rooms"),
            "facilities": h.get("facilities"),
            "check_in": h.get("check_in_time"),
            "check_out": h.get("check_out_time"),
            "chain": h.get("hotel_chain"),
            "address": h.get("address_line_1")
        }
    } for h in hotels if h.get("hotel_name") or h.get("name")]

def transform_activities_to_inventory(activities: List[Dict]) -> List[Dict]:
    """Transform activity data to inventory format"""
    return [{
        "id": f"activity_{a.get('name')}",
        "name": a.get("activity_name") or a.get("name"),
        "category": "activity",
        "price": extract_base_price(a, ["base_display_price", "adult_price"]),
        "rating": a.get("rating") or 4.2,
        "description": a.get("description") or a.get("highlights") or f"{a.get('activity_type')} experience",
        "doctype": "Activity",
        "docname": a.get("name"),
        "destination": a.get("city"),
        "duration": format_duration(a.get("duration_hours"), a.get("duration_minutes")),
        "metadata": {
            "activity_type": a.get("activity_type"),
            "venue": a.get("venue_name"),
            "min_age": a.get("minimum_age"),
            "max_age": a.get("maximum_age"),
            "child_price": a.get("child_price"),
            "highlights": a.get("highlights")
        }
    } for a in activities if a.get("activity_name") or a.get("name")]

def transform_meals_to_inventory(meals: List[Dict]) -> List[Dict]:
    """Transform meal data to inventory format"""
    return [{
        "id": f"meal_{m.get('name')}",
        "name": m.get("meal_name") or m.get("name"),
        "category": "dining",
        "price": extract_base_price(m, ["base_display_price", "adult_price"]),
        "rating": m.get("rating") or 4.1,
        "description": m.get("description") or f"{m.get('cuisine_type')} {m.get('meal_type')}",
        "doctype": "Meal",
        "docname": m.get("name"),
        "destination": m.get("city"),
        "duration": format_duration(m.get("duration_hours"), m.get("duration_minutes")),
        "metadata": {
            "meal_type": m.get("meal_type"),
            "cuisine": m.get("cuisine_type"),
            "venue": m.get("venue_name") or m.get("restaurant_name"),
            "dietary_options": m.get("dietary_options"),
            "menu_highlights": m.get("menu_highlights"),
            "child_price": m.get("child_price")
        }
    } for m in meals if m.get("meal_name") or m.get("name")]

def transform_transfers_to_inventory(transfers: List[Dict]) -> List[Dict]:
    """Transform transfer data to inventory format"""
    return [{
        "id": f"transfer_{t.get('name')}",
        "name": t.get("transfer_name") or f"{t.get('pickup_location')} to {t.get('dropoff_location')}",
        "category": "transportation",
        "price": extract_base_price(t, ["base_display_price", "base_price"]),
        "rating": t.get("rating") or 4.0,
        "description": f"{t.get('vehicle_type')} transfer from {t.get('pickup_location')} to {t.get('dropoff_location')}",
        "doctype": "Transfer",
        "docname": t.get("name"),
        "destination": t.get("pickup_city") or t.get("dropoff_city"),
        "duration": format_duration(t.get("estimated_duration_hours"), t.get("estimated_duration_minutes")),
        "metadata": {
            "transfer_type": t.get("transfer_type"),
            "vehicle_type": t.get("vehicle_type"),
            "pickup": t.get("pickup_location"),
            "dropoff": t.get("dropoff_location"),
            "capacity": t.get("seating_capacity")
        }
    } for t in transfers if t.get("transfer_name") or (t.get("pickup_location") and t.get("dropoff_location"))]

def transform_transportations_to_inventory(transportations: List[Dict]) -> List[Dict]:
    """Transform transportation data to inventory format"""
    return [{
        "id": f"transport_{t.get('name')}",
        "name": t.get("transportation_name") or f"{t.get('departure_city')} to {t.get('arrival_city')}",
        "category": "transportation",
        "price": extract_base_price(t, ["base_display_price", "adult_price"]),
        "rating": t.get("rating") or 4.0,
        "description": f"{t.get('mode_of_transport')} from {t.get('departure_city')} to {t.get('arrival_city')}",
        "doctype": "Transportation",
        "docname": t.get("name"),
        "destination": t.get("departure_city") or t.get("arrival_city"),
        "duration": format_duration(t.get("journey_duration_hours"), t.get("journey_duration_minutes")),
        "metadata": {
            "transport_type": t.get("transportation_type"),
            "mode": t.get("mode_of_transport"),
            "carrier": t.get("carrier_name"),
            "departure": t.get("departure_location"),
            "arrival": t.get("arrival_location"),
            "child_fare": t.get("child_fare")
        }
    } for t in transportations if t.get("transportation_name") or (t.get("departure_city") and t.get("arrival_city"))]

# Helper functions
def extract_base_price(item: Dict, price_fields: List[str]) -> float:
    """Extract base price from item, checking multiple possible fields"""
    for field in price_fields:
        price = item.get(field)
        if price and (isinstance(price, (int, float)) and price > 0):
            return float(price)
    return 0.0

def format_duration(hours: int = None, minutes: int = None) -> str:
    """Format duration from hours and minutes"""
    if not hours and not minutes:
        return None
    
    duration_parts = []
    if hours:
        duration_parts.append(f"{hours}h")
    if minutes:
        duration_parts.append(f"{minutes}m")
    
    return " ".join(duration_parts) if duration_parts else None

def generate_hotel_description(hotel: Dict) -> str:
    """Generate a short description for hotel"""
    parts = []
    
    if hotel.get("star_rating"):
        parts.append(f"{hotel.get('star_rating')}-star")
    
    if hotel.get("category"):
        parts.append(hotel.get("category").lower())
    
    if hotel.get("hotel_chain"):
        parts.append(f"by {hotel.get('hotel_chain')}")
    
    if hotel.get("city"):
        parts.append(f"in {hotel.get('city')}")
    
    return " ".join(parts) if parts else "Hotel accommodation"

def get_category_counts(search_term: str = None, destination: str = None) -> Dict[str, int]:
    """Get count of items in each category"""
    try:
        counts = {
            "all": 0,
            "accommodation": 0,
            "activity": 0,
            "dining": 0,
            "transportation": 0
        }
        
        # Count hotels
        hotel_filters = {"docstatus": 0}
        if destination:
            hotel_filters["city"] = ["like", f"%{destination}%"]
        counts["accommodation"] = frappe.db.count("Hotel", filters=hotel_filters)
        
        # Count activities
        activity_filters = {"docstatus": 0}
        if destination:
            activity_filters["city"] = ["like", f"%{destination}%"]
        counts["activity"] = frappe.db.count("Activity", filters=activity_filters)
        
        # Count meals
        meal_filters = {"docstatus": 0}
        if destination:
            meal_filters["city"] = ["like", f"%{destination}%"]
        counts["dining"] = frappe.db.count("Meal", filters=meal_filters)
        
        # Count transfers and transportations
        transfer_filters = {"docstatus": 0}
        transport_filters = {"docstatus": 0}
        
        transfer_count = frappe.db.count("Transfer", filters=transfer_filters)
        transport_count = frappe.db.count("Transportation", filters=transport_filters)
        counts["transportation"] = transfer_count + transport_count
        
        # Calculate total
        counts["all"] = sum([counts["accommodation"], counts["activity"], counts["dining"], counts["transportation"]])
        
        return counts
        
    except Exception as e:
        frappe.log_error(f"Error getting category counts: {str(e)}")
        return {"all": 0, "accommodation": 0, "activity": 0, "dining": 0, "transportation": 0}

@frappe.whitelist()
def get_inventory_categories() -> Dict[str, Any]:
    """Get available inventory categories with counts"""
    try:
        counts = get_category_counts()
        
        categories = [
            {"id": "all", "label": "All Items", "shortLabel": "All", "icon": "all", "count": counts["all"]},
            {"id": "accommodation", "label": "Hotels", "shortLabel": "Hotels", "icon": "building", "count": counts["accommodation"]},
            {"id": "activity", "label": "Activities", "shortLabel": "Activities", "icon": "activity", "count": counts["activity"]},
            {"id": "dining", "label": "Dining", "shortLabel": "Food", "icon": "restaurant", "count": counts["dining"]},
            {"id": "transportation", "label": "Transport", "shortLabel": "Transport", "icon": "car", "count": counts["transportation"]},
        ]
        
        return {
            "success": True,
            "categories": categories,
            "message": "Categories retrieved successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_inventory_categories: {str(e)}")
        return {
            "success": False,
            "categories": [],
            "error": str(e),
            "message": "Failed to retrieve categories"
        }