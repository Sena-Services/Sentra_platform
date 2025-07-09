import frappe
from frappe import _


@frappe.whitelist()
def create_lead_with_trip(lead_data, trip_data=None):
	"""
	Create a CRM Lead and automatically create a Trip for it.
	
	Args:
		lead_data (dict): CRM Lead data
		trip_data (dict): Trip data (optional)
	
	Returns:
		dict: Created lead with trip information
	"""
	try:
		# Step 1: Create CRM Lead
		lead_doc = frappe.new_doc("CRM Lead")
		
		# Set required fields with defaults
		lead_doc.update({
			"naming_series": "CRM-LEAD-.YYYY.-",
			"lead_owner": lead_data.get("lead_owner", "Administrator"),
			"status": lead_data.get("status", "New"),
			"priority": lead_data.get("priority", "Medium"),
			"source": lead_data.get("source", ""),
			"service_type": lead_data.get("service_type", ""),
			"link_to_contact": lead_data.get("link_to_contact")
		})
		
		# Add any additional lead fields
		for key, value in lead_data.items():
			if hasattr(lead_doc, key) and key not in ["naming_series"]:
				setattr(lead_doc, key, value)
		
		lead_doc.insert(ignore_permissions=True)
		
		# Step 2: Create Trip if trip_data is provided
		trip_doc = None
		if trip_data:
			trip_doc = frappe.new_doc("Trip")
			
			# Link Trip to Lead
			trip_doc.lead = lead_doc.name
			
			# Set Trip fields with defaults
			trip_doc.update({
				"title": trip_data.get("title", f"Trip for {lead_doc.name}"),
				"start_date": trip_data.get("start_date"),
				"end_date": trip_data.get("end_date"),
				"budget": trip_data.get("budget"),
				"pax": trip_data.get("pax", 1),
				"category": trip_data.get("category"),
				"no_of_rooms": trip_data.get("no_of_rooms", 1),
				"flexible_days": trip_data.get("flexible_days", 0),
			})
			
			# Handle child table fields
			if trip_data.get("destination_city"):
				trip_doc.destination_city = []
				for dest in trip_data.get("destination_city", []):
					trip_doc.append("destination_city", dest)
			
			if trip_data.get("passenger_details"):
				trip_doc.passenger_details = []
				for passenger in trip_data.get("passenger_details", []):
					trip_doc.append("passenger_details", passenger)
			
			if trip_data.get("activity"):
				trip_doc.activity = []
				for activity in trip_data.get("activity", []):
					trip_doc.append("activity", activity)
			
			trip_doc.insert(ignore_permissions=True)
		
		# Return lead with trip information
		result = lead_doc.as_dict()
		if trip_doc:
			result["trip"] = trip_doc.as_dict()
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Error creating lead with trip: {str(e)}")
		frappe.throw(_("Failed to create Lead and Trip: {0}").format(str(e)))


@frappe.whitelist()
def create_lead_with_trip_simple(**kwargs):
	"""
	Simplified API that accepts parameters as kwargs.
	All parameters are passed directly from the frontend API call.
	"""
	
	try:
		# Get all parameters passed from frontend
		data = kwargs
		frappe.log_error(f"API called with data: {data}", "Lead Trip API Debug")
		
		# Separate lead and trip data
		lead_data = {}
		trip_data = {}
		
		# Extract lead fields
		lead_fields = [
			"lead_owner", "status", "priority", "source", "service_type", 
			"link_to_contact"
		]
		
		for field in lead_fields:
			if field in data:
				lead_data[field] = data[field]
		
		# Always add naming_series for CRM Lead
		lead_data["naming_series"] = "CRM-LEAD-.YYYY.-"
		
		# Validate required fields
		if not lead_data.get("link_to_contact"):
			frappe.throw(_("Contact is required to create a Lead"))
		
		# Extract trip fields (prefixed with trip_)
		trip_field_mapping = {
			"trip_title": "title",
			"trip_start_date": "start_date", 
			"trip_end_date": "end_date",
			"trip_budget": "budget",
			"trip_pax": "pax",
			"trip_category": "category",
			"trip_rooms": "no_of_rooms",
			"trip_flexible": "flexible_days",
			"trip_destinations": "destination_city",
			"trip_passengers": "passenger_details",
			"trip_activities": "activity"
		}
		
		for frontend_key, backend_key in trip_field_mapping.items():
			if frontend_key in data:
				trip_data[backend_key] = data[frontend_key]
		
		frappe.log_error(f"Lead data: {lead_data}", "Lead Trip API Debug")
		frappe.log_error(f"Trip data: {trip_data}", "Lead Trip API Debug")
		
		# Call the main function
		return create_lead_with_trip(lead_data, trip_data)
		
	except Exception as e:
		frappe.log_error(f"API Error: {str(e)}", "Lead Trip API Error")
		# Let Frappe handle the error naturally
		frappe.throw(_(str(e)))