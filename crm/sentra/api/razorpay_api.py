"""
Razorpay Payment Integration API
Handles order creation, payment verification, and invoice generation
"""
import frappe
from frappe import _
import razorpay
import hmac
import hashlib
import json

# Razorpay credentials (test mode)
RAZORPAY_KEY_ID = "rzp_test_RTGHwIWbTEpoZO"
RAZORPAY_KEY_SECRET = "508nu518Fvx2BygNWWCyBL78"

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_contact_from_passenger(passenger_data):
	"""
	Create a new contact from passenger data

	Args:
		passenger_data: Dict with passenger information (name, email, phone)

	Returns:
		str: Contact ID
	"""
	try:
		name = passenger_data.get('name', 'Guest')
		email = passenger_data.get('email', '')
		phone = passenger_data.get('phone', '')

		# Create contact
		contact = frappe.get_doc({
			"doctype": "Contact",
			"first_name": name.split()[0] if name else "Guest",
			"last_name": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
			"full_name": name,
			"email_id": email,
			"mobile_no": phone,
			"status": "Passive"
		})

		contact.insert(ignore_permissions=True)
		frappe.db.commit()

		print(f"✅ Contact created: {contact.name}")
		return contact.name

	except Exception as e:
		print(f"❌ Error creating contact: {str(e)}")
		# Return a default contact or throw error
		frappe.throw(_("Failed to create contact: {0}").format(str(e)))


@frappe.whitelist(allow_guest=True)
def check_existing_booking(package_id, contact_id, trip_id=None):
	"""
	Check if user has already booked and paid for this package

	Args:
		package_id: Standard Package ID
		contact_id: Contact ID
		trip_id: Trip ID (optional)

	Returns:
		dict: Booking status
	"""
	frappe.flags.ignore_csrf = True

	try:
		# Build filters
		filters = {
			"package_id": package_id,
			"payment_status": "Paid",
			"order_status": ["!=", "Cancelled"]
		}

		# Add contact filter if provided
		if contact_id and frappe.db.exists("Contact", contact_id):
			filters["contact_id"] = contact_id
		else:
			# No contact means no existing booking
			return {
				"success": True,
				"has_booking": False
			}

		# Add trip filter if provided
		if trip_id:
			filters["trip_id"] = trip_id

		# Check for existing paid booking
		existing_orders = frappe.get_all(
			"Package Order",
			filters=filters,
			fields=["name", "order_date", "total_amount", "currency", "paid_date"],
			limit=1
		)

		if existing_orders:
			order = existing_orders[0]
			return {
				"success": True,
				"has_booking": True,
				"order_id": order.name,
				"order_date": str(order.order_date),
				"paid_date": str(order.paid_date) if order.paid_date else None,
				"amount": order.total_amount,
				"currency": order.currency
			}

		return {
			"success": True,
			"has_booking": False
		}

	except Exception as e:
		frappe.log_error(
			title="Check Existing Booking Failed",
			message=str(e)
		)
		return {
			"success": False,
			"error": str(e),
			"has_booking": False
		}


