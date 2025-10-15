# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PackageOrder(Document):
	def before_insert(self):
		"""Set order_id before inserting"""
		if not self.order_id:
			self.order_id = self.name

	def validate(self):
		"""Calculate total amount"""
		self.calculate_total()

	def calculate_total(self):
		"""Calculate total amount from base amount, tax, and discount"""
		base = float(self.base_amount or 0)
		tax = float(self.tax_amount or 0)
		discount = float(self.discount_amount or 0)

		self.total_amount = base + tax - discount

	def on_payment_success(self):
		"""Called when payment is successful"""
		self.payment_status = 'Paid'
		self.order_status = 'Confirmed'
		self.paid_date = frappe.utils.now_datetime()
		self.save(ignore_permissions=True)
		frappe.db.commit()

		# Generate invoice if not already generated
		if not self.invoice_generated:
			self.generate_invoice()

	def generate_invoice(self):
		"""Generate invoice for this order"""
		try:
			# Import here to avoid circular imports
			from crm.sentra.api.razorpay_api import create_invoice_for_order

			invoice = create_invoice_for_order(self.name)
			if invoice:
				self.invoice_id = invoice.name
				self.invoice_generated = 1
				self.save(ignore_permissions=True)
				frappe.db.commit()
				return invoice
		except Exception as e:
			frappe.log_error(
				title=f"Invoice Generation Failed for {self.name}",
				message=str(e)
			)
			return None
