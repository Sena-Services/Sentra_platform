import frappe
from frappe import _
import json

@frappe.whitelist()
def insert_lead_with_requirement(doc):
    """
    Custom insert handler for CRM Lead that also creates Requirement record.
    This function intercepts the standard frappe.client.insert call.
    
    Args:
        doc (dict): The document data in the format sent by frappe.client.insert:
            {
                "doctype": "CRM Lead",
                "link_to_contact": "CONT-2024-00001", 
                "status": "Lead",
                "priority": "High",
                "service_type": ["Flight", "Hotel"],
                "trip_name": "Trip to Paris",
                "departure_city": "Chennai",
                "destination_city": "Paris",
                "travel_dates": {"start_date": "2024-06-15", "end_date": "2024-06-20"},
                "travelers": {"adults": 2, "children": 0, "infants": 0},
                "budget_per_person": 50000,
                "hotel_category": 4,
                "special_interests": ["Sightseeing", "Shopping"],
                ...
            }
    
    Returns:
        dict: Created lead document
    """
    try:
        # Parse if string
        if isinstance(doc, str):
            doc = json.loads(doc)
        
        print(f"=== Lead+Requirement Creation Debug ===")
        print(f"Received doc type: {type(doc)}")
        print(f"Doc keys: {list(doc.keys()) if isinstance(doc, dict) else 'Not a dict'}")
        
        if not doc or doc.get("doctype") != "CRM Lead":
            frappe.throw(_("Invalid document type. Expected CRM Lead."))
        
        # Extract lead-specific fields
        lead_fields = [
            "doctype", "link_to_contact", "status", "source", "lead_owner", 
            "priority", "service_type", "notes", "tags", "_user_tags", "naming_series"
        ]
        
        # Extract requirement-specific fields  
        requirement_field_mapping = {
            "trip_name": "title",
            "departure_city": "departure",
            "destination_city": "destination_city",
            "travel_dates": "travel_dates",
            "date_flexibility": "flexible_days",
            "travelers": "passengers", 
            "budget_per_person": "budget",
            "hotel_category": "category",
            "number_of_rooms": "no_of_rooms",
            "special_interests": "activity",
            "notes": "notes"
        }
        
        # Separate the data
        lead_data = {}
        requirement_data = {}
        
        # Store service_type array separately for processing
        service_type_array = None
        
        for key, value in doc.items():
            if key in lead_fields and value is not None:
                # Skip service_type - we'll handle it separately
                if key == "service_type":
                    service_type_array = value
                    continue
                else:
                    lead_data[key] = value
            elif key in requirement_field_mapping and value is not None:
                requirement_data[key] = value
        
        print(f"\nLead fields extracted: {list(lead_data.keys())}")
        print(f"Requirement fields found: {list(requirement_data.keys())}")
        print(f"Service type array: {service_type_array}")
                
        # Handle tags specially
        tags = lead_data.pop("tags", None) or lead_data.pop("_user_tags", None)
        
        # Create Lead
        lead_doc = frappe.new_doc("CRM Lead")
        lead_doc.update(lead_data)
        if not hasattr(lead_doc, "naming_series") or not lead_doc.naming_series:
            lead_doc.naming_series = "CRM-LEAD-.YYYY.-"
        
        print(f"\nCreating lead...")
        lead_doc.insert(ignore_permissions=True)
        print(f"Lead created successfully: {lead_doc.name}")
        
        # Handle tags after creation
        if tags:
            if isinstance(tags, list):
                lead_doc._user_tags = ",".join(tags)
            else:
                lead_doc._user_tags = tags
            lead_doc.save(ignore_permissions=True)
        
        # Handle service types
        if service_type_array and isinstance(service_type_array, list):
            print(f"\nProcessing service types: {service_type_array}")
            
            # Special logic for Tour Package
            tour_package_services = ['Tour Package', 'Hotels', 'Transportation', 
                                   'Activities', 'Transfers', 'Visa']
            
            # Check if all tour package services are selected
            if all(service in service_type_array for service in tour_package_services):
                # If all services are selected, just add "Tour Package"
                lead_doc.append("service_types", {
                    "service_type": "Tour Package"
                })
                print(f"All services selected, adding only 'Tour Package'")
            else:
                # Add each selected service
                for service in service_type_array:
                    lead_doc.append("service_types", {
                        "service_type": service
                    })
                    print(f"Added service type: {service}")
            
            lead_doc.save(ignore_permissions=True)
            print(f"Lead updated with service types")
        
        # Create Requirement if we have trip data
        requirement_doc = None
        if requirement_data:
            print(f"\nCreating requirement with data: {requirement_data}")
            requirement_doc = create_requirement_from_data(lead_doc.name, requirement_data)
            print(f"Requirement created: {requirement_doc.name}")
        else:
            print("\nNo requirement data found, skipping requirement creation")
            
        # Return the lead doc in the expected format
        result = lead_doc.as_dict()
        
        # Add requirement info if created
        if requirement_doc:
            result["_requirement_created"] = requirement_doc.name
            
        return result
        
    except Exception as e:
        frappe.log_error(f"Error in insert_lead_with_requirement: {str(e)}")
        frappe.throw(str(e))


