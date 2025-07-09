# Copyright (c) 2024, Sentra and contributors
# For license information, please see license.txt

import frappe


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