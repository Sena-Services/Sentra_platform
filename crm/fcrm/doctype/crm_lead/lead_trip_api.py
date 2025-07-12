import frappe
from frappe import _
from frappe.desk.doctype.tag.tag import add_tag


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
		
		# Handle tags separately (don't include in the main lead data)
		tags = lead_data.pop("tags", None) or lead_data.pop("_user_tags", None)
		
		# Add any additional lead fields
		for key, value in lead_data.items():
			if hasattr(lead_doc, key) and key not in ["naming_series", "tags", "_user_tags"]:
				setattr(lead_doc, key, value)
		
		lead_doc.insert(ignore_permissions=True)
		
		# Handle tags after document creation
		if tags:
			if isinstance(tags, list):
				# If tags is a list, convert to comma-separated string
				lead_doc._user_tags = ",".join(tags)
				lead_doc.save(ignore_permissions=True)
			elif isinstance(tags, str):
				# If tags is already a string, use it directly
				lead_doc._user_tags = tags
				lead_doc.save(ignore_permissions=True)
		
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
				"departure": trip_data.get("departure"),  # Add departure field
			})
			
			# Handle child table fields
			if trip_data.get("destination_city"):
				trip_doc.destination_city = []
				for dest in trip_data.get("destination_city", []):
					trip_doc.append("destination_city", dest)
			
			if trip_data.get("passenger_details"):
				trip_doc.passenger_details = []
				departure_city = None
				for passenger in trip_data.get("passenger_details", []):
					trip_doc.append("passenger_details", passenger)
					# Extract departure city from first passenger if not already set
					if not departure_city and passenger.get("source_city"):
						departure_city = passenger.get("source_city")
				
				# Set departure field from passenger details if not already provided
				if departure_city and not trip_doc.departure:
					trip_doc.departure = departure_city
			
			if trip_data.get("activity"):
				trip_doc.activity = []
				for activity in trip_data.get("activity", []):
					# Ensure activity is a dictionary with required fields
					if isinstance(activity, str):
						activity = {"activity": activity}
					
					# Create Activity List record if it doesn't exist
					activity_name = activity.get("activity")
					if activity_name:
						try:
							if not frappe.db.exists("Activity List", activity_name):
								activity_doc = frappe.new_doc("Activity List")
								activity_doc.activity = activity_name
								activity_doc.insert(ignore_permissions=True)
								frappe.log_error(f"Created Activity List: {activity_name}", "Trip Activity Creation")
							
							# Only append the activity if it exists or was successfully created
							trip_doc.append("activity", activity)
						except Exception as activity_error:
							frappe.log_error(f"Failed to create Activity List '{activity_name}': {activity_error}", "Trip Activity Creation Error")
							# Skip this activity rather than failing the entire operation
							pass
			
			trip_doc.insert(ignore_permissions=True)
		
		# Return lead with trip information
		result = lead_doc.as_dict()
		
		# Parse tags for frontend convenience 
		if result.get("_user_tags"):
			result["tags_parsed"] = [tag.strip() for tag in result["_user_tags"].split(",") if tag.strip()]
		else:
			result["tags_parsed"] = []
		
		if trip_doc:
			result["trip"] = trip_doc.as_dict()
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Error creating lead with trip: {str(e)}", "Lead Trip Creation Error")
		
		# Provide more specific error messages based on the error type
		error_msg = str(e)
		if "Contact" in error_msg or "link_to_contact" in error_msg:
			frappe.throw(_("Failed to create Lead: The specified contact does not exist. Please provide a valid contact."))
		elif "Permission" in error_msg:
			frappe.throw(_("Failed to create Lead and Trip: Insufficient permissions to create records."))
		else:
			frappe.throw(_("Failed to create Lead and Trip: {0}").format(error_msg))


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
			"link_to_contact", "notes", "tags", "_user_tags"
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
		
		# Provide more specific error messages based on the error type
		error_msg = str(e)
		if "Contact" in error_msg or "link_to_contact" in error_msg:
			frappe.throw(_("Failed to create Lead: The specified contact does not exist. Please provide a valid contact."))
		elif "Permission" in error_msg:
			frappe.throw(_("Failed to create Lead and Trip: Insufficient permissions to create records."))
		else:
			frappe.throw(_("Failed to create Lead and Trip: {0}").format(error_msg))