import frappe
from frappe import _
import json
from frappe.desk.doctype.tag.tag import add_tag


# =============================================================================
# LEAD CRUD OPERATIONS
# =============================================================================

@frappe.whitelist()
def create_lead(lead_data, trip_data=None):
	"""
	Create a new Lead, optionally with Trip data.
	
	Args:
		lead_data (dict): Lead fields
		trip_data (dict|list): Single trip or list of trips (optional)
	
	Returns:
		dict: Created lead with trip info
	
	Example:
		# Lead only
		POST /api/method/crm.api.lead_trip_crud.create_lead
		{
			"lead_data": {
				"link_to_contact": "Contact-001",
				"status": "New",
				"source": "Website"
			}
		}
		
		# Lead with single trip
		{
			"lead_data": {...},
			"trip_data": {
				"title": "Europe Trip",
				"start_date": "2024-06-15",
				"budget": 5000
			}
		}
		
		# Lead with multiple trips
		{
			"lead_data": {...},
			"trip_data": [
				{"title": "Europe Trip", "budget": 5000},
				{"title": "Asia Trip", "budget": 3000}
			]
		}
	"""
	try:
		# Validate and parse input
		if isinstance(lead_data, str):
			lead_data = json.loads(lead_data)
		
		if not lead_data or not isinstance(lead_data, dict):
			frappe.throw(_("lead_data is required and must be a dictionary"))
		
		# Parse trip_data if it's a string
		if isinstance(trip_data, str):
			trip_data = json.loads(trip_data)
		
		# Handle tags separately (don't include in the main lead data)
		tags = lead_data.pop("tags", None) or lead_data.pop("_user_tags", None)
		
		# Create Lead
		lead_doc = frappe.new_doc("CRM Lead")
		lead_doc.update({
			"naming_series": "CRM-LEAD-.YYYY.-",
			**lead_data
		})
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
		
		# Create Trip(s) if provided
		trips = []
		if trip_data:
			trip_list = trip_data if isinstance(trip_data, list) else [trip_data]
			for trip in trip_list:
				trip_doc = _create_trip_for_lead(lead_doc.name, trip)
				trips.append(trip_doc.as_dict())
		
		result = lead_doc.as_dict()
		
		# Parse tags for frontend convenience 
		if result.get("_user_tags"):
			result["tags_parsed"] = [tag.strip() for tag in result["_user_tags"].split(",") if tag.strip()]
		else:
			result["tags_parsed"] = []
		
		result["trips"] = trips
		return result
		
	except Exception as e:
		frappe.log_error(f"Error creating lead: {str(e)}")
		frappe.throw(_("Failed to create Lead: {0}").format(str(e)))


@frappe.whitelist()
def get_lead(lead_id, include_trips=True):
	"""
	Get a single Lead with optional Trip data.
	
	Args:
		lead_id (str): Lead name/ID
		include_trips (bool): Include trip data
	
	Returns:
		dict: Lead data with trips
	"""
	try:
		lead_doc = frappe.get_doc("CRM Lead", lead_id)
		result = lead_doc.as_dict()
		
		# Parse tags for frontend convenience 
		if result.get("_user_tags"):
			result["tags_parsed"] = [tag.strip() for tag in result["_user_tags"].split(",") if tag.strip()]
		else:
			result["tags_parsed"] = []
		
		if include_trips:
			# Get full Trip documents for this lead
			trip_names = frappe.get_all("Trip", filters={"lead": lead_id}, pluck="name")
			trips = []
			for trip_name in trip_names:
				trip_doc = frappe.get_doc("Trip", trip_name)
				trips.append(trip_doc.as_dict())
			result["trips"] = trips
		
		return result
		
	except Exception as e:
		frappe.throw(_("Failed to get Lead: {0}").format(str(e)))


@frappe.whitelist()
def update_lead(lead_id, lead_data):
	"""
	Update Lead data only (trips handled separately).
	
	Args:
		lead_id (str): Lead name/ID
		lead_data (dict): Fields to update
	
	Returns:
		dict: Updated lead data
	"""
	try:
		if isinstance(lead_data, str):
			lead_data = json.loads(lead_data)
		
		# Handle tags separately
		tags = lead_data.pop("tags", None) or lead_data.pop("_user_tags", None)
		
		lead_doc = frappe.get_doc("CRM Lead", lead_id)
		lead_doc.update(lead_data)
		
		# Handle tags if provided
		if tags is not None:  # Allow empty string to clear tags
			if isinstance(tags, list):
				lead_doc._user_tags = ",".join(tags)
			elif isinstance(tags, str):
				lead_doc._user_tags = tags
		
		lead_doc.save(ignore_permissions=True)
		
		result = lead_doc.as_dict()
		
		# Parse tags for frontend convenience 
		if result.get("_user_tags"):
			result["tags_parsed"] = [tag.strip() for tag in result["_user_tags"].split(",") if tag.strip()]
		else:
			result["tags_parsed"] = []
		
		return result
		
	except Exception as e:
		frappe.throw(_("Failed to update Lead: {0}").format(str(e)))


