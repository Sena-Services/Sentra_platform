# Copyright (c) 2024, Sentra and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import validate_email_address
import json


# ========== ACTIVITY APIs ==========

@frappe.whitelist()
def get_activities(filters=None, fields=None, order_by=None, limit_start=0, limit_page_length=20):
	"""
	Get list of activities with filtering and pagination
	
	Args:
		filters (dict): Filter conditions
		fields (list): Fields to return
		order_by (str): Sort order
		limit_start (int): Pagination start
		limit_page_length (int): Number of records per page
	
	Returns:
		dict: List of activities with count
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		if isinstance(fields, str):
			fields = json.loads(fields)
		
		if not fields:
			fields = [
				"name", "activity_name", "activity_code", "activity_type", 
				"city", "status", "adult_price", "child_price", "currency",
				"venue_name", "difficulty_level", "creation", "modified"
			]
		
		activities = frappe.get_list(
			"Activity",
			filters=filters or {},
			fields=fields,
			order_by=order_by or "creation desc",
			start=int(limit_start),
			page_length=int(limit_page_length)
		)
		
		# Get total count
		total_count = frappe.db.count("Activity", filters=filters or {})
		
		return {
			"data": activities,
			"count": len(activities),
			"total_count": total_count,
			"limit_start": int(limit_start),
			"limit_page_length": int(limit_page_length)
		}
		
	except Exception as e:
		frappe.log_error(f"Error in get_activities: {str(e)}")
		frappe.throw(_("Failed to fetch activities: {0}").format(str(e)))


@frappe.whitelist()
def get_activity(name):
	"""
	Get single activity by name
	
	Args:
		name (str): Activity ID
		
	Returns:
		dict: Activity document
	"""
	try:
		if not frappe.db.exists("Activity", name):
			frappe.throw(_("Activity not found"))
		
		activity = frappe.get_doc("Activity", name)
		return activity.as_dict()
		
	except Exception as e:
		frappe.log_error(f"Error in get_activity: {str(e)}")
		frappe.throw(_("Failed to fetch activity: {0}").format(str(e)))


@frappe.whitelist()
def create_activity(activity_data):
	"""
	Create new activity
	
	Args:
		activity_data (dict): Activity data
		
	Returns:
		dict: Created activity document
	"""
	try:
		if isinstance(activity_data, str):
			activity_data = json.loads(activity_data)
		
		# Validate required fields
		required_fields = ["activity_name", "activity_code", "activity_type", "city", "currency", "pricing_type"]
		for field in required_fields:
			if not activity_data.get(field):
				frappe.throw(_("Field '{0}' is required").format(field))
		
		# Check if activity_code is unique
		if frappe.db.exists("Activity", {"activity_code": activity_data.get("activity_code")}):
			frappe.throw(_("Activity Code '{0}' already exists").format(activity_data.get("activity_code")))
		
		doc = frappe.new_doc("Activity")
		doc.update(activity_data)
		doc.insert()
		
		frappe.db.commit()
		
		return doc.as_dict()
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in create_activity: {str(e)}")
		frappe.throw(_("Failed to create activity: {0}").format(str(e)))


@frappe.whitelist()
def update_activity(name, activity_data):
	"""
	Update existing activity
	
	Args:
		name (str): Activity ID
		activity_data (dict): Updated activity data
		
	Returns:
		dict: Updated activity document
	"""
	try:
		if isinstance(activity_data, str):
			activity_data = json.loads(activity_data)
		
		if not frappe.db.exists("Activity", name):
			frappe.throw(_("Activity not found"))
		
		doc = frappe.get_doc("Activity", name)
		
		# Check if activity_code is being updated and is unique
		if "activity_code" in activity_data and activity_data["activity_code"] != doc.activity_code:
			if frappe.db.exists("Activity", {"activity_code": activity_data["activity_code"], "name": ["!=", name]}):
				frappe.throw(_("Activity Code '{0}' already exists").format(activity_data["activity_code"]))
		
		doc.update(activity_data)
		doc.save()
		
		frappe.db.commit()
		
		return doc.as_dict()
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in update_activity: {str(e)}")
		frappe.throw(_("Failed to update activity: {0}").format(str(e)))


@frappe.whitelist()
def delete_activity(name):
	"""
	Delete activity
	
	Args:
		name (str): Activity ID
		
	Returns:
		dict: Success message
	"""
	try:
		if not frappe.db.exists("Activity", name):
			frappe.throw(_("Activity not found"))
		
		frappe.delete_doc("Activity", name)
		frappe.db.commit()
		
		return {"message": _("Activity deleted successfully")}
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in delete_activity: {str(e)}")
		frappe.throw(_("Failed to delete activity: {0}").format(str(e)))


@frappe.whitelist()
def get_activities_by_city(city, filters=None, limit=50):
	"""
	Get activities by city with optional additional filters
	
	Args:
		city (str): City name
		filters (dict): Additional filters
		limit (int): Maximum results
		
	Returns:
		list: Activities in the specified city
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		base_filters = {"city": city, "status": "Active"}
		if filters:
			base_filters.update(filters)
		
		activities = frappe.get_list(
			"Activity",
			filters=base_filters,
			fields=[
				"name", "activity_name", "activity_code", "activity_type",
				"adult_price", "child_price", "currency", "venue_name",
				"difficulty_level", "duration_hours", "duration_minutes"
			],
			order_by="activity_name",
			limit=int(limit)
		)
		
		return activities
		
	except Exception as e:
		frappe.log_error(f"Error in get_activities_by_city: {str(e)}")
		frappe.throw(_("Failed to fetch activities by city: {0}").format(str(e)))


