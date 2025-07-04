import frappe

def sync_lead_to_contact(doc, method):
	"""Global handler to sync lead changes to contact - called from hooks.py"""
	frappe.logger().info(f"🌐 Global sync handler called for lead {doc.name} via {method}")
	
	# Check if this is a relevant field change
	if method == "on_update":
		# For direct database updates, we need to check differently
		sync_fields = ["email", "mobile_no", "first_name", "last_name", "gender", "instagram"]
		
		# Since we can't use has_value_changed() in global handlers,
		# we'll always attempt sync and let the sync function handle it
		frappe.logger().info(f"🔄 Attempting to sync lead {doc.name} to contact")
		
		try:
			# Call the sync method from the document
			if hasattr(doc, 'sync_contact_on_lead_update'):
				doc.sync_contact_on_lead_update()
			else:
				# Fallback: call sync logic directly
				sync_lead_contact_direct(doc)
		except Exception as e:
			frappe.logger().error(f"❌ Error in global sync handler: {str(e)}")
			frappe.log_error(f"Global lead sync failed for {doc.name}: {str(e)}")

def sync_lead_contact_direct(lead_doc):
	"""Direct sync logic for when document methods aren't available"""
	frappe.logger().info(f"📋 Direct sync for lead {lead_doc.name}")
	
	# Find associated contact
	contact = get_associated_contact_direct(lead_doc)
	if not contact:
		frappe.logger().info("❌ No associated contact found for direct sync")
		return
	
	try:
		frappe.logger().info(f"📋 Loading contact document: {contact}")
		contact_doc = frappe.get_doc("Contact", contact)
		
		# Update basic fields (since we can't detect changes, update all)
		contact_doc.first_name = lead_doc.first_name or lead_doc.lead_name
		contact_doc.last_name = lead_doc.last_name
		contact_doc.gender = lead_doc.gender
		
		# Update contact email
		if lead_doc.email:
			update_contact_email_direct(contact_doc, lead_doc.email)
		
		# Update contact mobile
		if lead_doc.mobile_no:
			update_contact_mobile_direct(contact_doc, lead_doc.mobile_no)
		
		# Update instagram (if field exists)
		if hasattr(lead_doc, 'instagram') and lead_doc.instagram:
			if hasattr(contact_doc, 'instagram'):
				contact_doc.instagram = lead_doc.instagram
		
		# Save the contact
		frappe.logger().info(f"💾 Saving contact {contact}")
		contact_doc.save(ignore_permissions=True)
		frappe.logger().info(f"✅ Contact {contact} synced successfully via global handler")
		
	except Exception as e:
		frappe.logger().error(f"❌ Error in direct sync: {str(e)}")
		raise

def get_associated_contact_direct(lead_doc):
	"""Find contact associated with lead - direct version"""
	frappe.logger().info(f"🔎 Looking for contact for lead {lead_doc.name}")
	
	# Find by email
	if lead_doc.email:
		email_contact = frappe.db.get_value("Contact Email", {"email_id": lead_doc.email}, "parent")
		frappe.logger().info(f"📧 Email search result: {email_contact}")
		if email_contact:
			return email_contact
	
	# Find by mobile
	if lead_doc.mobile_no:
		mobile_contact = frappe.db.get_value("Contact Phone", {"phone": lead_doc.mobile_no}, "parent")
		frappe.logger().info(f"📱 Mobile search result: {mobile_contact}")
		if mobile_contact:
			return mobile_contact
	
	# Find by Instagram
	if hasattr(lead_doc, 'instagram') and lead_doc.instagram:
		instagram_contact = frappe.db.get_value("Contact", {"instagram": lead_doc.instagram}, "name")
		frappe.logger().info(f"📷 Instagram search result: {instagram_contact}")
		if instagram_contact:
			return instagram_contact
	
	frappe.logger().info("❌ No contact found via direct search")
	return None

def update_contact_email_direct(contact_doc, new_email):
	"""Update contact email - direct version"""
	frappe.logger().info(f"📧 Updating contact email to: {new_email}")
	
	# Check if email already exists
	existing_email = None
	for email_row in contact_doc.email_ids:
		if email_row.email_id == new_email:
			existing_email = email_row
			break
	
	if not existing_email:
		# Add new email
		frappe.logger().info(f"➕ Adding new email: {new_email}")
		contact_doc.append("email_ids", {
			"email_id": new_email,
			"is_primary": 1 if not any(e.get("is_primary") for e in contact_doc.email_ids) else 0
		})

def update_contact_mobile_direct(contact_doc, new_mobile):
	"""Update contact mobile - direct version"""
	frappe.logger().info(f"📱 Updating contact mobile to: {new_mobile}")
	
	# Check if mobile already exists
	existing_mobile = None
	for phone_row in contact_doc.phone_nos:
		if phone_row.phone == new_mobile:
			existing_mobile = phone_row
			break
	
	if not existing_mobile:
		# Add new mobile
		frappe.logger().info(f"➕ Adding new mobile: {new_mobile}")
		contact_doc.append("phone_nos", {
			"phone": new_mobile,
			"is_primary_mobile_no": 1 if not any(p.get("is_primary_mobile_no") for p in contact_doc.phone_nos) else 0
		}) 