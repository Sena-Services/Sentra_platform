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
			{
				"label": "City",
				"type": "Data",
				"key": "city",
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
			"_user_tags",
			"_assign",
			"_liked_by",
			"modified",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def get_available_columns():
		"""Return only the fields that should be available in the column selector"""
		# Only include fields that are actually being populated by our frontend
		available_fields = [
			{"fieldname": "full_name", "label": "Full Name", "fieldtype": "Data"},
			{"fieldname": "first_name", "label": "First Name", "fieldtype": "Data"},
			{"fieldname": "last_name", "label": "Last Name", "fieldtype": "Data"},
			{"fieldname": "primary_type", "label": "Primary Type", "fieldtype": "Link"},
			{"fieldname": "secondary_type", "label": "Secondary Type", "fieldtype": "Link"},
			{"fieldname": "email_id", "label": "Email", "fieldtype": "Data"},
			{"fieldname": "mobile_no", "label": "Mobile", "fieldtype": "Data"},
			# {"fieldname": "phone", "label": "Phone", "fieldtype": "Data"},
			{"fieldname": "instagram", "label": "Instagram", "fieldtype": "Data"},
			{"fieldname": "dob", "label": "Date of Birth", "fieldtype": "Date"},
			{"fieldname": "notes", "label": "Notes", "fieldtype": "Long Text"},
			{"fieldname": "_user_tags", "label": "Tags", "fieldtype": "Data"},
			{"fieldname": "_assign", "label": "Assigned To", "fieldtype": "Text"},
			{"fieldname": "_liked_by", "label": "Like", "fieldtype": "Data"},
			{"fieldname": "address_line1", "label": "Address Line 1", "fieldtype": "Data"},
			{"fieldname": "city", "label": "City", "fieldtype": "Data"},
			{"fieldname": "state", "label": "State", "fieldtype": "Data"},
			{"fieldname": "country", "label": "Country", "fieldtype": "Data"},
			# {"fieldname": "organization_name", "label": "Organization Name", "fieldtype": "Data"},
			# {"fieldname": "designation", "label": "Designation", "fieldtype": "Data"},
			# {"fieldname": "company_name", "label": "Company Name", "fieldtype": "Data"},
			# {"fieldname": "gender", "label": "Gender", "fieldtype": "Link"},
			# {"fieldname": "department", "label": "Department", "fieldtype": "Data"},
			{"fieldname": "modified", "label": "Last Modified", "fieldtype": "Datetime"},
			{"fieldname": "creation", "label": "Created On", "fieldtype": "Datetime"},
			{"fieldname": "owner", "label": "Created By", "fieldtype": "Link"},
		]
		return available_fields