@frappe.whitelist(allow_guest=True)
def create_booking_order(package_id, contact_id, passenger_details, amount, currency="INR", trip_id=None):
	"""
	Create a new booking order and Razorpay order

	Args:
		package_id: Standard Package ID
		contact_id: Contact ID (will be created if not exists)
		passenger_details: JSON string with passenger information
		amount: Total amount to charge
		currency: Currency code (default: INR)
		trip_id: Optional Trip ID to link

	Returns:
		dict: Order details with Razorpay order ID
	"""
	frappe.flags.ignore_csrf = True

	try:
		print(f"\n{'='*80}")
		print(f"🛒 CREATING BOOKING ORDER")
		print(f"   Package ID: {package_id}")
		print(f"   Contact ID: {contact_id}")
		print(f"   Amount: {amount} {currency}")
		print(f"   Trip ID: {trip_id or 'None'}")
		print(f"{'='*80}\n")

		# Validate package exists
		if not frappe.db.exists("Standard Package", package_id):
			frappe.throw(_("Package {0} does not exist").format(package_id))

		# Parse passenger details
		if isinstance(passenger_details, str):
			passenger_details = json.loads(passenger_details)

		# Create contact if not exists
		if not contact_id or not frappe.db.exists("Contact", contact_id):
			print(f"⚠️ Contact not found, creating new contact from primary passenger")

			# Get primary passenger details
			primary_passenger = passenger_details[0] if isinstance(passenger_details, list) and len(passenger_details) > 0 else {}

			contact_id = create_contact_from_passenger(primary_passenger)
			print(f"✅ Created new contact: {contact_id}")

		# Parse passenger details
		if isinstance(passenger_details, str):
			passenger_details = json.loads(passenger_details)

		# Get package details
		package = frappe.get_doc("Standard Package", package_id)

		# Get contact details
		contact = frappe.get_doc("Contact", contact_id)

		# Convert amount to paise (Razorpay requires smallest currency unit)
		amount_in_paise = int(float(amount) * 100)

		# Ensure passenger_details is properly formatted for JSON field
		if isinstance(passenger_details, list):
			passenger_details_json = json.dumps(passenger_details)
			num_passengers = len(passenger_details)
		elif isinstance(passenger_details, str):
			# Already a JSON string
			passenger_details_json = passenger_details
			try:
				parsed = json.loads(passenger_details)
				num_passengers = len(parsed) if isinstance(parsed, list) else 1
			except:
				num_passengers = 1
		else:
			passenger_details_json = json.dumps([passenger_details])
			num_passengers = 1

		# Create Package Order first (without payment details)
		order = frappe.get_doc({
			"doctype": "Package Order",
			"package_id": package_id,
			"contact_id": contact_id,
			"trip_id": trip_id,
			"passenger_details": passenger_details_json,
			"number_of_passengers": num_passengers,
			"currency": currency,
			"base_amount": float(amount),
			"total_amount": float(amount),
			"order_status": "Pending",
			"payment_status": "Unpaid",
			"payment_gateway": "Razorpay"
		})

		order.insert(ignore_permissions=True)
		frappe.db.commit()

		print(f"✅ Package order created: {order.name}")

		# Get callback URL
		callback_url = frappe.utils.get_url(f"/api/method/crm.sentra.api.razorpay_api.invoice_payment_callback?order_id={order.name}")

		# Create Razorpay Invoice
		invoice_data = {
			"type": "invoice",
			"description": f"Travel Package: {package.package_name}",
			"customer": {
				"name": contact.full_name or contact.first_name,
				"email": contact.email_id or "",
				"contact": contact.mobile_no or ""
			},
			"line_items": [{
				"name": package.package_name,
				"description": f"Booking for {num_passengers} passenger(s)",
				"amount": amount_in_paise,
				"currency": currency,
				"quantity": 1
			}],
			"currency": currency,
			"sms_notify": 1,
			"email_notify": 1,
			"partial_payment": False,
			"receipt": order.name,  # Link invoice to our order
			"callback_url": callback_url,
			"callback_method": "get"
		}

		print(f"📄 Creating Razorpay invoice for order {order.name}...")

		razorpay_invoice = razorpay_client.invoice.create(data=invoice_data)

		print(f"✅ Razorpay invoice created: {razorpay_invoice.get('id')}")
		print(f"   Invoice URL: {razorpay_invoice.get('short_url')}")

		# Update order with Razorpay invoice details
		order.razorpay_invoice_id = razorpay_invoice.get('id')
		order.razorpay_invoice_url = razorpay_invoice.get('short_url')
		order.save(ignore_permissions=True)
		frappe.db.commit()

		# Return invoice details for frontend
		return {
			"success": True,
			"order_id": order.name,
			"razorpay_invoice_id": razorpay_invoice.get('id'),
			"invoice_url": razorpay_invoice.get('short_url'),
			"amount": float(amount),
			"currency": currency,
			"package_name": package.package_name,
			"contact_email": contact.email_id,
			"contact_phone": contact.mobile_no
		}

	except Exception as e:
		print(f"❌ ERROR creating booking order: {str(e)}")
		import traceback
		print(traceback.format_exc())
		frappe.log_error(
			title="Booking Order Creation Failed",
			message=f"Package: {package_id}\nError: {str(e)}\n\n{frappe.get_traceback()}"
		)
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def verify_payment(order_id, razorpay_payment_id, razorpay_signature, razorpay_order_id):
	"""
	Verify Razorpay payment signature and update order status

	Args:
		order_id: Package Order ID
		razorpay_payment_id: Payment ID from Razorpay
		razorpay_signature: Signature from Razorpay
		razorpay_order_id: Order ID from Razorpay

	Returns:
		dict: Verification result with invoice details
	"""
	frappe.flags.ignore_csrf = True

	try:
		print(f"\n{'='*80}")
		print(f"🔐 VERIFYING PAYMENT")
		print(f"   Order ID: {order_id}")
		print(f"   Razorpay Payment ID: {razorpay_payment_id}")
		print(f"   Razorpay Order ID: {razorpay_order_id}")
		print(f"{'='*80}\n")

		# Get order
		order = frappe.get_doc("Package Order", order_id)

		# Verify signature
		signature_payload = f"{razorpay_order_id}|{razorpay_payment_id}"
		expected_signature = hmac.new(
			RAZORPAY_KEY_SECRET.encode('utf-8'),
			signature_payload.encode('utf-8'),
			hashlib.sha256
		).hexdigest()

		if expected_signature != razorpay_signature:
			print(f"❌ Signature verification failed")
			return {
				"success": False,
				"error": "Payment verification failed. Invalid signature."
			}

		print(f"✅ Signature verified successfully")

		# Fetch payment details from Razorpay
		payment = razorpay_client.payment.fetch(razorpay_payment_id)

		# Create Payment Transaction record
		transaction = frappe.get_doc({
			"doctype": "Payment Transaction",
			"order_id": order_id,
			"contact_id": order.contact_id,
			"amount": order.total_amount,
			"currency": order.currency,
			"razorpay_order_id": razorpay_order_id,
			"razorpay_payment_id": razorpay_payment_id,
			"razorpay_signature": razorpay_signature,
			"payment_method": payment.get("method"),
			"payment_email": payment.get("email"),
			"payment_contact": payment.get("contact"),
			"transaction_status": "Captured" if payment.get("captured") else "Failed",
			"payment_captured": payment.get("captured"),
			"signature_verified": True,
			"verified_at": frappe.utils.now_datetime()
		})

		transaction.insert(ignore_permissions=True)
		frappe.db.commit()

		print(f"✅ Payment transaction created: {transaction.name}")

		# Update order status
		order.payment_id = transaction.name
		order.razorpay_payment_id = razorpay_payment_id
		order.payment_method = payment.get("method")
		order.payment_status = "Paid"
		order.order_status = "Confirmed"
		order.paid_date = frappe.utils.now_datetime()

		# Call order's on_payment_success method
		order.on_payment_success()

		print(f"✅ Order updated: {order.name}")

		# Get contact details
		contact = frappe.get_doc("Contact", order.contact_id)

		# Send email receipt via Razorpay
		try:
			print(f"📧 Sending Razorpay email receipt to {contact.email_id}...")

			receipt_response = razorpay_client.payment.send_notification(
				razorpay_payment_id,
				{
					"email": contact.email_id or payment.get("email"),
					"medium": "email"
				}
			)

			print(f"✅ Email receipt sent successfully")
		except Exception as e:
			print(f"⚠️ Error sending email receipt: {str(e)}")

		# Create payment receipt URL
		payment_receipt_url = f"https://dashboard.razorpay.com/app/payments/{razorpay_payment_id}"

		# Store receipt URL in order
		order.razorpay_invoice_url = payment_receipt_url
		order.save(ignore_permissions=True)
		frappe.db.commit()

		# Send confirmation with payment details via WhatsApp/Instagram
		try:
			send_payment_confirmation_to_channel(order, payment, razorpay_payment_id)
		except Exception as msg_error:
			print(f"⚠️ Error sending confirmation to channel: {str(msg_error)}")

		return {
			"success": True,
			"order_id": order.name,
			"payment_id": razorpay_payment_id,
			"invoice_url": payment_receipt_url,
			"message": "Payment verified successfully. Your booking is confirmed!"
		}

	except Exception as e:
		print(f"❌ ERROR verifying payment: {str(e)}")
		import traceback
		print(traceback.format_exc())
		frappe.log_error(
			title="Payment Verification Failed",
			message=f"Order: {order_id}\nError: {str(e)}\n\n{frappe.get_traceback()}"
		)
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_order_status(order_id):
	"""
	Get order and payment status

	Args:
		order_id: Package Order ID

	Returns:
		dict: Order status details
	"""
	try:
		order = frappe.get_doc("Package Order", order_id)

		return {
			"success": True,
			"order": {
				"name": order.name,
				"order_status": order.order_status,
				"payment_status": order.payment_status,
				"total_amount": order.total_amount,
				"currency": order.currency,
				"razorpay_order_id": order.razorpay_order_id,
				"razorpay_payment_id": order.razorpay_payment_id,
				"invoice_id": order.invoice_id,
				"invoice_generated": order.invoice_generated
			}
		}

	except Exception as e:
		frappe.log_error(
			title="Get Order Status Failed",
			message=f"Order: {order_id}\nError: {str(e)}\n\n{frappe.get_traceback()}"
		)
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def download_invoice(invoice_id):
	"""
	Get invoice PDF download URL

	Args:
		invoice_id: Package Invoice ID

	Returns:
		dict: Invoice PDF details
	"""
	frappe.flags.ignore_csrf = True

	try:
		invoice = frappe.get_doc("Package Invoice", invoice_id)

		if not invoice.pdf_file:
			return {
				"success": False,
				"error": "Invoice PDF not generated yet"
			}

		# Get full URL
		pdf_url = frappe.utils.get_url(invoice.pdf_file)

		return {
			"success": True,
			"invoice_id": invoice.name,
			"invoice_number": invoice.invoice_number,
			"pdf_url": pdf_url,
			"pdf_path": invoice.pdf_file,
			"invoice_date": str(invoice.invoice_date),
			"total_amount": invoice.total_amount,
			"currency": invoice.currency,
			"order_id": invoice.order_id,
			"package_name": invoice.package_name
		}

	except Exception as e:
		frappe.log_error(
			title="Download Invoice Failed",
			message=f"Invoice: {invoice_id}\nError: {str(e)}\n\n{frappe.get_traceback()}"
		)
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def invoice_payment_callback():
	"""
	Handle callback after Razorpay invoice payment
	"""
	frappe.flags.ignore_csrf = True

	try:
		# Get parameters from URL
		order_id = frappe.request.args.get('order_id')
		razorpay_invoice_id = frappe.request.args.get('razorpay_invoice_id')
		razorpay_payment_id = frappe.request.args.get('razorpay_payment_id')

		print(f"\n{'='*80}")
		print(f"📞 INVOICE PAYMENT CALLBACK")
		print(f"   Order ID: {order_id}")
		print(f"   Invoice ID: {razorpay_invoice_id}")
		print(f"   Payment ID: {razorpay_payment_id}")
		print(f"{'='*80}\n")

		if not order_id:
			return frappe.redirect_to_message(
				"Error",
				"Order ID not provided",
				indicator_color='red'
			)

		# Get order
		if not frappe.db.exists("Package Order", order_id):
			return frappe.redirect_to_message(
				"Error",
				f"Order {order_id} not found",
				indicator_color='red'
			)

		order = frappe.get_doc("Package Order", order_id)

		# Fetch latest invoice status from Razorpay
		if razorpay_invoice_id or order.razorpay_invoice_id:
			invoice_id = razorpay_invoice_id or order.razorpay_invoice_id

			try:
				# Fetch invoice from Razorpay
				invoice = razorpay_client.invoice.fetch(invoice_id)

				print(f"📄 Invoice Status: {invoice.get('status')}")
				print(f"   Paid: {invoice.get('paid_at')}")

				# Check if invoice is paid
				if invoice.get('status') == 'paid':
					# Get payment details
					payment_id = invoice.get('payment_id') or razorpay_payment_id

					# Create Payment Transaction
					if payment_id and not frappe.db.exists("Payment Transaction", {"razorpay_payment_id": payment_id}):
						# Fetch payment details
						try:
							payment = razorpay_client.payment.fetch(payment_id)
						except:
							payment = {}

						transaction = frappe.get_doc({
							"doctype": "Payment Transaction",
							"order_id": order.name,
							"contact_id": order.contact_id,
							"amount": order.total_amount,
							"currency": order.currency,
							"razorpay_payment_id": payment_id,
							"payment_method": payment.get("method", "Unknown"),
							"payment_email": payment.get("email"),
							"payment_contact": payment.get("contact"),
							"transaction_status": "Captured",
							"payment_captured": True,
							"signature_verified": True,
							"verified_at": frappe.utils.now_datetime()
						})

						transaction.insert(ignore_permissions=True)
						frappe.db.commit()

						print(f"✅ Payment transaction created: {transaction.name}")

						# Update order
						order.payment_id = transaction.name
						order.razorpay_payment_id = payment_id

					# Update order status
					order.payment_status = "Paid"
					order.order_status = "Confirmed"
					order.paid_date = frappe.utils.now_datetime()
					order.invoice_generated = 1
					order.save(ignore_permissions=True)
					frappe.db.commit()

					print(f"✅ Order {order.name} updated to Paid status")

					# Send WhatsApp confirmation
					try:
						send_payment_confirmation_to_channel(order, invoice)
					except Exception as e:
						print(f"⚠️ Error sending WhatsApp: {str(e)}")

					# Redirect to success page
					return frappe.redirect_to_message(
						"Payment Successful! 🎉",
						f"""Your booking is confirmed!<br><br>
						<strong>Order ID:</strong> {order.name}<br>
						<strong>Amount Paid:</strong> {order.currency} {order.total_amount:,.2f}<br><br>
						Your invoice has been sent to your email and WhatsApp.<br><br>
						<a href="{order.razorpay_invoice_url}" target="_blank" class="btn btn-primary">View Invoice</a>""",
						indicator_color='green'
					)

				elif invoice.get('status') == 'issued':
					# Invoice not paid yet
					return frappe.redirect_to_message(
						"Payment Pending",
						f"""Your invoice is still pending payment.<br><br>
						<strong>Order ID:</strong> {order.name}<br><br>
						<a href="{order.razorpay_invoice_url}" target="_blank" class="btn btn-primary">Complete Payment</a>""",
						indicator_color='orange'
					)

			except Exception as e:
				print(f"❌ Error fetching invoice: {str(e)}")
				frappe.log_error(
					title=f"Invoice Fetch Failed: {invoice_id}",
					message=str(e)
				)

		# Default redirect
		return frappe.redirect_to_message(
			"Order Created",
			f"""Your order has been created.<br><br>
			<strong>Order ID:</strong> {order.name}<br><br>
			Please complete payment to confirm your booking.<br><br>
			<a href="{order.razorpay_invoice_url}" target="_blank" class="btn btn-primary">Pay Now</a>""",
			indicator_color='blue'
		)

	except Exception as e:
		print(f"❌ Callback error: {str(e)}")
		import traceback
		print(traceback.format_exc())
		frappe.log_error(
			title="Invoice Payment Callback Error",
			message=str(e)
		)
		return frappe.redirect_to_message(
			"Error",
			"An error occurred processing your payment. Please contact support.",
			indicator_color='red'
		)


