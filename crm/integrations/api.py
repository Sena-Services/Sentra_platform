import frappe
from frappe.query_builder import Order
from pypika.functions import Replace

from crm.utils import are_same_phone_number, parse_phone_number


@frappe.whitelist()
def is_call_integration_enabled():
	twilio_enabled = frappe.db.get_single_value("CRM Twilio Settings", "enabled")
	exotel_enabled = frappe.db.get_single_value("CRM Exotel Settings", "enabled")

	return {
		"twilio_enabled": twilio_enabled,
		"exotel_enabled": exotel_enabled,
		"default_calling_medium": get_user_default_calling_medium(),
	}


def get_user_default_calling_medium():
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		return None

	default_medium = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "default_medium")

	if not default_medium:
		return None

	return default_medium


@frappe.whitelist()
def set_default_calling_medium(medium):
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"agent": frappe.session.user,
				"default_medium": medium,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("CRM Telephony Agent", frappe.session.user, "default_medium", medium)

	return get_user_default_calling_medium()


@frappe.whitelist()
def add_note_to_call_log(call_sid, note):
	"""Add/Update note to call log based on call sid."""
	_note = None
	if not note.get("name"):
		_note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": note.get("title", "Call Note"),
				"content": note.get("content"),
			}
		).insert(ignore_permissions=True)
	else:
		_note = frappe.set_value("FCRM Note", note.get("name"), "content", note.get("content"))

	call_log = frappe.get_cached_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("FCRM Note", _note.name)
	call_log.save(ignore_permissions=True)

	return _note


@frappe.whitelist()
def add_task_to_call_log(call_sid, task):
	"""Add/Update task to call log based on call sid."""
	_task = None
	if not task.get("name"):
		_task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		).insert(ignore_permissions=True)
	else:
		_task = frappe.get_doc("CRM Task", task.get("name"))
		_task.update(
			{
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		)
		_task.save(ignore_permissions=True)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("CRM Task", _task.name)
	call_log.save(ignore_permissions=True)

	return _task


@frappe.whitelist()
def get_contact_by_phone_number(phone_number):
	"""Get contact by phone number."""
	number = parse_phone_number(phone_number)

	if number.get("is_valid"):
		return get_contact(number.get("national_number"), number.get("country"))
	else:
		return get_contact(phone_number, number.get("country"), exact_match=True)


def get_contact(phone_number, country="IN", exact_match=False):
	if not phone_number:
		return {"mobile_no": phone_number}

	cleaned_number = (
		phone_number.strip()
		.replace(" ", "")
		.replace("-", "")
		.replace("(", "")
		.replace(")", "")
		.replace("+", "")
	)

	# Check if the number is associated with a contact
	Contact = frappe.qb.DocType("Contact")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Contact.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Contact)
		.select(Contact.name, Contact.full_name, Contact.image, Contact.mobile_no)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	contacts = query.run(as_dict=True)

	if len(contacts):
		# Check if the contact is associated with a deal
		for contact in contacts:
			if frappe.db.exists("CRM Contacts", {"contact": contact.name, "is_primary": 1}):
				deal = frappe.db.get_value(
					"CRM Contacts", {"contact": contact.name, "is_primary": 1}, "parent"
				)
				if are_same_phone_number(contact.mobile_no, phone_number, country, validate=not exact_match):
					contact["deal"] = deal
					return contact
		# Else, return the first contact
		if are_same_phone_number(contacts[0].mobile_no, phone_number, country, validate=not exact_match):
			return contacts[0]

	# Else, Check if the number is associated with a lead
	Lead = frappe.qb.DocType("CRM Lead")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Lead.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Lead)
		.select(Lead.name, Lead.lead_name, Lead.image, Lead.mobile_no)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	leads = query.run(as_dict=True)

	if len(leads):
		for lead in leads:
			if are_same_phone_number(lead.mobile_no, phone_number, country, validate=not exact_match):
				lead["lead"] = lead.name
				lead["full_name"] = lead.lead_name
				return lead

	return {"mobile_no": phone_number}


