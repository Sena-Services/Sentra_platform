# Copyright (c) 2025, arvis and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Trip(Document):
	def validate(self):
		"""Copy destinations from linked Standard Package to Trip"""
		self.sync_destinations_from_package()

	def sync_destinations_from_package(self):
		"""
		When use_standard_package is set, copy destinations from that package to Trip's destination_city table
		"""
		if not self.use_standard_package:
			return

		try:
			# Get the linked package
			package = frappe.get_doc("Standard Package", self.use_standard_package)

			# Check if package has destinations
			if not package.destinations:
				print(f"⚠️ Package {self.use_standard_package} has no destinations to copy")
				return

			# Get existing destination names in trip (to avoid duplicates)
			existing_destinations = set()
			if self.destination_city:
				existing_destinations = {d.destination for d in self.destination_city if d.destination}

			# Track if we added any new destinations
			added_count = 0

			# Copy destinations from package to trip
			for pkg_dest in package.destinations:
				if pkg_dest.destination and pkg_dest.destination not in existing_destinations:
					self.append("destination_city", {
						"destination": pkg_dest.destination,
						"number_of_nights": pkg_dest.number_of_nights if hasattr(pkg_dest, 'number_of_nights') else None
					})
					added_count += 1
					print(f"✅ Copied destination '{pkg_dest.destination}' from package to trip")

			if added_count > 0:
				print(f"✅ Synced {added_count} destination(s) from package {self.use_standard_package} to trip {self.name}")

		except Exception as e:
			frappe.log_error(
				title="Trip Destination Sync Failed",
				message=f"Trip: {self.name}\nPackage: {self.use_standard_package}\nError: {str(e)}"
			)
			print(f"❌ Error syncing destinations from package: {str(e)}")

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
