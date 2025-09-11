import frappe
from frappe import _


@frappe.whitelist()
def export_data(doctype=None, export_fields=None, filters=None, file_type="CSV"):
	"""Export leads data using Frappe's built-in export functionality"""
	from frappe.core.doctype.data_import.exporter import Exporter
	
	# Default to CRM Lead doctype
	if not doctype:
		doctype = "CRM Lead"
	
	# Default export fields for leads
	if not export_fields:
		export_fields = {
			"CRM Lead": [
				"name", "lead_name", "first_name", "last_name", 
				"email", "mobile_no", "status", "source", "service_type",
				"priority", "lead_owner", "notes",
				"trip_name", "destinations", "source_city", "start_date", "end_date",
				"budget_per_head", "passenger_adults", "passenger_children", "passenger_infants",
				"hotel_star_rating", "number_of_rooms", "activity_preferences", "tags",
				"creation", "modified"
			]
		}
	
	# Create exporter instance
	exporter = Exporter(
		doctype=doctype,
		export_fields=export_fields,
		export_data=True,
		export_filters=filters,
		file_type=file_type
	)
	
	# Build and return the response
	exporter.build_response()
	return True


# Alias for backward compatibility
@frappe.whitelist()
def export(doctype=None, export_fields=None, filters=None, file_type="CSV"):
	"""Alias for export_data function"""
	return export_data(doctype, export_fields, filters, file_type)


@frappe.whitelist()
def upload_and_preview(file_content=None):
	"""Upload and preview leads import file"""
	import csv
	import io
	import json
	
	# This is a placeholder - in real implementation, you'd handle file upload
	# and parse CSV/Excel to return preview data
	
	return {
		"columns": ["lead_name", "first_name", "last_name", "email", "mobile_no", "status", "source"],
		"rows": [
			{"lead_name": "John Doe", "first_name": "John", "last_name": "Doe", "email": "john@example.com", "mobile_no": "+1234567890", "status": "Open", "source": "Website"},
			{"lead_name": "Jane Smith", "first_name": "Jane", "last_name": "Smith", "email": "jane@example.com", "mobile_no": "+0987654321", "status": "New", "source": "Referral"}
		],
		"file_path": "/tmp/uploaded_file.csv"
	}


@frappe.whitelist()
def start_import(file_path, field_mapping, import_type="Insert New Records"):
	"""Start leads import process"""
	from frappe.core.doctype.data_import.data_import import import_file
	
	# Create a data import document
	data_import = frappe.new_doc("Data Import")
	data_import.reference_doctype = "CRM Lead"
	data_import.import_file = file_path
	data_import.import_type = import_type
	
	if field_mapping:
		data_import.template_options = frappe.as_json(field_mapping)
	
	data_import.save()
	
	# Start the import process
	data_import.start_import()
	
	return {"name": data_import.name}


@frappe.whitelist()
def bulk_actions(action, names, **kwargs):
	"""Handle bulk actions for leads"""
	if not isinstance(names, list):
		names = frappe.parse_json(names) if isinstance(names, str) else [names]
	
	if action == "delete":
		for name in names:
			if frappe.has_permission("CRM Lead", "delete", name):
				frappe.delete_doc("CRM Lead", name)
		return {"message": _("Selected leads deleted successfully")}
	
	elif action == "update_status":
		status = kwargs.get("status")
		if not status:
			frappe.throw(_("Status is required"))
		
		for name in names:
			if frappe.has_permission("CRM Lead", "write", name):
				lead = frappe.get_doc("CRM Lead", name)
				lead.status = status
				lead.save()
		
		return {"message": _("Status updated for selected leads")}
	
	else:
		frappe.throw(_("Invalid action: {0}").format(action))