@frappe.whitelist(allow_guest=True)
def razorpay_webhook():
	"""
	Handle Razorpay webhooks for invoice payments
	"""
	frappe.flags.ignore_csrf = True

	try:
		# Get webhook data
		webhook_body = frappe.request.get_data(as_text=True)
		webhook_signature = frappe.request.headers.get('X-Razorpay-Signature')

		# Verify webhook signature
		expected_signature = hmac.new(
			RAZORPAY_WEBHOOK_SECRET.encode('utf-8') if 'RAZORPAY_WEBHOOK_SECRET' in globals() else RAZORPAY_KEY_SECRET.encode('utf-8'),
			webhook_body.encode('utf-8'),
			hashlib.sha256
		).hexdigest()

		if expected_signature != webhook_signature:
			print(f"⚠️ Webhook signature verification failed")
			return {"success": False, "error": "Invalid signature"}

		# Parse webhook data
		webhook_data = json.loads(webhook_body)
		event = webhook_data.get('event')

		print(f"📥 Razorpay Webhook: {event}")

		# Handle invoice paid event
		if event == 'invoice.paid':
			invoice_data = webhook_data.get('payload', {}).get('invoice', {}).get('entity', {})
			invoice_id = invoice_data.get('id')
			receipt = invoice_data.get('receipt')  # This is our order ID

			print(f"✅ Invoice paid: {invoice_id}")
			print(f"   Order ID: {receipt}")

			if receipt and frappe.db.exists("Package Order", receipt):
				# Update order status
				order = frappe.get_doc("Package Order", receipt)
				order.payment_status = "Paid"
				order.order_status = "Confirmed"
				order.paid_date = frappe.utils.now_datetime()
				order.save(ignore_permissions=True)
				frappe.db.commit()

				print(f"✅ Order {receipt} marked as paid")

				# Send WhatsApp confirmation
				try:
					send_payment_confirmation_to_channel(order, invoice_data)
				except Exception as e:
					print(f"⚠️ Error sending WhatsApp: {str(e)}")

		return {"success": True}

	except Exception as e:
		frappe.log_error(
			title="Razorpay Webhook Error",
			message=str(e)
		)
		print(f"❌ Webhook error: {str(e)}")
		return {"success": False, "error": str(e)}