@frappe.whitelist()
def get_activities_by_type(activity_type, filters=None, limit=50):
	"""
	Get activities by activity type
	
	Args:
		activity_type (str): Activity type
		filters (dict): Additional filters
		limit (int): Maximum results
		
	Returns:
		list: Activities of the specified type
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		base_filters = {"activity_type": activity_type, "status": "Active"}
		if filters:
			base_filters.update(filters)
		
		activities = frappe.get_list(
			"Activity",
			filters=base_filters,
			fields=[
				"name", "activity_name", "activity_code", "city",
				"adult_price", "child_price", "currency", "venue_name",
				"difficulty_level", "duration_hours", "duration_minutes"
			],
			order_by="city, activity_name",
			limit=int(limit)
		)
		
		return activities
		
	except Exception as e:
		frappe.log_error(f"Error in get_activities_by_type: {str(e)}")
		frappe.throw(_("Failed to fetch activities by type: {0}").format(str(e)))


@frappe.whitelist()
def search_activities(query, filters=None, limit=20):
	"""
	Search activities by name, code, or description
	
	Args:
		query (str): Search query
		filters (dict): Additional filters
		limit (int): Maximum results
		
	Returns:
		list: Matching activities
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		base_filters = {"status": "Active"}
		if filters:
			base_filters.update(filters)
		
		# Search in multiple fields
		or_filters = [
			["activity_name", "like", f"%{query}%"],
			["activity_code", "like", f"%{query}%"],
			["description", "like", f"%{query}%"],
			["venue_name", "like", f"%{query}%"]
		]
		
		activities = frappe.get_list(
			"Activity",
			filters=base_filters,
			or_filters=or_filters,
			fields=[
				"name", "activity_name", "activity_code", "activity_type",
				"city", "adult_price", "child_price", "currency",
				"venue_name", "difficulty_level"
			],
			order_by="activity_name",
			limit=int(limit)
		)
		
		return activities
		
	except Exception as e:
		frappe.log_error(f"Error in search_activities: {str(e)}")
		frappe.throw(_("Failed to search activities: {0}").format(str(e)))


@frappe.whitelist()
def get_activity_stats():
	"""
	Get activity statistics
	
	Returns:
		dict: Activity statistics
	"""
	try:
		stats = {
			"total_activities": frappe.db.count("Activity"),
			"active_activities": frappe.db.count("Activity", {"status": "Active"}),
			"by_type": {},
			"by_city": {},
			"by_difficulty": {}
		}
		
		# Activities by type
		type_stats = frappe.db.sql("""
			SELECT activity_type, COUNT(*) as count
			FROM `tabActivity`
			WHERE status = 'Active'
			GROUP BY activity_type
			ORDER BY count DESC
		""", as_dict=True)
		
		stats["by_type"] = {item["activity_type"]: item["count"] for item in type_stats if item["activity_type"]}
		
		# Activities by city
		city_stats = frappe.db.sql("""
			SELECT city, COUNT(*) as count
			FROM `tabActivity`
			WHERE status = 'Active' AND city IS NOT NULL
			GROUP BY city
			ORDER BY count DESC
			LIMIT 10
		""", as_dict=True)
		
		stats["by_city"] = {item["city"]: item["count"] for item in city_stats}
		
		# Activities by difficulty
		difficulty_stats = frappe.db.sql("""
			SELECT difficulty_level, COUNT(*) as count
			FROM `tabActivity`
			WHERE status = 'Active' AND difficulty_level IS NOT NULL
			GROUP BY difficulty_level
			ORDER BY count DESC
		""", as_dict=True)
		
		stats["by_difficulty"] = {item["difficulty_level"]: item["count"] for item in difficulty_stats}
		
		return stats
		
	except Exception as e:
		frappe.log_error(f"Error in get_activity_stats: {str(e)}")
		frappe.throw(_("Failed to fetch activity statistics: {0}").format(str(e)))


