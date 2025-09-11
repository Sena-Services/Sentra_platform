import frappe
from frappe import _
from frappe.utils import flt
import json


@frappe.whitelist()
def get_list(doctype="CRM Lead", fields=None, filters=None, order_by=None, 
             limit_start=0, limit_page_length=20, parent_doctype=None, debug=False):
	"""Get list of leads with linked requirement data using manual joins (same as get_leads_with_requirements)"""
	
	# Parse fields if it's a string
	if isinstance(fields, str):
		fields = json.loads(fields)
	
	# Parse filters if it's a string
	if isinstance(filters, str):
		filters = json.loads(filters) if filters else {}
	
	# Default fields if not specified
	if not fields:
		fields = [
			"name", "lead_name", "first_name", "last_name", "email", 
			"mobile_no", "status", "source", "priority", "lead_owner",
			"creation", "modified"
		]
	
	# Check if any field or filter involves requirements
	has_requirement_fields = any(f.startswith("requirement.") for f in fields)
	has_requirement_filters = filters and any(k.startswith("requirement.") for k in filters.keys())
	
	# If no requirement fields/filters, use simple frappe.get_all for better performance
	if not has_requirement_fields and not has_requirement_filters:
		return frappe.get_all(
			doctype,
			fields=fields,
			filters=filters,
			order_by=order_by or "modified desc",
			start=limit_start,
			page_length=limit_page_length,
			parent_doctype=parent_doctype,
			debug=debug
		)
	
	# Otherwise, use the internal join function
	return _get_leads_with_joins(
		fields=fields,
		filters=filters,
		order_by=order_by,
		limit_start=limit_start,
		limit_page_length=limit_page_length
	)


@frappe.whitelist()
def get_view(name, fields=None):
	"""Get single lead with all linked requirement data"""
	
	# Parse fields if it's a string
	if isinstance(fields, str):
		fields = json.loads(fields)
	
	# Get the lead document with specified fields
	lead_fields = fields.get("lead", ["*"]) if fields else ["*"]
	lead = frappe.get_doc("CRM Lead", name).as_dict()
	
	# Get linked requirements with their child tables
	requirement_fields = fields.get("requirement", ["*"]) if fields else ["*"]
	
	# Add child table fields using dot notation
	if "destination_city" not in requirement_fields:
		requirement_fields.extend([
			"destination_city.destination",
			"destination_city.nights",
			"destination_city.sequence"
		])
	if "passenger_details" not in requirement_fields:
		requirement_fields.extend([
			"passenger_details.passenger_type",
			"passenger_details.age"
		])
	if "activity" not in requirement_fields:
		requirement_fields.extend([
			"activity.activity"
		])
	
	# Get requirements with child data using frappe.get_all
	requirements = frappe.get_all(
		"Requirement",
		filters={"lead": name},
		fields=requirement_fields
	)
	
	# Group child table data by parent requirement
	requirements_dict = {}
	for row in requirements:
		req_name = row.get("name")
		if req_name not in requirements_dict:
			requirements_dict[req_name] = {
				"name": req_name,
				"destination_city": [],
				"passenger_details": [],
				"activity": []
			}
		
		# Copy parent fields
		for key, value in row.items():
			if "." not in key and key not in ["destination_city", "passenger_details", "activity"]:
				requirements_dict[req_name][key] = value
		
		# Handle child table data
		for child_table in ["destination_city", "passenger_details", "activity"]:
			child_data = {}
			for key, value in row.items():
				if key.startswith(f"{child_table}."):
					field_name = key.split(".", 1)[1]
					child_data[field_name] = value
			
			if child_data and any(v is not None for v in child_data.values()):
				requirements_dict[req_name][child_table].append(child_data)
	
	lead["requirements"] = list(requirements_dict.values())
	
	# Add comment and like counts
	try:
		lead["_comment_count"] = frappe.db.count("Comment", {
			"reference_doctype": "CRM Lead",
			"reference_name": name
		})
	except:
		lead["_comment_count"] = 0
	
	try:
		lead["_like_count"] = frappe.db.count("Like Log", {
			"reference_doctype": "CRM Lead",
			"reference_name": name
		})
	except:
		lead["_like_count"] = 0
	
	return lead