def send_payment_confirmation_to_channel(order, payment_data):
	"""
	Send payment confirmation with invoice link to WhatsApp
	"""
	try:
		from frappe_whatsapp.api.send_message import send_message

		# Get package name
		package_name = "Travel Package"
		if order.package_id:
			try:
				package = frappe.get_doc("Standard Package", order.package_id)
				package_name = package.package_name
			except:
				pass

		# Format message
		message = f"""🎉 *Payment Confirmed!*

Thank you for your payment!

*Booking Details:*
📦 Order ID: {order.name}
✈️ Package: {package_name}
👥 Passengers: {order.number_of_passengers}
💰 Amount Paid: {order.currency} {order.total_amount:,.2f}

Your invoice has been sent to your email by Razorpay.

📄 *View Invoice:* {order.razorpay_invoice_url}

_We're excited to serve you! Safe travels!_ ✈️"""

		# Send via WhatsApp
		result = send_message(
			contact_name=order.contact_id,
			message_content=message,
			subject=f"Payment Confirmation - {order.name}"
		)

		print(f"✅ WhatsApp confirmation sent to {order.contact_id}")
		return result

	except Exception as e:
		frappe.log_error(
			title=f"Send Payment Confirmation Failed for {order.name}",
			message=str(e)
		)
		print(f"❌ Error sending confirmation: {str(e)}")
		return None


