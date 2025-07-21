# Copyright (c) 2025, Sentra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Hotel(Document):
	def validate(self):
		self.validate_star_rating()
		self.calculate_title()
	
	def validate_star_rating(self):
		"""Validate star rating matches category"""
		if self.star_rating and self.category:
			if "5 Star" in self.star_rating and self.category == "Budget":
				frappe.msgprint("5 Star hotels are typically not in Budget category")
			elif "1 Star" in self.star_rating and self.category == "Luxury":
				frappe.msgprint("1 Star hotels are typically not in Luxury category")
	
	def calculate_title(self):
		"""Set title for better display"""
		if self.hotel_name and self.city:
			self.title = f"{self.hotel_name}, {self.city}"