@frappe.whitelist()
def create(doc=None, with_requirement=False, requirement_data=None):
	"""Create lead with optional requirement"""
	if isinstance(doc, str):
		doc = json.loads(doc)
	
	if isinstance(requirement_data, str):
		requirement_data = json.loads(requirement_data)
	
	# Create the lead (fetch rules will automatically populate fields from contact)
	lead = frappe.get_doc(doc)
	lead.insert()
	
	# Create requirement if requested
	if with_requirement and requirement_data:
		requirement_data["lead"] = lead.name
		requirement_data["doctype"] = "Requirement"
		req = frappe.get_doc(requirement_data)
		req.insert()
		
		# Return lead with requirement
		return get_view(lead.name)
	
	return lead.as_dict()


@frappe.whitelist()
def update(name, doc=None, update_requirement=False, requirement_data=None):
	"""Update lead and optionally its requirement"""
	if isinstance(doc, str):
		doc = json.loads(doc)
	
	if isinstance(requirement_data, str):
		requirement_data = json.loads(requirement_data)
	
	# Update the lead (fetch rules will update fields from contact if link_to_contact changes)
	lead = frappe.get_doc("CRM Lead", name)
	for key, value in doc.items():
		if key not in ["name", "doctype", "requirements"]:
			setattr(lead, key, value)
	lead.save()
	
	# Update requirement if requested
	if update_requirement and requirement_data:
		req_name = requirement_data.get("name")
		if req_name:
			req = frappe.get_doc("Requirement", req_name)
			for key, value in requirement_data.items():
				if key not in ["name", "doctype", "lead"]:
					setattr(req, key, value)
			req.save()
	
	return get_view(name)


@frappe.whitelist()
def delete(names):
	"""Delete leads and their linked requirements"""
	if isinstance(names, str):
		names = json.loads(names) if "[" in names else [names]
	
	deleted = []
	for name in names:
		# Delete linked requirements first
		requirements = frappe.get_all("Requirement", filters={"lead": name}, pluck="name")
		for req in requirements:
			frappe.delete_doc("Requirement", req)
		
		# Delete the lead
		frappe.delete_doc("CRM Lead", name)
		deleted.append(name)
	
	return {"deleted": deleted}


@frappe.whitelist()
def bulk_action(action, names, **kwargs):
	"""Handle bulk actions for leads"""
	if isinstance(names, str):
		names = json.loads(names)
	
	results = {"success": [], "failed": []}
	
	if action == "delete":
		return delete(names)
	
	elif action == "update_status":
		status = kwargs.get("status")
		if not status:
			frappe.throw(_("Status is required"))
		
		for name in names:
			try:
				lead = frappe.get_doc("CRM Lead", name)
				lead.status = status
				lead.save()
				results["success"].append(name)
			except Exception as e:
				results["failed"].append({"name": name, "error": str(e)})
		
		return results
	
	elif action == "assign_owner":
		owner = kwargs.get("owner")
		if not owner:
			frappe.throw(_("Owner is required"))
		
		for name in names:
			try:
				lead = frappe.get_doc("CRM Lead", name)
				lead.lead_owner = owner
				lead.save()
				results["success"].append(name)
			except Exception as e:
				results["failed"].append({"name": name, "error": str(e)})
		
		return results
	
	elif action == "update_priority":
		priority = kwargs.get("priority")
		if not priority:
			frappe.throw(_("Priority is required"))
		
		for name in names:
			try:
				lead = frappe.get_doc("CRM Lead", name)
				lead.priority = priority
				lead.save()
				results["success"].append(name)
			except Exception as e:
				results["failed"].append({"name": name, "error": str(e)})
		
		return results
	
	else:
		frappe.throw(_("Invalid action: {0}").format(action))