@frappe.whitelist(allow_guest=True)
def resend_invoice(invoice_id, contact_id):
	"""
	Resend invoice to contact's channel

	Args:
		invoice_id: Package Invoice ID
		contact_id: Contact ID

	Returns:
		dict: Success status
	"""
	frappe.flags.ignore_csrf = True

	try:
		invoice = frappe.get_doc("Package Invoice", invoice_id)

		# Send to WhatsApp/Instagram
		result = send_invoice_to_channel(invoice, contact_id)

		if result.get("success"):
			return {
				"success": True,
				"message": "Invoice sent successfully to your WhatsApp/Instagram"
			}
		else:
			return {
				"success": False,
				"error": result.get("error", "Failed to send invoice")
			}

	except Exception as e:
		frappe.log_error(
			title="Resend Invoice Failed",
			message=f"Invoice: {invoice_id}\nContact: {contact_id}\nError: {str(e)}\n\n{frappe.get_traceback()}"
		)
		return {
			"success": False,
			"error": str(e)
		}


def create_razorpay_invoice(order):
	"""
	Create invoice via Razorpay Invoice API

	Args:
		order: Package Order document

	Returns:
		dict: Razorpay invoice object
	"""
	try:
		# Get contact details
		contact = frappe.get_doc("Contact", order.contact_id)

		# Get passenger details
		passengers = []
		if order.passenger_details:
			passengers = order.passenger_details if isinstance(order.passenger_details, list) else json.loads(order.passenger_details)

		# Get package name
		package_name = "Travel Package"
		if order.package_id:
			try:
				package = frappe.get_doc("Standard Package", order.package_id)
				package_name = package.package_name
			except:
				pass

		# Prepare line items
		line_items = [{
			"name": package_name,
			"description": f"Booking for {order.number_of_passengers} passenger(s)",
			"amount": int(float(order.total_amount) * 100),  # Convert to paise
			"currency": order.currency,
			"quantity": 1
		}]

		# Prepare customer details
		customer_details = {
			"name": contact.full_name or contact.first_name,
			"email": contact.email_id or "",
			"contact": contact.mobile_no or ""
		}

		# Create invoice via Razorpay API
		invoice_data = {
			"type": "invoice",
			"description": f"Travel Package Booking - {package_name}",
			"customer": customer_details,
			"line_items": line_items,
			"currency": order.currency,
			"expire_by": int((frappe.utils.now_datetime() + frappe.utils.timedelta(days=30)).timestamp()),
			"sms_notify": 1,
			"email_notify": 1,
			"partial_payment": False
		}

		print(f"📄 Creating Razorpay invoice for order {order.name}...")

		# Call Razorpay Invoice API
		razorpay_invoice = razorpay_client.invoice.create(data=invoice_data)

		# Mark invoice as paid since payment is already done
		# Note: This might require additional API call or we just store the invoice for record

		print(f"✅ Razorpay invoice created: {razorpay_invoice.get('id')}")
		print(f"   Invoice URL: {razorpay_invoice.get('short_url')}")

		return razorpay_invoice

	except Exception as e:
		frappe.log_error(
			title=f"Razorpay Invoice Creation Failed for Order {order.name}",
			message=str(e)
		)
		print(f"❌ Error creating Razorpay invoice: {str(e)}")
		return None


