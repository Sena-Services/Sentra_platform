# Copyright (c) 2025, Sentra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class Activity(Document):
	def validate(self):
		self.validate_age_limits()
		self.validate_participant_limits()
		self.validate_pricing()
		self.calculate_total_duration()
	
	def validate_age_limits(self):
		"""Validate age limits are logical"""
		if self.minimum_age and self.maximum_age:
			if self.minimum_age > self.maximum_age:
				frappe.throw("Minimum age cannot be greater than maximum age")
	
	def validate_participant_limits(self):
		"""Validate participant limits are logical"""
		if self.min_participants and self.max_participants:
			if self.min_participants > self.max_participants:
				frappe.throw("Minimum participants cannot be greater than maximum participants")
	
	def validate_pricing(self):
		"""Validate pricing logic"""
		# Removed validation for adult_price requirement

		if self.group_discount_applicable:
			if not self.group_size_for_discount:
				frappe.throw("Group size is required when group discount is applicable")
			if not self.group_discount_percentage:
				frappe.throw("Discount percentage is required when group discount is applicable")
	
	def calculate_total_duration(self):
		"""Calculate total duration in minutes"""
		total_minutes = (flt(self.duration_hours) * 60) + flt(self.duration_minutes)
		if total_minutes > 0:
			self.total_duration_minutes = total_minutes