# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_url, get_files_path
import os

class PackageInvoice(Document):
	def validate(self):
		"""Calculate total amount"""
		self.calculate_total()

	def calculate_total(self):
		"""Calculate total amount from subtotal, tax, and discount"""
		subtotal = float(self.subtotal or 0)
		tax = float(self.tax_amount or 0)
		discount = float(self.discount_amount or 0)

		self.total_amount = subtotal + tax - discount

	def after_insert(self):
		"""Set invoice number and generate PDF after invoice is created"""
		# Set invoice_number and invoice_id from auto-generated name
		if not self.invoice_number:
			self.invoice_number = self.name
		if not self.invoice_id:
			self.invoice_id = self.name

		# Get package name from order if not set
		if not self.package_name and self.order_id:
			try:
				order = frappe.get_doc("Package Order", self.order_id)
				if order.package_id:
					package = frappe.get_doc("Standard Package", order.package_id)
					self.package_name = package.package_name
			except Exception as e:
				frappe.log_error(f"Error fetching package name: {str(e)}")

		# Save invoice_number before generating PDF
		frappe.db.set_value(self.doctype, self.name, {
			"invoice_number": self.invoice_number,
			"invoice_id": self.invoice_id,
			"package_name": self.package_name
		}, update_modified=False)
		frappe.db.commit()

		# Now generate PDF with proper invoice_number
		self.generate_pdf()

	def generate_pdf(self):
		"""Generate PDF invoice"""
		try:
			# Get invoice template
			template_path = frappe.get_app_path("crm", "sentra", "templates", "invoice_template.html")

			if not os.path.exists(template_path):
				frappe.log_error(
					title="Invoice Template Not Found",
					message=f"Template not found at: {template_path}"
				)
				return

			# Prepare invoice data
			invoice_data = self.as_dict()

			# Get order details if available
			if self.order_id:
				order = frappe.get_doc("Package Order", self.order_id)
				invoice_data["order"] = order.as_dict()

			# Render template
			html = frappe.render_template(template_path, {"doc": invoice_data})

			# Generate PDF
			pdf = frappe.utils.pdf.get_pdf(html)

			# Save PDF file
			file_name = f"Invoice-{self.invoice_number}.pdf"

			# Create file doc
			file_doc = frappe.get_doc({
				"doctype": "File",
				"file_name": file_name,
				"attached_to_doctype": self.doctype,
				"attached_to_name": self.name,
				"content": pdf,
				"is_private": 1
			})
			file_doc.save(ignore_permissions=True)

			# Update invoice with PDF file path
			self.pdf_file = file_doc.file_url
			self.invoice_status = "Generated"
			self.save(ignore_permissions=True)
			frappe.db.commit()

			return file_doc.file_url

		except Exception as e:
			frappe.log_error(
				title=f"PDF Generation Failed for {self.name}",
				message=str(e)
			)
			return None

	def send_invoice_email(self):
		"""Send invoice email to customer"""
		try:
			if not self.customer_email:
				return False

			# Prepare email content
			subject = f"Your Travel Package Invoice - {self.invoice_number}"

			message = f"""
			<p>Dear {self.customer_name},</p>

			<p>Thank you for booking with us! Your payment has been confirmed.</p>

			<p><strong>Invoice Details:</strong></p>
			<ul>
				<li>Invoice Number: {self.invoice_number}</li>
				<li>Order ID: {self.order_id}</li>
				<li>Package: {self.package_name}</li>
				<li>Total Amount: {self.currency} {self.total_amount}</li>
				<li>Invoice Date: {self.invoice_date}</li>
			</ul>

			<p>Your invoice is attached to this email.</p>

			<p>We look forward to serving you!</p>

			<p>Best regards,<br>Sentra Travel Team</p>
			"""

			# Send email with attachment
			frappe.sendmail(
				recipients=[self.customer_email],
				subject=subject,
				message=message,
				attachments=[{
					"fname": f"Invoice-{self.invoice_number}.pdf",
					"fcontent": self.get_pdf_content()
				}]
			)

			return True

		except Exception as e:
			frappe.log_error(
				title=f"Email Send Failed for {self.name}",
				message=str(e)
			)
			return False

	def get_pdf_content(self):
		"""Get PDF file content"""
		if not self.pdf_file:
			return None

		try:
			file_doc = frappe.get_doc("File", {"file_url": self.pdf_file})
			return file_doc.get_content()
		except:
			return None