@frappe.whitelist()
def delete_lead(lead_id, action="delete_with_trips"):
	"""
	Delete Lead with different trip handling options.
	
	Args:
		lead_id (str): Lead name/ID
		action (str): "delete_with_trips" | "delete_keep_trips" | "orphan_trips"
	
	Returns:
		dict: Deletion summary
	"""
	try:
		# Get associated trips
		trips = frappe.get_all("Trip", filters={"lead": lead_id}, pluck="name")
		
		if action == "delete_with_trips":
			# Delete all trips first
			for trip_name in trips:
				frappe.delete_doc("Trip", trip_name, ignore_permissions=True)
		
		elif action == "delete_keep_trips":
			# Unlink trips (set lead to null)
			for trip_name in trips:
				trip_doc = frappe.get_doc("Trip", trip_name)
				trip_doc.lead = None
				trip_doc.save(ignore_permissions=True)
		
		elif action == "orphan_trips":
			# Leave trips as-is (they'll become orphaned)
			pass
		
		# Delete the lead
		frappe.delete_doc("CRM Lead", lead_id, ignore_permissions=True)
		
		return {
			"message": f"Lead {lead_id} deleted successfully",
			"trips_affected": len(trips),
			"action_taken": action
		}
		
	except Exception as e:
		frappe.throw(_("Failed to delete Lead: {0}").format(str(e)))


# =============================================================================
# TRIP CRUD OPERATIONS
# =============================================================================

@frappe.whitelist()
def create_trip(lead_id, trip_data):
	"""
	Create a new Trip for existing Lead.
	
	Args:
		lead_id (str): Lead name/ID
		trip_data (dict|list): Single trip or list of trips
	
	Returns:
		dict: Created trip(s)
	"""
	try:
		if isinstance(trip_data, str):
			trip_data = json.loads(trip_data)
		
		# Verify lead exists
		if not frappe.db.exists("CRM Lead", lead_id):
			frappe.throw(_("Lead {0} not found").format(lead_id))
		
		trips = []
		trip_list = trip_data if isinstance(trip_data, list) else [trip_data]
		
		for trip in trip_list:
			trip_doc = _create_trip_for_lead(lead_id, trip)
			trips.append(trip_doc.as_dict())
		
		return {
			"trips": trips,
			"count": len(trips)
		}
		
	except Exception as e:
		frappe.throw(_("Failed to create Trip: {0}").format(str(e)))


@frappe.whitelist()
def get_trip(trip_id):
	"""
	Get a single Trip.
	
	Args:
		trip_id (str): Trip name/ID
	
	Returns:
		dict: Trip data
	"""
	try:
		trip_doc = frappe.get_doc("Trip", trip_id)
		return trip_doc.as_dict()
		
	except Exception as e:
		frappe.throw(_("Failed to get Trip: {0}").format(str(e)))


@frappe.whitelist()
def update_trip(trip_id, trip_data):
	"""
	Update Trip data.
	
	Args:
		trip_id (str): Trip name/ID
		trip_data (dict): Fields to update
	
	Returns:
		dict: Updated trip data
	"""
	try:
		if isinstance(trip_data, str):
			trip_data = json.loads(trip_data)
		
		trip_doc = frappe.get_doc("Trip", trip_id)
		
		# Handle child table fields
		for field, value in trip_data.items():
			if field in ["destination_city", "passenger_details", "activity"]:
				# Clear existing child table
				setattr(trip_doc, field, [])
				# Add new rows
				if value and isinstance(value, list):
					for row in value:
						# Special handling for activity field
						if field == "activity":
							# Ensure activity is a dictionary with required fields
							if isinstance(row, str):
								row = {"activity": row}
							
							# Create Activity List record if it doesn't exist
							activity_name = row.get("activity")
							if activity_name:
								try:
									if not frappe.db.exists("Activity List", activity_name):
										activity_doc = frappe.new_doc("Activity List")
										activity_doc.activity = activity_name
										activity_doc.insert(ignore_permissions=True)
										frappe.log_error(f"Created Activity List: {activity_name}", "Trip Activity Creation")
									
									# Only append the activity if it exists or was successfully created
									trip_doc.append(field, row)
								except Exception as activity_error:
									frappe.log_error(f"Failed to create Activity List '{activity_name}': {activity_error}", "Trip Activity Creation Error")
									# Skip this activity rather than failing the entire operation
									pass
					else:
						trip_doc.append(field, row)
			else:
				setattr(trip_doc, field, value)
		
		trip_doc.save(ignore_permissions=True)
		return trip_doc.as_dict()
		
	except Exception as e:
		frappe.throw(_("Failed to update Trip: {0}").format(str(e)))


