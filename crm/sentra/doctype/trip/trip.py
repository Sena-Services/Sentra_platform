# Copyright (c) 2025, arvis and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Trip(Document):
	@staticmethod
	def default_list_data():
		"""
		Default list configuration for Trip doctype
		Following CRM's exact pattern
		"""
		columns = [
			{"label": "Trip Name", "type": "Data", "key": "title", "width": "200px"},
			{"label": "Destination", "type": "Data", "key": "destination_city", "width": "150px"},
			{"label": "Start Date", "type": "Date", "key": "start_date", "width": "120px"},
			{"label": "End Date", "type": "Date", "key": "end_date", "width": "120px"},
			{"label": "PAX", "type": "Int", "key": "pax", "width": "80px"},
			{"label": "Budget", "type": "Currency", "key": "budget", "width": "120px"},
		]
		rows = [
			"name", "title", "destination_city", "start_date", "end_date", 
			"pax", "budget", "status", "lead", "creation", "modified"
		]
		return {"columns": columns, "rows": rows}