# ========== DMC APIs ==========

@frappe.whitelist()
def get_dmcs(filters=None, fields=None, order_by=None, limit_start=0, limit_page_length=20):
	"""
	Get list of DMCs with filtering and pagination
	
	Args:
		filters (dict): Filter conditions
		fields (list): Fields to return
		order_by (str): Sort order
		limit_start (int): Pagination start
		limit_page_length (int): Number of records per page
	
	Returns:
		dict: List of DMCs with count
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		if isinstance(fields, str):
			fields = json.loads(fields)
		
		if not fields:
			fields = [
				"name", "company_name", "dmc_code", "city", "country", 
				"status", "primary_email", "primary_phone", "specialization",
				"commission_percentage", "payment_terms", "creation", "modified"
			]
		
		dmcs = frappe.get_list(
			"DMC",
			filters=filters or {},
			fields=fields,
			order_by=order_by or "creation desc",
			start=int(limit_start),
			page_length=int(limit_page_length)
		)
		
		# Get total count
		total_count = frappe.db.count("DMC", filters=filters or {})
		
		return {
			"data": dmcs,
			"count": len(dmcs),
			"total_count": total_count,
			"limit_start": int(limit_start),
			"limit_page_length": int(limit_page_length)
		}
		
	except Exception as e:
		frappe.log_error(f"Error in get_dmcs: {str(e)}")
		frappe.throw(_("Failed to fetch DMCs: {0}").format(str(e)))


@frappe.whitelist()
def get_dmc(name):
	"""
	Get single DMC by name
	
	Args:
		name (str): DMC ID
		
	Returns:
		dict: DMC document
	"""
	try:
		if not frappe.db.exists("DMC", name):
			frappe.throw(_("DMC not found"))
		
		dmc = frappe.get_doc("DMC", name)
		return dmc.as_dict()
		
	except Exception as e:
		frappe.log_error(f"Error in get_dmc: {str(e)}")
		frappe.throw(_("Failed to fetch DMC: {0}").format(str(e)))


@frappe.whitelist()
def create_dmc(dmc_data):
	"""
	Create new DMC
	
	Args:
		dmc_data (dict): DMC data
		
	Returns:
		dict: Created DMC document
	"""
	try:
		if isinstance(dmc_data, str):
			dmc_data = json.loads(dmc_data)
		
		# Validate required fields
		required_fields = ["company_name", "dmc_code", "city", "country", "address_line_1"]
		for field in required_fields:
			if not dmc_data.get(field):
				frappe.throw(_("Field '{0}' is required").format(field))
		
		# Check if dmc_code is unique
		if frappe.db.exists("DMC", {"dmc_code": dmc_data.get("dmc_code")}):
			frappe.throw(_("DMC Code '{0}' already exists").format(dmc_data.get("dmc_code")))
		
		# Validate email if provided
		if dmc_data.get("primary_email"):
			validate_email_address(dmc_data.get("primary_email"), True)
		
		doc = frappe.new_doc("DMC")
		doc.update(dmc_data)
		doc.insert()
		
		frappe.db.commit()
		
		return doc.as_dict()
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in create_dmc: {str(e)}")
		frappe.throw(_("Failed to create DMC: {0}").format(str(e)))


@frappe.whitelist()
def update_dmc(name, dmc_data):
	"""
	Update existing DMC
	
	Args:
		name (str): DMC ID
		dmc_data (dict): Updated DMC data
		
	Returns:
		dict: Updated DMC document
	"""
	try:
		if isinstance(dmc_data, str):
			dmc_data = json.loads(dmc_data)
		
		if not frappe.db.exists("DMC", name):
			frappe.throw(_("DMC not found"))
		
		doc = frappe.get_doc("DMC", name)
		
		# Check if dmc_code is being updated and is unique
		if "dmc_code" in dmc_data and dmc_data["dmc_code"] != doc.dmc_code:
			if frappe.db.exists("DMC", {"dmc_code": dmc_data["dmc_code"], "name": ["!=", name]}):
				frappe.throw(_("DMC Code '{0}' already exists").format(dmc_data["dmc_code"]))
		
		# Validate email if provided
		if dmc_data.get("primary_email"):
			validate_email_address(dmc_data.get("primary_email"), True)
		
		doc.update(dmc_data)
		doc.save()
		
		frappe.db.commit()
		
		return doc.as_dict()
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in update_dmc: {str(e)}")
		frappe.throw(_("Failed to update DMC: {0}").format(str(e)))


@frappe.whitelist()
def delete_dmc(name):
	"""
	Delete DMC
	
	Args:
		name (str): DMC ID
		
	Returns:
		dict: Success message
	"""
	try:
		if not frappe.db.exists("DMC", name):
			frappe.throw(_("DMC not found"))
		
		frappe.delete_doc("DMC", name)
		frappe.db.commit()
		
		return {"message": _("DMC deleted successfully")}
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in delete_dmc: {str(e)}")
		frappe.throw(_("Failed to delete DMC: {0}").format(str(e)))


@frappe.whitelist()
def get_dmcs_by_city(city, filters=None, limit=50):
	"""
	Get DMCs by city with optional additional filters
	
	Args:
		city (str): City name
		filters (dict): Additional filters
		limit (int): Maximum results
		
	Returns:
		list: DMCs in the specified city
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		base_filters = {"city": city, "status": "Active"}
		if filters:
			base_filters.update(filters)
		
		dmcs = frappe.get_list(
			"DMC",
			filters=base_filters,
			fields=[
				"name", "company_name", "dmc_code", "country",
				"primary_email", "primary_phone", "specialization",
				"commission_percentage", "payment_terms"
			],
			order_by="company_name",
			limit=int(limit)
		)
		
		return dmcs
		
	except Exception as e:
		frappe.log_error(f"Error in get_dmcs_by_city: {str(e)}")
		frappe.throw(_("Failed to fetch DMCs by city: {0}").format(str(e)))


