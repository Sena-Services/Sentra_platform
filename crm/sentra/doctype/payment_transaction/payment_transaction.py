# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentTransaction(Document):
	def before_insert(self):
		"""Set transaction_id before inserting"""
		if not self.transaction_id:
			self.transaction_id = self.name

	def validate(self):
		"""Validate transaction data"""
		if self.signature_verified and not self.verified_at:
			self.verified_at = frappe.utils.now_datetime()