def send_razorpay_invoice_to_channel(order, razorpay_invoice):
	"""
	Send Razorpay invoice link to the user's WhatsApp or Instagram channel

	Args:
		order: Package Order document
		razorpay_invoice: Razorpay invoice object
	"""
	try:
		from frappe_whatsapp.api.send_message import send_message

		print(f"📤 Sending Razorpay invoice to contact {order.contact_id}...")

		# Get invoice details
		invoice_id = razorpay_invoice.get('id')
		invoice_url = razorpay_invoice.get('short_url')

		# Get package name
		package_name = "Travel Package"
		if order.package_id:
			try:
				package = frappe.get_doc("Standard Package", order.package_id)
				package_name = package.package_name
			except:
				pass

		# Format message with Razorpay invoice link
		message = f"""🎉 *Booking Confirmed!*

Thank you for booking with Sentra Travel!

*Invoice Details:*
📋 Invoice ID: {invoice_id}
📦 Order ID: {order.name}
✈️ Package: {package_name}
👥 Passengers: {order.number_of_passengers}
💰 Total Amount: {order.currency} {order.total_amount:,.2f}

📄 *Download Invoice:* {invoice_url}

_We're excited to serve you! Safe travels!_ ✈️"""

		# Send via WhatsApp/Instagram
		result = send_message(
			contact_name=order.contact_id,
			message_content=message,
			subject=f"Booking Confirmation - {order.name}"
		)

		if result:
			print(f"✅ Invoice sent successfully to {order.contact_id}")

		return result

	except Exception as e:
		frappe.log_error(
			title=f"Send Razorpay Invoice Failed for Order {order.name}",
			message=str(e)
		)
		print(f"❌ Error sending invoice: {str(e)}")
		raise