@frappe.whitelist()
def get_dmcs_by_country(country, filters=None, limit=50):
	"""
	Get DMCs by country
	
	Args:
		country (str): Country name
		filters (dict): Additional filters
		limit (int): Maximum results
		
	Returns:
		list: DMCs in the specified country
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		base_filters = {"country": country, "status": "Active"}
		if filters:
			base_filters.update(filters)
		
		dmcs = frappe.get_list(
			"DMC",
			filters=base_filters,
			fields=[
				"name", "company_name", "dmc_code", "city",
				"primary_email", "primary_phone", "specialization",
				"commission_percentage", "payment_terms"
			],
			order_by="city, company_name",
			limit=int(limit)
		)
		
		return dmcs
		
	except Exception as e:
		frappe.log_error(f"Error in get_dmcs_by_country: {str(e)}")
		frappe.throw(_("Failed to fetch DMCs by country: {0}").format(str(e)))


@frappe.whitelist()
def search_dmcs(query, filters=None, limit=20):
	"""
	Search DMCs by name, code, or specialization
	
	Args:
		query (str): Search query
		filters (dict): Additional filters
		limit (int): Maximum results
		
	Returns:
		list: Matching DMCs
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		base_filters = {"status": "Active"}
		if filters:
			base_filters.update(filters)
		
		# Search in multiple fields
		or_filters = [
			["company_name", "like", f"%{query}%"],
			["dmc_code", "like", f"%{query}%"],
			["specialization", "like", f"%{query}%"],
			["services_offered", "like", f"%{query}%"]
		]
		
		dmcs = frappe.get_list(
			"DMC",
			filters=base_filters,
			or_filters=or_filters,
			fields=[
				"name", "company_name", "dmc_code", "city", "country",
				"primary_email", "primary_phone", "specialization",
				"commission_percentage"
			],
			order_by="company_name",
			limit=int(limit)
		)
		
		return dmcs
		
	except Exception as e:
		frappe.log_error(f"Error in search_dmcs: {str(e)}")
		frappe.throw(_("Failed to search DMCs: {0}").format(str(e)))


