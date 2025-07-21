# Copyright (c) 2025, Sentra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DMC(Document):
	def validate(self):
		self.validate_insurance()
		self.validate_registration()
	
	def validate_insurance(self):
		"""Validate insurance details if liability insurance is enabled"""
		if self.liability_insurance:
			if not self.insurance_provider:
				frappe.throw("Insurance Provider is required when Liability Insurance is enabled")
			if not self.policy_number:
				frappe.throw("Policy Number is required when Liability Insurance is enabled")
			if self.insurance_validity and self.insurance_validity < frappe.utils.today():
				frappe.msgprint("Insurance has expired. Please update the insurance details.")
	
	def validate_registration(self):
		"""Validate registration and license details"""
		if self.status == "Active" and not self.registration_number:
			frappe.msgprint("Registration Number is recommended for Active DMCs")