# Copyright (c) 2025, arvis and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Trip(Document):
	def insert(self, ignore_permissions=None, ignore_links=None, ignore_if_duplicate=None, ignore_mandatory=None, set_name=None, set_child_names=None):
		"""Override insert to auto-create destinations before link validation"""
		
		# Auto-create destinations first
		try:
			if hasattr(self, 'destination_city') and self.destination_city:
				for destination_row in self.destination_city:
					if hasattr(destination_row, 'destination') and destination_row.destination:
						destination_name = str(destination_row.destination).strip()
						if destination_name:
							# Check if destination exists
							if not frappe.db.exists("Destination", destination_name):
								# Create new destination using Document API
								dest_doc = frappe.get_doc({
									'doctype': 'Destination',
									'city': destination_name.title(),
									'country': 'Unknown'
								})
								dest_doc.insert(ignore_permissions=True)
								# Update the reference to the created destination
								destination_row.destination = dest_doc.name
		except Exception as e:
			frappe.log_error(f"Error auto-creating destinations: {str(e)}")
		
		# Now call the parent insert method
		return super().insert(
			ignore_permissions=ignore_permissions,
			ignore_links=ignore_links, 
			ignore_if_duplicate=ignore_if_duplicate,
			ignore_mandatory=ignore_mandatory,
			set_name=set_name,
			set_child_names=set_child_names
		)
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
