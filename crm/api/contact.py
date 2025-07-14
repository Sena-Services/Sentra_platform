import frappe
from frappe import _


def validate(doc, method):
	update_deals_email_mobile_no(doc)

def update_leads_from_contact(doc, method):
    """
    Called when a Contact is updated.
    Updates fetched fields in all linked Leads.
    """
  


    lead_meta = frappe.get_meta("CRM Lead")
    fetched_fields_map = {}
    
    # Method 1: Look for fields that have "fetch_from" property pointing to Contact
    for field in lead_meta.fields:
        if hasattr(field, 'fetch_from') and field.fetch_from:
            # Parse fetch_from syntax: "link_field.target_field"
            if '.' in field.fetch_from:
                link_field, target_field = field.fetch_from.split('.', 1)
                # Check if the link field points to Contact
                link_field_meta = lead_meta.get_field(link_field)
                if link_field_meta and link_field_meta.options == "Contact":
                    fetched_fields_map[target_field] = field.fieldname
    
    # Method 2: Fallback to common field mappings if no fetch_from fields found
    if not fetched_fields_map:
        # Common field mappings between Contact and Lead
        contact_meta = frappe.get_meta("Contact")
        common_fields = []
        
        for contact_field in contact_meta.fields:
            lead_field = lead_meta.get_field(contact_field.fieldname)
            if lead_field:
                common_fields.append((contact_field.fieldname, contact_field.fieldname))
        
     
        
        fetched_fields_map = dict(common_fields)

    # Find all Lead documents where 'link_to_contact' field is this Contact
    leads_to_update = frappe.get_all(
        "CRM Lead",
        filters={"link_to_contact": doc.name},
        fields=["name"] # We only need the name to load the document
    )

    


    for lead_data in leads_to_update:
        lead_name = lead_data.name
        try:
            lead_doc = frappe.get_doc("CRM Lead", lead_name)

            # Check if any field value has actually changed to avoid unnecessary saves
            changed = False
            for contact_field, lead_field in fetched_fields_map.items():
                new_value = doc.get(contact_field) # Value from the updated Contact
                current_lead_value = lead_doc.get(lead_field) # Current value in the Lead

                if new_value != current_lead_value:
                    lead_doc.set(lead_field, new_value)
                    changed = True
                    
            if changed:
                lead_doc.save(ignore_permissions=True) # Save the updated Lead
                frappe.db.commit() # Commit changes for this lead

        except Exception as e:
            frappe.log_error(f"Error updating Lead {lead_name} for Contact {doc.name}: {e}", "Lead Update Hook Error")
            frappe.db.rollback() # Rollback if an error occurs for this specific lead


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.get_cached_doc("CRM Deal", linked_deal.parent)
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			deal.email = doc.email_id
			deal.mobile_no = doc.mobile_no
			deal.save(ignore_permissions=True)


@frappe.whitelist()
def get_contact(name):
	contact = frappe.get_doc("Contact", name)
	contact.check_permission("read")

	contact = contact.as_dict()

	if not len(contact):
		frappe.throw(_("Contact not found"), frappe.DoesNotExistError)

	return contact


@frappe.whitelist()
def get_linked_deals(contact):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	deal_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "CRM Deal"},
		fields=["parent"],
		distinct=True,
	)

	# get deals data
	deals = []
	for d in deal_names:
		deal = frappe.get_cached_doc(
			"CRM Deal",
			d.parent,
			fields=[
				"name",
				"organization",
				"currency",
				"annual_revenue",
				"status",
				"email",
				"mobile_no",
				"deal_owner",
				"modified",
			],
		)
		deals.append(deal.as_dict())

	return deals


@frappe.whitelist()
def create_new(contact, field, value):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact.phone_nos) == 0 else 0}
		contact.append("phone_nos", mobile_no)
	else:
		frappe.throw("Invalid field")

	contact.save()
	return True


@frappe.whitelist()
def set_as_primary(contact, field, value):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw("Invalid field")

	contact.save()
	return True


@frappe.whitelist()
def search_emails(txt: str):
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results


@frappe.whitelist()
def export_data(doctype=None, export_fields=None, filters=None, file_type="CSV"):
	"""Export contacts data using Frappe's built-in export functionality"""
	from frappe.core.doctype.data_import.exporter import Exporter
	
	# Default to Contact doctype
	if not doctype:
		doctype = "Contact"
	
	# Default export fields for contacts
	if not export_fields:
		export_fields = {
			"Contact": [
				"name", "full_name", "first_name", "last_name", 
				"email_id", "mobile_no",
				"designation", "address_line1", "address_line2", "city", "state", "country",
				"pincode", "contact_type", "contact_category", "notes", "gender",
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
