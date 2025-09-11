import frappe

from crm.api.doc import get_assigned_users, get_fields_meta
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def get_lead(name):
	lead = frappe.get_doc("CRM Lead", name)
	lead.check_permission("read")

	lead = lead.as_dict()

	# Parse tags for frontend convenience 
	if lead.get("_user_tags"):
		lead["tags_parsed"] = [tag.strip() for tag in lead["_user_tags"].split(",") if tag.strip()]
	else:
		lead["tags_parsed"] = []

	lead["fields_meta"] = get_fields_meta("CRM Lead")
	lead["_form_script"] = get_form_script("CRM Lead")
	
	# Auto-include Trip data for this lead with ALL fields
	trip_names = frappe.get_all(
		"Trip",
		filters={"lead": name},
		fields=["name"]
	)
	
	# Get complete Trip documents with all fields
	trips_data = []
	for trip_info in trip_names:
		trip_doc = frappe.get_doc("Trip", trip_info.get("name"))
		trips_data.append(trip_doc.as_dict())
	
	lead["trips"] = trips_data
	
	return lead
