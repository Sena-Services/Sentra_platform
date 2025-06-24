# import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import Contact


class CustomContact(Contact):
	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Full Name",
				"type": "Data",
				"key": "full_name",
				"width": "10rem",
			},
			{
				"label": "Primary Type",
				"type": "Link",
				"key": "primary_type",
				"width": "8rem",
			},
			{
				"label": "Secondary Type",
				"type": "Link",
				"key": "secondary_type",
				"width": "8rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email_id",
				"width": "10rem",
			},
			{
				"label": "Mobile",
				"type": "Data",
				"key": "mobile_no",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"full_name",
			"primary_type",
			"secondary_type",
			"email_id",
			"mobile_no",
			"image",
			"modified",
		]
		return {"columns": columns, "rows": rows}