def create_requirement_from_data(lead_id, data):
    """
    Helper to create Requirement from frontend data
    """
    req_doc = frappe.new_doc("Requirement")
    req_doc.lead = lead_id
    
    # Basic field mapping
    req_doc.title = data.get("trip_name", f"Trip for {lead_id}")
    req_doc.departure = data.get("departure_city")
    req_doc.notes = data.get("notes")
    
    # Handle travel dates
    travel_dates = data.get("travel_dates")
    if isinstance(travel_dates, dict):
        req_doc.start_date = travel_dates.get("start_date")
        req_doc.end_date = travel_dates.get("end_date")
    
    # Handle date flexibility
    date_flexibility = data.get("date_flexibility")
    if date_flexibility:
        if isinstance(date_flexibility, str):
            req_doc.flexible_days = 1 if date_flexibility != "Exact dates" else 0
        else:
            req_doc.flexible_days = 1 if date_flexibility else 0
    
    # Handle budget (per person budget only)
    budget_per_person = data.get("budget_per_person")
    if budget_per_person:
        req_doc.budget = float(budget_per_person)
    
    # Handle hotel category
    hotel_category = data.get("hotel_category")
    if hotel_category:
        if isinstance(hotel_category, (int, float)):
            req_doc.category = f"{int(hotel_category)} Star"
        else:
            req_doc.category = hotel_category
    
    # Handle number of rooms
    req_doc.no_of_rooms = data.get("number_of_rooms", 1)
    
    # Handle destinations (child table)
    destination = data.get("destination_city")
    if destination:
        if isinstance(destination, str):
            # Single destination
            add_destination_to_requirement(req_doc, destination, 1)
        elif isinstance(destination, list):
            # Multiple destinations
            for dest in destination:
                if isinstance(dest, str):
                    add_destination_to_requirement(req_doc, dest, 1)
                elif isinstance(dest, dict):
                    add_destination_to_requirement(
                        req_doc,
                        dest.get("city") or dest.get("destination"),
                        dest.get("nights", 1)
                    )
    
    # Handle passengers (child table)
    travelers = data.get("travelers")
    if travelers:
        pax_total = 0
        
        if isinstance(travelers, dict):
            # Format: {"adults": 2, "children": 1, "infants": 0, "childAges": [13, 6], "infantMonths": [9, 2]}
            
            # Add adults
            adult_count = travelers.get("adults", 0)
            for i in range(int(adult_count) if adult_count else 0):
                req_doc.append("passenger_details", {
                    "passenger_type": "Adult",
                    "age": None  # Adults don't need age specified
                })
                pax_total += 1
            
            # Add children with their ages
            child_count = travelers.get("children", 0)
            child_ages = travelers.get("childAges", [])
            for i in range(int(child_count) if child_count else 0):
                age = child_ages[i] if i < len(child_ages) else None
                req_doc.append("passenger_details", {
                    "passenger_type": "Child",
                    "age": age
                })
                pax_total += 1
            
            # Add infants with their ages in months (convert to age in years)
            infant_count = travelers.get("infants", 0)
            infant_months = travelers.get("infantMonths", [])
            for i in range(int(infant_count) if infant_count else 0):
                months = infant_months[i] if i < len(infant_months) else None
                # Convert months to age (0 for infants less than 1 year)
                age = 0 if months is not None else None
                req_doc.append("passenger_details", {
                    "passenger_type": "Infant", 
                    "age": age
                })
                pax_total += 1
        
        req_doc.pax = pax_total
    
    # Handle activities (child table)
    activities = data.get("special_interests")
    if activities:
        if isinstance(activities, str):
            add_activity_to_requirement(req_doc, activities)
        elif isinstance(activities, list):
            for activity in activities:
                if isinstance(activity, str):
                    add_activity_to_requirement(req_doc, activity)
                elif isinstance(activity, dict):
                    add_activity_to_requirement(
                        req_doc, 
                        activity.get("activity") or activity.get("name")
                    )
    
    
    req_doc.insert(ignore_permissions=True)
    return req_doc


def add_destination_to_requirement(req_doc, city_name, nights=1):
    """Add destination to requirement, creating if needed"""
    if not city_name:
        return
        
    try:
        # Create destination if it doesn't exist
        if not frappe.db.exists("Destination", city_name):
            dest_doc = frappe.new_doc("Destination")
            dest_doc.city = city_name
            dest_doc.country = "India"  # Default
            dest_doc.insert(ignore_permissions=True)
        
        req_doc.append("destination_city", {
            "destination": city_name,
            "nights": nights or 1
        })
    except Exception as e:
        frappe.log_error(f"Failed to add destination '{city_name}': {e}")


def add_activity_to_requirement(req_doc, activity_name):
    """Add activity to requirement, creating if needed"""
    if not activity_name:
        return
        
    try:
        # Create activity if it doesn't exist
        if not frappe.db.exists("Activity List", activity_name):
            activity_doc = frappe.new_doc("Activity List")
            activity_doc.activity = activity_name
            activity_doc.insert(ignore_permissions=True)
        
        req_doc.append("activity", {
            "activity": activity_name
        })
    except Exception as e:
        frappe.log_error(f"Failed to add activity '{activity_name}': {e}")


def map_passenger_type(frontend_type):
    """Map frontend passenger types to backend format"""
    mapping = {
        "adults": "Adult",
        "children": "Child",
        "infants": "Infant",
        "adult": "Adult",
        "child": "Child",
        "infant": "Infant"
    }
    return mapping.get(frontend_type.lower(), "Adult")