def send_invoice_to_channel(invoice, contact_id):
	"""
	Send invoice to the user's WhatsApp or Instagram channel

	Args:
		invoice: Package Invoice doc
		contact_id: Contact ID
	"""
	try:
		from frappe_whatsapp.api.send_message import send_message

		# Get contact details
		contact = frappe.get_doc("Contact", contact_id)

		# Prepare invoice message
		pdf_url = frappe.utils.get_url(invoice.pdf_file) if invoice.pdf_file else ""

		message = f"""🎉 *Booking Confirmed!*

Thank you for booking with Sentra Travel!

*Invoice Details:*
📋 Invoice Number: {invoice.invoice_number}
📦 Order ID: {invoice.order_id}
✈️ Package: {invoice.package_name or 'Travel Package'}
👥 Passengers: {invoice.number_of_passengers}
💰 Total Amount: {invoice.currency} {invoice.total_amount:,.2f}

Your invoice has been generated and is ready for download.

📄 *Download Invoice:* {pdf_url}

_We're excited to serve you! Safe travels!_ ✈️"""

		print(f"📤 Sending invoice to contact {contact_id} via WhatsApp/Instagram...")

		# Send message via WhatsApp/Instagram
		result = send_message(
			contact_name=contact_id,
			message_content=message,
			subject=f"Booking Confirmation - {invoice.invoice_number}"
		)

		if result.get("success"):
			print(f"✅ Invoice sent successfully to {contact_id}")
		else:
			print(f"⚠️ Failed to send invoice: {result.get('error', 'Unknown error')}")

		return result

	except Exception as e:
		print(f"❌ Error sending invoice to channel: {str(e)}")
		import traceback
		print(traceback.format_exc())
		frappe.log_error(
			title=f"Send Invoice to Channel Failed - {invoice.name}",
			message=str(e)
		)
		return {"success": False, "error": str(e)}