@frappe.whitelist()
def get_dmc_stats():
	"""
	Get DMC statistics
	
	Returns:
		dict: DMC statistics
	"""
	try:
		stats = {
			"total_dmcs": frappe.db.count("DMC"),
			"active_dmcs": frappe.db.count("DMC", {"status": "Active"}),
			"by_country": {},
			"by_city": {},
			"by_specialization": {}
		}
		
		# DMCs by country
		country_stats = frappe.db.sql("""
			SELECT country, COUNT(*) as count
			FROM `tabDMC`
			WHERE status = 'Active' AND country IS NOT NULL
			GROUP BY country
			ORDER BY count DESC
			LIMIT 10
		""", as_dict=True)
		
		stats["by_country"] = {item["country"]: item["count"] for item in country_stats}
		
		# DMCs by city
		city_stats = frappe.db.sql("""
			SELECT city, COUNT(*) as count
			FROM `tabDMC`
			WHERE status = 'Active' AND city IS NOT NULL
			GROUP BY city
			ORDER BY count DESC
			LIMIT 10
		""", as_dict=True)
		
		stats["by_city"] = {item["city"]: item["count"] for item in city_stats}
		
		# DMCs by specialization (this would need parsing since it's a long text field)
		specialization_stats = frappe.db.sql("""
			SELECT 
				CASE 
					WHEN specialization LIKE '%Adventure%' THEN 'Adventure Tourism'
					WHEN specialization LIKE '%Cultural%' THEN 'Cultural Tourism'
					WHEN specialization LIKE '%Wildlife%' THEN 'Wildlife Tourism'
					WHEN specialization LIKE '%Luxury%' THEN 'Luxury Travel'
					WHEN specialization LIKE '%Budget%' THEN 'Budget Travel'
					WHEN specialization LIKE '%Corporate%' THEN 'Corporate Travel'
					WHEN specialization LIKE '%Medical%' THEN 'Medical Tourism'
					WHEN specialization LIKE '%Religious%' THEN 'Religious Tourism'
					ELSE 'Other'
				END as specialization_type,
				COUNT(*) as count
			FROM `tabDMC`
			WHERE status = 'Active' AND specialization IS NOT NULL
			GROUP BY specialization_type
			ORDER BY count DESC
		""", as_dict=True)
		
		stats["by_specialization"] = {item["specialization_type"]: item["count"] for item in specialization_stats}
		
		return stats
		
	except Exception as e:
		frappe.log_error(f"Error in get_dmc_stats: {str(e)}")
		frappe.throw(_("Failed to fetch DMC statistics: {0}").format(str(e)))


# ========== EXISTING APIs ==========

@frappe.whitelist(allow_guest=True)
def get_conversation_history(phone_number=None, contact_name=None, medium=None):
	"""
	Retrieve the message history for a conversation, identified by phone number or contact name.
	If medium is not provided, it will fetch messages across all mediums.
	"""
	if not phone_number and not contact_name:
		frappe.throw("Please provide either a phone_number or a contact_name.")

	# Find all parent Communication documents
	parent_comms = find_conversations(phone_number, contact_name, medium)
	if not parent_comms:
		return []

	parent_comm_names = [d.name for d in parent_comms]

	# Retrieve all comments (which represent the messages) for all found conversations
	comments = frappe.get_all(
		"Comment",
		filters={"reference_doctype": "Communication", "reference_name": ["in", parent_comm_names]},
		fields=["content", "creation", "owner"],
		order_by="creation asc",
	)

	return comments


def find_conversations(phone_number=None, contact_name=None, medium=None):
	"""
	Find all parent Communication documents for a conversation.
	Returns a list of documents.
	"""
	filters = {"communication_medium": medium} if medium else {}
	comm_names = set()

	if contact_name:
		names = frappe.get_all(
			"Communication",
			filters={**filters, "reference_doctype": "Contact", "reference_name": contact_name},
			pluck="name",
		)
		comm_names.update(names)

	if phone_number:
		# First, try to find a communication linked to a Contact with this phone number
		contact_for_phone = frappe.db.get_value("Contact Phone", {"phone": phone_number}, "parent")
		if contact_for_phone:
			names = frappe.get_all(
				"Communication",
				filters={**filters, "reference_doctype": "Contact", "reference_name": contact_for_phone},
				pluck="name",
			)
			comm_names.update(names)

		# If no contact-linked communication, find one by phone number
		names = frappe.get_all("Communication", filters={**filters, "phone_no": phone_number}, pluck="name")
		comm_names.update(names)

	if not comm_names:
		return []

	# Return a list of documents
	return [frappe.get_doc("Communication", name) for name in comm_names] 


@frappe.whitelist()
def create_trip_with_destinations(doc):
	"""
	Create a Trip with auto-creation of destinations if they don't exist
	"""
	import json
	
	# Parse the doc if it's a string
	if isinstance(doc, str):
		doc = json.loads(doc)
	
	# Auto-create destinations first
	if doc.get('destination_city'):
		for destination_row in doc['destination_city']:
			destination_name = destination_row.get('destination', '').strip()
			if destination_name:
				# Check if destination exists (case-insensitive)
				existing_destination = frappe.db.get_value("Destination", 
					{"city": ["like", f"%{destination_name}%"]}, "name")
				
				if not existing_destination:
					# Auto-create the destination
					new_destination = frappe.new_doc("Destination")
					new_destination.city = destination_name.title()  # Title case
					new_destination.country = "Unknown"  # Default country
					try:
						new_destination.insert(ignore_permissions=True)
						destination_row['destination'] = new_destination.name
						frappe.logger().info(f"Auto-created destination: {new_destination.name}")
					except Exception as e:
						frappe.logger().error(f"Failed to create destination {destination_name}: {str(e)}")
						frappe.throw(f"Could not create destination '{destination_name}'. Error: {str(e)}")
				else:
					# Use the existing destination name
					destination_row['destination'] = existing_destination
	
	# Now create the Trip
	trip = frappe.new_doc("Trip")
	trip.update(doc)
	trip.insert(ignore_permissions=True)
	return trip.as_dict()