@frappe.whitelist()
def get_whatsapp_messages(contact_id):
	"""Get WhatsApp messages for a specific contact from Communication doctype."""
	if not contact_id:
		return []

	try:
		# Get the Communication record for this contact and WhatsApp medium
		communications = frappe.get_all(
			"Communication",
			fields=["name", "content", "communication_date", "sender_full_name", "sent_or_received"],
			filters={
				"reference_doctype": "Contact",
				"reference_name": contact_id,
				"communication_medium": "WhatsApp",
				"communication_type": "Communication"
			},
			order_by="communication_date desc",
			limit=1
		)
		
		if not communications:
			return []
			
		communication = communications[0]
		
		if not communication.content:
			return []
			
		# Parse the HTML content to extract individual messages
		messages = []
		
		import re
		from bs4 import BeautifulSoup
		
		soup = BeautifulSoup(communication.content, 'html.parser')
		message_entries = soup.find_all('div', class_='message-entry')
		
		for entry in message_entries:
			sender_element = entry.find('strong')
			timestamp_element = entry.find('span')
			content_element = entry.find('div', style=lambda value: value and 'margin-top' in value)
			
			if sender_element and content_element:
				sender_name = sender_element.get_text(strip=True)
				timestamp = timestamp_element.get_text(strip=True) if timestamp_element else ''
				content = content_element.get_text(strip=True)
				
				# Determine if it's incoming or outgoing based on arrow direction and sender
				entry_html = str(entry)
				is_outgoing = '←' in entry_html or sender_name == 'You'
				
				# Convert timestamp to JavaScript Date format if possible
				message_time = None
				if timestamp:
					try:
						# Try to parse various timestamp formats
						from dateutil import parser as date_parser
						parsed_time = date_parser.parse(timestamp)
						message_time = parsed_time.isoformat()
					except:
						# If parsing fails, try to extract time from common formats like "Jan 07, 2025 11:01 AM"
						import re
						time_match = re.search(r'(\d{1,2}:\d{2}\s*(AM|PM|am|pm))', timestamp)
						if time_match:
							try:
								from datetime import datetime
								time_str = time_match.group(1)
								# Create a date object for today with the extracted time
								today = datetime.now().date()
								parsed_time = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %I:%M %p")
								message_time = parsed_time.isoformat()
							except:
								pass
				
				if not message_time:
					# Fallback to current time if no valid timestamp
					from datetime import datetime
					message_time = datetime.now().isoformat()
				
				messages.append({
					'sender': 'user' if is_outgoing else 'contact',
					'text': content,
					'time': message_time,
					'sender_name': sender_name,
				})
		
		return messages
		
	except Exception as e:
		frappe.log_error(f"Error fetching WhatsApp messages for contact {contact_id}: {str(e)}")
		return []


@frappe.whitelist()
def get_whatsapp_contacts_by_activity():
	"""Get contacts sorted by latest WhatsApp message activity."""
	try:
		# Get all contacts with mobile numbers and their latest WhatsApp communication date
		contacts_with_activity = frappe.db.sql("""
			SELECT 
				c.name,
				c.full_name,
				c.first_name,
				c.last_name,
				c.mobile_no,
				c.image,
				COALESCE(comm.latest_communication_date, c.modified) as last_activity
			FROM `tabContact` c
			LEFT JOIN (
				SELECT 
					reference_name,
					MAX(communication_date) as latest_communication_date
				FROM `tabCommunication`
				WHERE reference_doctype = 'Contact'
					AND communication_medium = 'WhatsApp'
					AND communication_type = 'Communication'
				GROUP BY reference_name
			) comm ON c.name = comm.reference_name
			WHERE c.mobile_no IS NOT NULL 
				AND c.mobile_no != ''
			ORDER BY last_activity DESC
			LIMIT 1000
		""", as_dict=True)
		
		return contacts_with_activity
		
	except Exception as e:
		frappe.log_error(f"Error fetching WhatsApp contacts by activity: {str(e)}")
		return []


@frappe.whitelist()
def get_instagram_messages(contact_id):
	"""Get Instagram messages for a specific contact from Communication doctype."""
	if not contact_id:
		return []

	try:
		# Get the Communication record for this contact and Instagram medium
		communications = frappe.get_all(
			"Communication",
			fields=["name", "content", "communication_date", "sender_full_name", "sent_or_received"],
			filters={
				"reference_doctype": "Contact",
				"reference_name": contact_id,
				"communication_medium": "Instagram",
				"communication_type": "Communication"
			},
			order_by="communication_date desc",
			limit=1
		)
		
		if not communications:
			return []
			
		communication = communications[0]
		
		if not communication.content:
			return []
			
		# Parse the HTML content to extract individual messages
		messages = []
		
		import re
		from bs4 import BeautifulSoup
		
		soup = BeautifulSoup(communication.content, 'html.parser')
		message_entries = soup.find_all('div', class_='message-entry')
		
		for entry in message_entries:
			sender_element = entry.find('strong')
			timestamp_element = entry.find('span')
			content_element = entry.find('div', style=lambda value: value and 'margin-top' in value)
			
			if sender_element and content_element:
				sender_name = sender_element.get_text(strip=True)
				timestamp = timestamp_element.get_text(strip=True) if timestamp_element else ''
				content = content_element.get_text(strip=True)
				
				# Determine if it's incoming or outgoing based on arrow direction and sender
				entry_html = str(entry)
				is_outgoing = '←' in entry_html or sender_name == 'You'
				
				# Convert timestamp to JavaScript Date format if possible
				message_time = None
				if timestamp:
					try:
						# Try to parse various timestamp formats
						from dateutil import parser as date_parser
						parsed_time = date_parser.parse(timestamp)
						message_time = parsed_time.isoformat()
					except:
						# If parsing fails, try to extract time from common formats like "Jan 07, 2025 11:01 AM"
						import re
						time_match = re.search(r'(\d{1,2}:\d{2}\s*(AM|PM|am|pm))', timestamp)
						if time_match:
							try:
								from datetime import datetime
								time_str = time_match.group(1)
								# Create a date object for today with the extracted time
								today = datetime.now().date()
								parsed_time = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %I:%M %p")
								message_time = parsed_time.isoformat()
							except:
								pass
				
				if not message_time:
					# Fallback to current time if no valid timestamp
					from datetime import datetime
					message_time = datetime.now().isoformat()
				
				messages.append({
					'sender': 'user' if is_outgoing else 'contact',
					'text': content,
					'time': message_time,
					'sender_name': sender_name,
				})
		
		return messages
		
	except Exception as e:
		frappe.log_error(f"Error fetching Instagram messages for contact {contact_id}: {str(e)}")
		return []