@frappe.whitelist()
def export(fields=None, filters=None, file_type="CSV"):
	"""Export leads with requirement data"""
	from frappe.desk.reportview import export_query
	
	# Parse parameters
	if isinstance(fields, str):
		fields = json.loads(fields)
	if isinstance(filters, str):
		filters = json.loads(filters) if filters else {}
	
	# Get all data without pagination
	data = get_list(
		fields=fields,
		filters=filters,
		limit_page_length=None
	)
	
	# Use Frappe's built-in export
	return export_query(
		doctype="CRM Lead",
		file_format_type=file_type,
		filters=filters,
		fields=fields,
		with_data=True
	)


@frappe.whitelist()
def import_data(file_url=None, data=None, import_type="Insert New Records"):
	"""Import leads with requirements"""
	from frappe.core.doctype.data_import.data_import import DataImport
	
	# Create data import record
	data_import = frappe.new_doc("Data Import")
	data_import.reference_doctype = "CRM Lead"
	data_import.import_type = import_type
	
	if file_url:
		data_import.import_file = file_url
	elif data:
		# Handle direct data import
		import csv
		import io
		
		# Write data to temporary file
		output = io.StringIO()
		writer = csv.DictWriter(output, fieldnames=data[0].keys())
		writer.writeheader()
		writer.writerows(data)
		
		# Save temporary file
		from frappe.utils.file_manager import save_file
		file_doc = save_file("import_data.csv", output.getvalue(), "Data Import", data_import.name)
		data_import.import_file = file_doc.file_url
	
	data_import.save()
	
	# Start import
	data_import.start_import()
	
	return {
		"name": data_import.name,
		"status": data_import.status,
		"total_rows": data_import.total_rows,
		"success_count": data_import.success_count,
		"failed_count": data_import.failed_count
	}


@frappe.whitelist()
def get_count(filters=None):
	"""Get count of leads matching filters"""
	if isinstance(filters, str):
		filters = json.loads(filters) if filters else {}
	
	count = frappe.db.count("CRM Lead", filters=filters)
	
	# Get counts by status
	status_counts = frappe.db.sql("""
		SELECT status, COUNT(*) as count
		FROM `tabCRM Lead`
		WHERE {conditions}
		GROUP BY status
	""".format(
		conditions=" AND ".join([f"{k} = %({k})s" for k in filters.keys()]) if filters else "1=1"
	), filters, as_dict=True)
	
	return {
		"total": count,
		"by_status": {row.status: row.count for row in status_counts}
	}


@frappe.whitelist()
def get_stats(filters=None):
	"""Get statistics for leads"""
	if isinstance(filters, str):
		filters = json.loads(filters) if filters else {}
	
	# Base stats
	stats = {
		"total_leads": frappe.db.count("CRM Lead", filters=filters),
		"total_requirements": 0,
		"avg_budget": 0,
		"by_status": {},
		"by_priority": {},
		"by_source": {},
		"by_service_type": {},
		"conversion_rate": 0
	}
	
	# Get leads matching filters
	lead_names = frappe.get_all("CRM Lead", filters=filters, pluck="name")
	
	if lead_names:
		# Count requirements
		stats["total_requirements"] = frappe.db.count(
			"Requirement", 
			filters={"lead": ["in", lead_names]}
		)
		
		# Average budget from requirements
		avg_budget = frappe.db.sql("""
			SELECT AVG(budget) as avg_budget
			FROM `tabRequirement`
			WHERE lead IN %s AND budget > 0
		""", [lead_names], as_dict=True)
		
		if avg_budget and avg_budget[0].avg_budget:
			stats["avg_budget"] = flt(avg_budget[0].avg_budget, 2)
		
		# Group by various fields
		for field in ["status", "priority", "source"]:
			field_counts = frappe.db.sql("""
				SELECT {field}, COUNT(*) as count
				FROM `tabCRM Lead`
				WHERE name IN %s
				GROUP BY {field}
			""".format(field=field), [lead_names], as_dict=True)
			
			stats[f"by_{field}"] = {row[field]: row.count for row in field_counts if row[field]}
		
		# Service type stats (from child table)
		service_counts = frappe.db.sql("""
			SELECT lst.service_type, COUNT(DISTINCT lst.parent) as count
			FROM `tabLead Service Type` lst
			WHERE lst.parent IN %s
			GROUP BY lst.service_type
		""", [lead_names], as_dict=True)
		
		stats["by_service_type"] = {row.service_type: row.count for row in service_counts}
		
		# Conversion rate (converted leads / total leads)
		converted_count = frappe.db.count(
			"CRM Lead", 
			filters={"name": ["in", lead_names], "status": "Converted"}
		)
		stats["conversion_rate"] = round((converted_count / stats["total_leads"]) * 100, 2) if stats["total_leads"] > 0 else 0
	
	return stats