@frappe.whitelist()
def insert_trip_ignore_links(doc):
	"""
	Create a Trip using ignore_links=True to bypass destination validation
	Note: This will create the trip even if destinations don't exist
	"""
	import json
	
	# Parse the doc if it's a string
	if isinstance(doc, str):
		doc = json.loads(doc)
	
	# Create the Trip with link validation disabled
	trip = frappe.new_doc("Trip")
	trip.update(doc)
	trip.insert(ignore_permissions=True, ignore_links=True)
	return trip.as_dict()


# ========== STANDARD PACKAGE APIs ==========

@frappe.whitelist()
def get_packages(filters=None, fields=None, order_by=None, limit_start=0, limit_page_length=20):
	"""
	Get list of standard packages with filtering and pagination
	
	Args:
		filters (dict): Filter conditions
		fields (list): Fields to return
		order_by (str): Sort order
		limit_start (int): Pagination start
		limit_page_length (int): Number of records per page
	
	Returns:
		dict: List of packages with count
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		if isinstance(fields, str):
			fields = json.loads(fields)
		
		if not fields:
			fields = [
				"name", "package_name", "package_code", "status", 
				"dmc", "valid_from", "valid_to", "base_cost", 
				"net_price", "currency", "min_group_size", 
				"max_group_size", "creation", "modified"
			]
		
		packages = frappe.get_list(
			"Standard Package",
			filters=filters or {},
			fields=fields,
			order_by=order_by or "creation desc",
			start=int(limit_start),
			page_length=int(limit_page_length)
		)
		
		# Get total count
		total_count = frappe.db.count("Standard Package", filters=filters or {})
		
		return {
			"data": packages,
			"count": len(packages),
			"total_count": total_count,
			"limit_start": int(limit_start),
			"limit_page_length": int(limit_page_length)
		}
		
	except Exception as e:
		frappe.log_error(f"Error in get_packages: {str(e)}")
		frappe.throw(_("Failed to fetch packages: {0}").format(str(e)))


@frappe.whitelist()
def get_package(name):
	"""
	Get single package by name with full details including itinerary
	
	Args:
		name (str): Package ID
		
	Returns:
		dict: Package document with all child tables
	"""
	try:
		if not frappe.db.exists("Standard Package", name):
			frappe.throw(_("Package not found"))
		
		package = frappe.get_doc("Standard Package", name)
		
		# Parse JSON itinerary data if exists
		package_dict = package.as_dict()
		if package_dict.get("itinerary_data"):
			try:
				package_dict["itinerary_data"] = json.loads(package_dict["itinerary_data"])
			except:
				pass  # If parsing fails, leave as is
		
		return package_dict
		
	except Exception as e:
		frappe.log_error(f"Error in get_package: {str(e)}")
		frappe.throw(_("Failed to fetch package: {0}").format(str(e)))


@frappe.whitelist()
def create_package(package_data):
	"""
	Create new standard package
	
	Args:
		package_data (dict): Package data including child tables
		
	Returns:
		dict: Created package document
	"""
	try:
		if isinstance(package_data, str):
			package_data = json.loads(package_data)
		
		# Validate required fields
		required_fields = ["package_name", "package_code", "dmc", "valid_from", "valid_to", 
						   "currency", "base_cost", "markup_percentage"]
		for field in required_fields:
			if not package_data.get(field):
				frappe.throw(_("Field '{0}' is required").format(field))
		
		# Check if package_code is unique
		if frappe.db.exists("Standard Package", {"package_code": package_data.get("package_code")}):
			frappe.throw(_("Package Code '{0}' already exists").format(package_data.get("package_code")))
		
		# Validate dates
		if package_data.get("valid_from") and package_data.get("valid_to"):
			from frappe.utils import getdate
			if getdate(package_data["valid_from"]) > getdate(package_data["valid_to"]):
				frappe.throw(_("Valid From date cannot be after Valid To date"))
		
		# Convert itinerary data to JSON if provided as dict
		if package_data.get("itinerary_data") and isinstance(package_data["itinerary_data"], (dict, list)):
			package_data["itinerary_data"] = json.dumps(package_data["itinerary_data"])
		
		# Calculate net price if base_cost and markup are provided
		if package_data.get("base_cost") and package_data.get("markup_percentage"):
			base_cost = float(package_data["base_cost"])
			markup = float(package_data["markup_percentage"])
			package_data["net_price"] = base_cost * (1 + markup / 100)
		
		doc = frappe.new_doc("Standard Package")
		doc.update(package_data)
		doc.insert()
		
		frappe.db.commit()
		
		return doc.as_dict()
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in create_package: {str(e)}")
		frappe.throw(_("Failed to create package: {0}").format(str(e)))


@frappe.whitelist()
def update_package(name, package_data):
	"""
	Update existing standard package
	
	Args:
		name (str): Package ID
		package_data (dict): Updated package data
		
	Returns:
		dict: Updated package document
	"""
	try:
		if isinstance(package_data, str):
			package_data = json.loads(package_data)
		
		if not frappe.db.exists("Standard Package", name):
			frappe.throw(_("Package not found"))
		
		doc = frappe.get_doc("Standard Package", name)
		
		# Check if package_code is being updated and is unique
		if "package_code" in package_data and package_data["package_code"] != doc.package_code:
			if frappe.db.exists("Standard Package", {"package_code": package_data["package_code"], "name": ["!=", name]}):
				frappe.throw(_("Package Code '{0}' already exists").format(package_data["package_code"]))
		
		# Validate dates if provided
		if package_data.get("valid_from") or package_data.get("valid_to"):
			from frappe.utils import getdate
			valid_from = getdate(package_data.get("valid_from", doc.valid_from))
			valid_to = getdate(package_data.get("valid_to", doc.valid_to))
			if valid_from > valid_to:
				frappe.throw(_("Valid From date cannot be after Valid To date"))
		
		# Convert itinerary data to JSON if provided as dict
		if package_data.get("itinerary_data") and isinstance(package_data["itinerary_data"], (dict, list)):
			package_data["itinerary_data"] = json.dumps(package_data["itinerary_data"])
		
		# Recalculate net price if base_cost or markup changed
		if "base_cost" in package_data or "markup_percentage" in package_data:
			base_cost = float(package_data.get("base_cost", doc.base_cost))
			markup = float(package_data.get("markup_percentage", doc.markup_percentage))
			package_data["net_price"] = base_cost * (1 + markup / 100)
		
		doc.update(package_data)
		doc.save()
		
		frappe.db.commit()
		
		return doc.as_dict()
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in update_package: {str(e)}")
		frappe.throw(_("Failed to update package: {0}").format(str(e)))


@frappe.whitelist()
def delete_package(name):
	"""
	Delete standard package
	
	Args:
		name (str): Package ID
		
	Returns:
		dict: Success message
	"""
	try:
		if not frappe.db.exists("Standard Package", name):
			frappe.throw(_("Package not found"))
		
		frappe.delete_doc("Standard Package", name)
		frappe.db.commit()
		
		return {"message": _("Package deleted successfully")}
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in delete_package: {str(e)}")
		frappe.throw(_("Failed to delete package: {0}").format(str(e)))


@frappe.whitelist()
def get_active_packages(filters=None, limit=50):
	"""
	Get active packages (status = Active and within valid dates)
	
	Args:
		filters (dict): Additional filters
		limit (int): Maximum results
		
	Returns:
		list: Active packages
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		from frappe.utils import today
		base_filters = {
			"status": "Active",
			"valid_from": ["<=", today()],
			"valid_to": [">=", today()]
		}
		if filters:
			base_filters.update(filters)
		
		packages = frappe.get_list(
			"Standard Package",
			filters=base_filters,
			fields=[
				"name", "package_name", "package_code", "dmc",
				"base_cost", "net_price", "currency",
				"min_group_size", "max_group_size",
				"valid_from", "valid_to"
			],
			order_by="package_name",
			limit=int(limit)
		)
		
		return packages
		
	except Exception as e:
		frappe.log_error(f"Error in get_active_packages: {str(e)}")
		frappe.throw(_("Failed to fetch active packages: {0}").format(str(e)))