@frappe.whitelist()
def delete_trip(trip_ids):
	"""
	Delete one or multiple Trips.
	
	Args:
		trip_ids (str|list): Single trip ID or list of trip IDs
	
	Returns:
		dict: Deletion summary
	"""
	try:
		if isinstance(trip_ids, str):
			try:
				trip_ids = json.loads(trip_ids)
			except:
				trip_ids = [trip_ids]
		
		deleted_count = 0
		for trip_id in trip_ids:
			if frappe.db.exists("Trip", trip_id):
				frappe.delete_doc("Trip", trip_id, ignore_permissions=True)
				deleted_count += 1
		
		return {
			"message": f"Deleted {deleted_count} trip(s) successfully",
			"deleted_count": deleted_count,
			"requested_count": len(trip_ids)
		}
		
	except Exception as e:
		frappe.throw(_("Failed to delete Trip(s): {0}").format(str(e)))


# =============================================================================
# BULK OPERATIONS
# =============================================================================

@frappe.whitelist()
def bulk_update_trips(lead_id, trips_data):
	"""
	Bulk update/create/delete trips for a Lead.
	
	Args:
		lead_id (str): Lead name/ID
		trips_data (list): List of trip operations
	
	Example:
		{
			"trips_data": [
				{"action": "create", "data": {"title": "New Trip"}},
				{"action": "update", "trip_id": "TRIP-001", "data": {"title": "Updated"}},
				{"action": "delete", "trip_id": "TRIP-002"}
			]
		}
	
	Returns:
		dict: Operation summary
	"""
	try:
		if isinstance(trips_data, str):
			trips_data = json.loads(trips_data)
		
		results = {
			"created": [],
			"updated": [],
			"deleted": [],
			"errors": []
		}
		
		for operation in trips_data:
			try:
				action = operation.get("action")
				
				if action == "create":
					trip_doc = _create_trip_for_lead(lead_id, operation.get("data", {}))
					results["created"].append(trip_doc.name)
				
				elif action == "update":
					trip_id = operation.get("trip_id")
					update_trip(trip_id, operation.get("data", {}))
					results["updated"].append(trip_id)
				
				elif action == "delete":
					trip_id = operation.get("trip_id")
					delete_trip([trip_id])
					results["deleted"].append(trip_id)
				
			except Exception as e:
				results["errors"].append({
					"operation": operation,
					"error": str(e)
				})
		
		return results
		
	except Exception as e:
		frappe.throw(_("Bulk operation failed: {0}").format(str(e)))