def _get_leads_with_joins(fields=None, filters=None, order_by=None, 
                         limit_start=0, limit_page_length=20):
	"""
	Internal function to get leads with their linked requirements using manual joins.
	Used by get_list when requirement fields/filters are detected.
	"""
	
	if isinstance(fields, str):
		fields = json.loads(fields)
	
	if isinstance(filters, str):
		filters = json.loads(filters) if filters else {}
	
	# Default fields if not specified
	if not fields:
		fields = ["name", "lead_name", "status", "email", "mobile_no"]
	
	# Separate lead fields and requirement fields
	lead_fields = []
	requirement_fields = []
	
	for field in fields:
		if field.startswith("requirement."):
			req_field = field.replace("requirement.", "")
			requirement_fields.append(f"r.{req_field} as `requirement.{req_field}`")
		else:
			lead_fields.append(f"l.{field}")
	
	# Build the query
	select_fields = lead_fields + requirement_fields
	
	query = f"""
		SELECT 
			{', '.join(select_fields)}
		FROM `tabCRM Lead` l
		LEFT JOIN `tabRequirement` r ON r.lead = l.name
	"""
	
	# Add filters
	conditions = []
	values = []
	
	if filters:
		for key, value in filters.items():
			# Determine table alias (l for lead, r for requirement)
			if key.startswith("requirement."):
				table_alias = "r"
				field_name = key.replace("requirement.", "")
			else:
				table_alias = "l"
				field_name = key
			
			if isinstance(value, list) and len(value) == 2 and value[0] in ["=", "!=", ">", "<", ">=", "<=", "like", "not like", "in", "not in"]:
				operator = value[0]
				val = value[1]
				if operator in ["in", "not in"]:
					if isinstance(val, list):
						placeholders = ', '.join(['%s'] * len(val))
						conditions.append(f"{table_alias}.{field_name} {operator} ({placeholders})")
						values.extend(val)
					else:
						conditions.append(f"{table_alias}.{field_name} {operator} (%s)")
						values.append(val)
				else:
					conditions.append(f"{table_alias}.{field_name} {operator} %s")
					values.append(val)
			elif isinstance(value, list):
				placeholders = ', '.join(['%s'] * len(value))
				conditions.append(f"{table_alias}.{field_name} IN ({placeholders})")
				values.extend(value)
			else:
				conditions.append(f"{table_alias}.{field_name} = %s")
				values.append(value)
	
	if conditions:
		query += f" WHERE {' AND '.join(conditions)}"
	
	# Add order by
	if order_by:
		query += f" ORDER BY {order_by}"
	else:
		query += " ORDER BY l.modified DESC"
	
	# Add limit
	query += f" LIMIT {limit_start}, {limit_page_length}"
	
	# Execute query
	results = frappe.db.sql(query, values, as_dict=True)
	
	return results