@frappe.whitelist()
def get_packages_by_dmc(dmc, filters=None, limit=50):
	"""
	Get packages by DMC provider
	
	Args:
		dmc (str): DMC name
		filters (dict): Additional filters
		limit (int): Maximum results
		
	Returns:
		list: Packages by the specified DMC
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		base_filters = {"dmc": dmc}
		if filters:
			base_filters.update(filters)
		
		packages = frappe.get_list(
			"Standard Package",
			filters=base_filters,
			fields=[
				"name", "package_name", "package_code", "status",
				"valid_from", "valid_to", "base_cost", "net_price",
				"currency", "min_group_size", "max_group_size"
			],
			order_by="package_name",
			limit=int(limit)
		)
		
		return packages
		
	except Exception as e:
		frappe.log_error(f"Error in get_packages_by_dmc: {str(e)}")
		frappe.throw(_("Failed to fetch packages by DMC: {0}").format(str(e)))


@frappe.whitelist()
def search_packages(query, filters=None, limit=20):
	"""
	Search packages by name, code, or description
	
	Args:
		query (str): Search query
		filters (dict): Additional filters
		limit (int): Maximum results
		
	Returns:
		list: Matching packages
	"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		base_filters = {}
		if filters:
			base_filters.update(filters)
		
		# Search in multiple fields
		or_filters = [
			["package_name", "like", f"%{query}%"],
			["package_code", "like", f"%{query}%"],
			["description", "like", f"%{query}%"],
			["notes", "like", f"%{query}%"]
		]
		
		packages = frappe.get_list(
			"Standard Package",
			filters=base_filters,
			or_filters=or_filters,
			fields=[
				"name", "package_name", "package_code", "status",
				"dmc", "base_cost", "net_price", "currency",
				"valid_from", "valid_to"
			],
			order_by="package_name",
			limit=int(limit)
		)
		
		return packages
		
	except Exception as e:
		frappe.log_error(f"Error in search_packages: {str(e)}")
		frappe.throw(_("Failed to search packages: {0}").format(str(e)))