@frappe.whitelist()
def get_lead_trips(lead_id, filters=None):
	"""
	Get all trips for a Lead with optional filtering.
	
	Args:
		lead_id (str): Lead name/ID
		filters (dict): Additional filters (optional)
	
	Returns:
		list: Trip data
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		base_filters = {"lead": lead_id}
		if filters:
			base_filters.update(filters)
		
		# Get Trip names first, then full documents
		trip_names = frappe.get_all(
			"Trip",
			filters=base_filters,
			pluck="name",
			order_by="creation desc"
		)
		
		trips = []
		for trip_name in trip_names:
			trip_doc = frappe.get_doc("Trip", trip_name)
			trips.append(trip_doc.as_dict())
		
		return trips
		
	except Exception as e:
		frappe.throw(_("Failed to get trips: {0}").format(str(e)))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _create_trip_for_lead(lead_id, trip_data):
	"""Helper function to create a trip for a lead"""
	trip_doc = frappe.new_doc("Trip")
	
	# Set lead relationship
	trip_doc.lead = lead_id
	
	# Set basic fields with defaults
	trip_doc.update({
		"title": trip_data.get("title", f"Trip for {lead_id}"),
		"start_date": trip_data.get("start_date"),
		"end_date": trip_data.get("end_date"),
		"budget": trip_data.get("budget"),
		"pax": trip_data.get("pax", 1),
		"category": trip_data.get("category"),
		"no_of_rooms": trip_data.get("no_of_rooms", 1),
		"flexible_days": trip_data.get("flexible_days", 0),
	})
	
	# Handle child table fields
	child_fields = ["destination_city", "passenger_details", "activity"]
	for field in child_fields:
		if field in trip_data and trip_data[field]:
			for row in trip_data[field]:
				# Special handling for activity field
				if field == "activity":
					# Ensure activity is a dictionary with required fields
					if isinstance(row, str):
						row = {"activity": row}
					
					# Create Activity List record if it doesn't exist
					activity_name = row.get("activity")
					if activity_name:
						try:
							if not frappe.db.exists("Activity List", activity_name):
								activity_doc = frappe.new_doc("Activity List")
								activity_doc.activity = activity_name
								activity_doc.insert(ignore_permissions=True)
								frappe.log_error(f"Created Activity List: {activity_name}", "Trip Activity Creation")
							
							# Only append the activity if it exists or was successfully created
							trip_doc.append(field, row)
						except Exception as activity_error:
							frappe.log_error(f"Failed to create Activity List '{activity_name}': {activity_error}", "Trip Activity Creation Error")
							# Skip this activity rather than failing the entire operation
							pass
				else:
					trip_doc.append(field, row)
	
	trip_doc.insert(ignore_permissions=True)
	return trip_doc


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@frappe.whitelist()
def get_lead_summary(lead_id):
	"""
	Get Lead summary with trip count and basic stats.
	
	Args:
		lead_id (str): Lead name/ID
	
	Returns:
		dict: Lead summary
	"""
	try:
		lead_doc = frappe.get_doc("CRM Lead", lead_id)
		
		# Get trip statistics
		trip_count = frappe.db.count("Trip", {"lead": lead_id})
		total_budget = frappe.db.sql("""
			SELECT SUM(budget) as total_budget
			FROM `tabTrip`
			WHERE lead = %s AND budget IS NOT NULL
		""", (lead_id,))[0][0] or 0
		
		return {
			"lead": {
				"name": lead_doc.name,
				"lead_name": lead_doc.lead_name,
				"status": lead_doc.status,
				"source": lead_doc.source,
				"creation": lead_doc.creation
			},
			"trip_stats": {
				"count": trip_count,
				"total_budget": total_budget
			}
		}
		
	except Exception as e:
		frappe.throw(_("Failed to get summary: {0}").format(str(e)))


@frappe.whitelist()
def search_leads_with_trips(query="", filters=None, limit=20):
	"""
	Search Leads with Trip data included.
	
	Args:
		query (str): Search term
		filters (dict): Additional filters
		limit (int): Result limit
	
	Returns:
		list: Lead data with trip counts
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters) if filters else {}
		
		# SECURE: Use parameterized queries to prevent SQL injection
		conditions = []
		params = []
		
		if query:
			# Escape query for LIKE search
			escaped_query = frappe.db.escape(f"%{query}%")
			conditions.append(f"(l.lead_name LIKE {escaped_query} OR l.email LIKE {escaped_query})")
		
		# SECURE: Validate filter fields against allowed fields
		allowed_filter_fields = ["status", "source", "lead_owner", "priority"]
		for key, value in (filters or {}).items():
			if key in allowed_filter_fields:
				conditions.append(f"l.{frappe.db.escape(key)} = %s")
				params.append(value)
		
		where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
		
		# SECURE: Validate and sanitize limit
		limit = min(int(limit or 20), 100)  # Max 100 results
		
		# Query with trip count using parameterized query
		results = frappe.db.sql(f"""
			SELECT 
				l.name,
				l.lead_name,
				l.email,
				l.status,
				l.source,
				l.creation,
				COUNT(t.name) as trip_count,
				SUM(t.budget) as total_budget
			FROM `tabCRM Lead` l
			LEFT JOIN `tabTrip` t ON t.lead = l.name
			{where_clause}
			GROUP BY l.name
			ORDER BY l.creation DESC
			LIMIT %s
		""", params + [limit], as_dict=True)
		
		return results
		
	except Exception as e:
		frappe.throw(_("Search failed: {0}").format(str(e)))