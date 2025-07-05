# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class StandardPackage(Document):
	pass

	@staticmethod
	def default_list_data():
		"""
		Provide default list view configuration for Standard Package doctype so that
		the generic get_data helper can build column and row definitions without
		running into AttributeError.
		"""
		columns = [
			{
				"label": "Package Name",
				"type": "Data",
				"key": "package_name",
				"width": "16rem",
			},
			{
				"label": "No. of Days",
				"type": "Int",
				"key": "no_of_days",
				"width": "8rem",
			},
			{
				"label": "No. of Nights",
				"type": "Int",
				"key": "no_of_nights",
				"width": "8rem",
			},
			{
				"label": "Price",
				"type": "Currency",
				"key": "price",
				"width": "10rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "10rem",
			},
		]

		rows = [
			"name",
			"package_name",
			"no_of_days",
			"no_of_nights",
			"price",
			"modified",
		]

		return {"columns": columns, "rows": rows}