@frappe.whitelist()
def get_package_stats():
	"""
	Get package statistics
	
	Returns:
		dict: Package statistics
	"""
	try:
		from frappe.utils import today
		
		stats = {
			"total_packages": frappe.db.count("Standard Package"),
			"active_packages": frappe.db.count("Standard Package", {
				"status": "Active",
				"valid_from": ["<=", today()],
				"valid_to": [">=", today()]
			}),
			"draft_packages": frappe.db.count("Standard Package", {"status": "Draft"}),
			"archived_packages": frappe.db.count("Standard Package", {"status": "Archived"}),
			"by_dmc": {},
			"price_range": {}
		}
		
		# Packages by DMC
		dmc_stats = frappe.db.sql("""
			SELECT dmc, COUNT(*) as count
			FROM `tabStandard Package`
			WHERE status = 'Active'
			GROUP BY dmc
			ORDER BY count DESC
			LIMIT 10
		""", as_dict=True)
		
		stats["by_dmc"] = {item["dmc"]: item["count"] for item in dmc_stats if item["dmc"]}
		
		# Price range statistics
		price_stats = frappe.db.sql("""
			SELECT 
				MIN(net_price) as min_price,
				MAX(net_price) as max_price,
				AVG(net_price) as avg_price
			FROM `tabStandard Package`
			WHERE status = 'Active' AND net_price > 0
		""", as_dict=True)
		
		if price_stats:
			stats["price_range"] = {
				"min": price_stats[0].get("min_price", 0),
				"max": price_stats[0].get("max_price", 0),
				"average": round(price_stats[0].get("avg_price", 0), 2) if price_stats[0].get("avg_price") else 0
			}
		
		return stats
		
	except Exception as e:
		frappe.log_error(f"Error in get_package_stats: {str(e)}")
		frappe.throw(_("Failed to fetch package statistics: {0}").format(str(e)))


@frappe.whitelist()
def duplicate_package(name, new_package_code=None):
	"""
	Duplicate an existing package with a new code
	
	Args:
		name (str): Source package ID
		new_package_code (str): Code for the new package (optional)
		
	Returns:
		dict: New package document
	"""
	try:
		if not frappe.db.exists("Standard Package", name):
			frappe.throw(_("Source package not found"))
		
		source_doc = frappe.get_doc("Standard Package", name)
		
		# Generate new package code if not provided
		if not new_package_code:
			new_package_code = f"{source_doc.package_code}_COPY"
			counter = 1
			while frappe.db.exists("Standard Package", {"package_code": new_package_code}):
				new_package_code = f"{source_doc.package_code}_COPY{counter}"
				counter += 1
		
		# Check if new code already exists
		if frappe.db.exists("Standard Package", {"package_code": new_package_code}):
			frappe.throw(_("Package Code '{0}' already exists").format(new_package_code))
		
		# Create new document with copied data
		new_doc = frappe.copy_doc(source_doc)
		new_doc.package_code = new_package_code
		new_doc.package_name = f"{source_doc.package_name} (Copy)"
		new_doc.status = "Draft"  # Always set duplicated packages as Draft
		
		new_doc.insert()
		frappe.db.commit()
		
		return new_doc.as_dict()
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in duplicate_package: {str(e)}")
		frappe.throw(_("Failed to duplicate package: {0}").format(str(e)))