def create_invoice_for_order(order_id):
	"""
	Create invoice for a package order

	Args:
		order_id: Package Order ID

	Returns:
		Package Invoice doc
	"""
	try:
		order = frappe.get_doc("Package Order", order_id)

		# Check if invoice already exists
		if order.invoice_id and frappe.db.exists("Package Invoice", order.invoice_id):
			return frappe.get_doc("Package Invoice", order.invoice_id)

		# Get passenger names
		passenger_names = []
		if order.passenger_details:
			passengers = order.passenger_details if isinstance(order.passenger_details, list) else json.loads(order.passenger_details)
			passenger_names = [p.get("name", "") for p in passengers if p.get("name")]

		# Get package name from order
		package_name = None
		if order.package_id:
			try:
				package = frappe.get_doc("Standard Package", order.package_id)
				package_name = package.package_name
			except Exception as e:
				frappe.log_error(f"Error fetching package name: {str(e)}")

		# Create invoice
		invoice = frappe.get_doc({
			"doctype": "Package Invoice",
			"order_id": order.name,
			"contact_id": order.contact_id,
			"package_id": order.package_id,
			"package_name": package_name,
			"trip_id": order.trip_id,
			"currency": order.currency,
			"subtotal": order.base_amount,
			"tax_amount": order.tax_amount or 0,
			"discount_amount": order.discount_amount or 0,
			"total_amount": order.total_amount,
			"number_of_passengers": order.number_of_passengers,
			"passenger_names": ", ".join(passenger_names),
			"payment_method": order.payment_method,
			"payment_id": order.payment_id,
			"razorpay_payment_id": order.razorpay_payment_id,
			"paid_date": order.paid_date,
			"invoice_status": "Generated"
		})

		invoice.insert(ignore_permissions=True)
		frappe.db.commit()

		return invoice

	except Exception as e:
		frappe.log_error(
			title=f"Create Invoice Failed for Order {order_id}",
			message=str(e)
		)
		return None
