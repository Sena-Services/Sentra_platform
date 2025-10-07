"""
Ticket API - Handle ticket creation and management
"""
import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def create_ticket_from_weblink(contact_id, change_requested, request_type="Inquiry", package_id=None, trip_id=None):
	"""
	Create a new ticket from package weblink request.

	This endpoint allows guest access for public weblinks to create support tickets.

	Args:
		contact_id: Contact ID (name field from Contact doctype)
		change_requested: The change/request description
		request_type: Type of request (default: Inquiry)
		package_id: Optional package ID for reference
		trip_id: Optional trip ID to link this ticket to a specific trip

	Returns:
		dict: Created ticket details
	"""
	# MUST be first line - disable CSRF check for guest-accessible endpoint
	frappe.flags.ignore_csrf = True

	# Set response to allow guest access
	frappe.local.response.http_status_code = 200

	try:
		print(f"\n{'='*80}")
		print(f"🎫 CREATING TICKET FROM WEBLINK - ENDPOINT HIT!")
		print(f"   Contact ID: {contact_id}")
		print(f"   Request Type: {request_type}")
		print(f"   Package ID: {package_id or 'None'}")
		print(f"   Trip ID: {trip_id or 'None'}")
		print(f"   Change Requested: {change_requested[:100] if change_requested else 'None'}...")
		try:
			print(f"   Request Method: {frappe.request.method}")
			print(f"   Content Type: {frappe.request.content_type}")
		except:
			print(f"   Request Method: (console call)")
		print(f"   Guest Access: {frappe.session.user == 'Guest'}")
		print(f"{'='*80}\n")

		# Validate contact exists
		if not frappe.db.exists("Contact", contact_id):
			frappe.throw(_("Contact {0} does not exist").format(contact_id))

		# Validate trip exists if trip_id is provided
		if trip_id and not frappe.db.exists("Trip", trip_id):
			print(f"⚠️ Warning: Trip {trip_id} does not exist, proceeding without trip link")
			trip_id = None

		# Create ticket
		ticket_data = {
			"doctype": "Ticket",
			"contact": contact_id,
			"request_type": request_type,
			"ticket_status": "Not Resolved",
			"change_requested": change_requested
		}

		# Add trip ID if provided and valid
		if trip_id:
			ticket_data["trip"] = trip_id
			print(f"🔗 Linking ticket to trip: {trip_id}")

		ticket = frappe.get_doc(ticket_data)

		ticket.insert(ignore_permissions=True)
		frappe.db.commit()

		print(f"✅ Ticket created: {ticket.name}")
		print(f"   Contact: {ticket.contact}")
		print(f"   Status: {ticket.ticket_status}")
		print(f"   Request Type: {ticket.request_type}")

		# Send confirmation message to customer via WhatsApp/Instagram
		try:
			from frappe_whatsapp.api.send_message import send_message

			confirmation_message = f"""🎫 *Request Received*

Thank you for submitting your request!

*Ticket ID:* {ticket.name}
*Status:* We are processing your request

Our team will review your request and get back to you shortly. You can track your request using the ticket ID above.

_We appreciate your patience!_"""

			print(f"📤 Sending confirmation message to {contact_id}...")
			send_result = send_message(
				contact_name=contact_id,
				message_content=confirmation_message,
				subject=f"Ticket Confirmation: {ticket.name}"
			)

			if send_result.get("success"):
				print(f"✅ Confirmation message sent successfully")
			else:
				print(f"⚠️ Failed to send confirmation message: {send_result.get('error', 'Unknown error')}")
		except Exception as msg_error:
			print(f"⚠️ Error sending confirmation message: {str(msg_error)}")
			# Don't fail ticket creation if message sending fails
			import traceback
			print(traceback.format_exc())

		# If ticket is linked to a trip, update the trip's tickets child table
		if trip_id:
			try:
				trip = frappe.get_doc("Trip", trip_id)

				# Check if ticket already exists in child table
				ticket_exists = False
				for trip_ticket in trip.tickets:
					if trip_ticket.ticket == ticket.name:
						ticket_exists = True
						break

				if not ticket_exists:
					trip.append("tickets", {
						"ticket": ticket.name,
						"ticket_status": ticket.ticket_status,
						"change_requested": ticket.change_requested
					})
					trip.save(ignore_permissions=True)
					frappe.db.commit()
					print(f"🔗 Added ticket {ticket.name} to trip {trip_id}")
				else:
					print(f"ℹ️ Ticket {ticket.name} already exists in trip {trip_id}")

			except Exception as trip_error:
				print(f"⚠️ Could not update trip {trip_id}: {str(trip_error)}")
				# Don't fail the ticket creation if trip update fails
				pass

		# Return ticket details
		return {
			"success": True,
			"ticket_id": ticket.name,
			"ticket": {
				"name": ticket.name,
				"contact": ticket.contact,
				"contact_name": ticket.contact_name,
				"request_type": ticket.request_type,
				"ticket_status": ticket.ticket_status,
				"change_requested": ticket.change_requested,
				"created_at": str(ticket.created_at),
				"trip": trip_id if trip_id else None
			}
		}

	except Exception as e:
		print(f"❌ ERROR creating ticket: {str(e)}")
		import traceback
		print(traceback.format_exc())
		frappe.log_error(
			title="Ticket Creation Failed",
			message=f"Contact: {contact_id}\nError: {str(e)}\n\n{frappe.get_traceback()}"
		)
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_tickets_for_contact(contact_id):
	"""
	Get all tickets for a contact.

	Args:
		contact_id: Contact ID

	Returns:
		list: List of tickets
	"""
	try:
		tickets = frappe.get_all(
			"Ticket",
			filters={"contact": contact_id},
			fields=["name", "contact", "contact_name", "request_type", "ticket_status",
			        "change_requested", "created_at", "resolved_at", "trip"],
			order_by="created_at desc"
		)

		return {
			"success": True,
			"tickets": tickets
		}

	except Exception as e:
		frappe.log_error(
			title="Get Tickets Failed",
			message=f"Contact: {contact_id}\nError: {str(e)}\n\n{frappe.get_traceback()}"
		)
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def update_ticket_status(ticket_id, new_status):
	"""
	Update ticket status.

	Args:
		ticket_id: Ticket ID
		new_status: New status (Not Resolved, Processing, Resolved)

	Returns:
		dict: Updated ticket details
	"""
	try:
		if new_status not in ["Not Resolved", "Processing", "Resolved"]:
			frappe.throw(_("Invalid status: {0}").format(new_status))

		ticket = frappe.get_doc("Ticket", ticket_id)
		ticket.ticket_status = new_status
		ticket.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"success": True,
			"ticket": {
				"name": ticket.name,
				"ticket_status": ticket.ticket_status,
				"resolved_at": str(ticket.resolved_at) if ticket.resolved_at else None
			}
		}

	except Exception as e:
		frappe.log_error(
			title="Update Ticket Status Failed",
			message=f"Ticket: {ticket_id}\nError: {str(e)}\n\n{frappe.get_traceback()}"
		)
		return {
			"success": False,
			"error": str(e)
		}
