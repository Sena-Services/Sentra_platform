# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.model.document import Document
from frappe.utils import has_gravatar, validate_email_address

from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
	add_status_change_log,
)


class CRMLead(Document):
	

	def validate(self):
		self.set_full_name()
		self.set_lead_name()
		self.set_title()
		self.validate_email()
		if not self.is_new() and self.has_value_changed("lead_owner") and self.lead_owner:
			self.share_with_agent(self.lead_owner)
			self.assign_agent(self.lead_owner)
		if self.has_value_changed("status"):
			add_status_change_log(self)

	def after_insert(self):
		if self.lead_owner:
			self.assign_agent(self.lead_owner)

		self.create_contact(throw=False)

	def on_update(self):
		"""Update contact when lead details change"""
		frappe.logger().info(f"🔄 on_update() called for lead {self.name}")
		self.sync_contact_on_lead_update()

	def sync_contact_on_lead_update(self):
		"""Sync contact information when lead fields change"""
		frappe.logger().info(f"📋 sync_contact_on_lead_update() started for lead {self.name}")
		
		# Fields to monitor for changes
		sync_fields = ["email", "mobile_no", "first_name", "last_name", "gender", "instagram_id"]
		
		# Check if any of the sync fields have changed
		changed_fields = []
		for field in sync_fields:
			if self.has_value_changed(field):
				old_value = self.get_value_before_save(field)
				new_value = self.get(field)
				frappe.logger().info(f"🔥 Field '{field}' changed: '{old_value}' → '{new_value}'")
				changed_fields.append(field)
		
		frappe.logger().info(f"📝 Changed fields: {changed_fields}")
		
		if not changed_fields:
			frappe.logger().info("⚠️ No relevant fields changed, skipping contact sync")
			return  # No relevant fields changed
		
		# Find associated contact
		contact = self.get_associated_contact()
		frappe.logger().info(f"🔍 Found associated contact: {contact}")
		
		if not contact:
			frappe.logger().info("❌ No associated contact found, cannot sync")
			return  # No contact to update
		
		try:
			frappe.logger().info(f"📋 Loading contact document: {contact}")
			contact_doc = frappe.get_doc("Contact", contact)
			
			# Update basic contact fields
			if "first_name" in changed_fields:
				frappe.logger().info(f"👤 Updating first_name: {contact_doc.first_name} → {self.first_name}")
				contact_doc.first_name = self.first_name
			if "last_name" in changed_fields:
				frappe.logger().info(f"👤 Updating last_name: {contact_doc.last_name} → {self.last_name}")
				contact_doc.last_name = self.last_name
			if "gender" in changed_fields:
				frappe.logger().info(f"👤 Updating gender: {contact_doc.gender} → {self.gender}")
				contact_doc.gender = self.gender
			
			# Update instagram ID if changed (requires custom field in Contact)
			if "instagram_id" in changed_fields and self.instagram_id:
				frappe.logger().info(f"📷 Updating instagram_id: {getattr(contact_doc, 'instagram_id', 'N/A')} → {self.instagram_id}")
				contact_doc.instagram_id = self.instagram_id
			
			# Update email if changed
			if "email" in changed_fields and self.email:
				frappe.logger().info(f"📧 Calling update_contact_email()")
				self.update_contact_email(contact_doc)
			
			# Update mobile number if changed
			if "mobile_no" in changed_fields and self.mobile_no:
				frappe.logger().info(f"📱 Calling update_contact_mobile()")
				self.update_contact_mobile(contact_doc)
			
			# Save the contact
			frappe.logger().info(f"💾 Saving contact {contact}")
			contact_doc.save(ignore_permissions=True)
			frappe.logger().info(f"✅ Contact {contact} saved successfully")
			frappe.msgprint(f"Contact {contact} updated with lead changes")
			
		except Exception as e:
			frappe.logger().error(f"❌ Error syncing contact: {str(e)}")
			frappe.log_error(f"Failed to sync contact {contact} for lead {self.name}: {str(e)}")

	def get_associated_contact(self):
		"""Find the contact associated with this lead through email, mobile, or instagram"""
		frappe.logger().info(f"🔎 Looking for contact associated with lead {self.name}")
		frappe.logger().info(f"📧 Lead email: {self.email}")
		frappe.logger().info(f"📱 Lead mobile: {self.mobile_no}")
		
		# Find by email
		if self.email:
			email_contact = frappe.db.get_value("Contact Email", {"email_id": self.email}, "parent")
			frappe.logger().info(f"📧 Email search result: {email_contact}")
			if email_contact:
				return email_contact
		
		# Find by mobile number
		if self.mobile_no:
			mobile_contact = frappe.db.get_value("Contact Phone", {"phone": self.mobile_no}, "parent")
			frappe.logger().info(f"📱 Mobile search result: {mobile_contact}")
			if mobile_contact:
				return mobile_contact
		
		# Find by Instagram ID (if you add this to Contact later)
		if self.instagram_id:
			instagram_contact = frappe.db.get_value("Contact", {"instagram_id": self.instagram_id}, "name")
			frappe.logger().info(f"📷 Instagram search result: {instagram_contact}")
			if instagram_contact:
				return instagram_contact
		
		frappe.logger().info("❌ No contact found through any method")
		return None

	def update_contact_email(self, contact_doc):
		"""Update contact's email information"""
		# Find existing email entry
		existing_email = None
		for email_row in contact_doc.email_ids:
			if email_row.email_id == self.get_value_before_save("email"):
				existing_email = email_row
				break
		
		if existing_email:
			# Update existing email
			existing_email.email_id = self.email
		else:
			# Add new email entry
			contact_doc.append("email_ids", {
				"email_id": self.email,
				"is_primary": 1 if not contact_doc.email_ids else 0
			})

	def update_contact_mobile(self, contact_doc):
		"""Update contact's mobile number information"""
		old_mobile = self.get_value_before_save("mobile_no")
		new_mobile = self.mobile_no
		frappe.logger().info(f"📱 update_contact_mobile() - Old: '{old_mobile}' → New: '{new_mobile}'")
		
		# Find existing mobile entry
		existing_mobile = None
		frappe.logger().info(f"📞 Contact has {len(contact_doc.phone_nos)} phone entries")
		
		for phone_row in contact_doc.phone_nos:
			frappe.logger().info(f"📞 Checking phone entry: {phone_row.phone}")
			if phone_row.phone == old_mobile:
				existing_mobile = phone_row
				frappe.logger().info(f"✅ Found matching phone entry to update")
				break
		
		if existing_mobile:
			# Update existing mobile
			frappe.logger().info(f"🔄 Updating existing mobile from '{existing_mobile.phone}' to '{new_mobile}'")
			existing_mobile.phone = new_mobile
		else:
			# Add new mobile entry
			frappe.logger().info(f"➕ Adding new mobile entry: '{new_mobile}'")
			contact_doc.append("phone_nos", {
				"phone": new_mobile,
				"is_primary_mobile_no": 1 if not any(p.get("is_primary_mobile_no") for p in contact_doc.phone_nos) else 0
			})
	
	def set_full_name(self):
		if self.first_name:
			self.lead_name = " ".join(
				filter(
					None,
					[
						self.first_name,
						self.last_name,
					],
				)
			)

	def set_lead_name(self):
		if not self.lead_name:
			# Check for leads being created through data import
			if not self.email and not self.flags.ignore_mandatory:
				frappe.throw(_("A Lead requiresa person's name"))
			elif self.email:
				self.lead_name = self.email.split("@")[0]
			else:
				self.lead_name = "Unnamed Lead"

	def set_title(self):
		self.title = self.lead_name

	def validate_email(self):
		if self.email:
			if not self.flags.ignore_email_validation:
				validate_email_address(self.email, throw=True)

			if self.email == self.lead_owner:
				frappe.throw(_("Lead Owner cannot be same as the Lead Email Address"))

			if self.is_new() or not self.image:
				self.image = has_gravatar(self.email)

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					# the agent is already set as an assignee
					return

		assign({"assign_to": [agent], "doctype": "CRM Lead", "name": self.name})

	def share_with_agent(self, agent):
		if not agent:
			return

		docshares = frappe.get_all(
			"DocShare",
			filters={"share_name": self.name, "share_doctype": self.doctype},
			fields=["name", "user"],
		)

		shared_with = [d.user for d in docshares] + [agent]

		for user in shared_with:
			if user == agent and not frappe.db.exists(
				"DocShare",
				{"user": agent, "share_name": self.name, "share_doctype": self.doctype},
			):
				frappe.share.add_docshare(
					self.doctype,
					self.name,
					agent,
					write=1,
					flags={"ignore_share_permission": True},
				)
			elif user != agent:
				frappe.share.remove(self.doctype, self.name, user)

	def create_contact(self, existing_contact=None, throw=True):
		if not self.lead_name:
			self.set_full_name()
			self.set_lead_name()

		existing_contact = existing_contact or self.contact_exists(throw)
		if existing_contact:
			self.update_lead_contact(existing_contact)
			return existing_contact

		contact = frappe.new_doc("Contact")
		contact.update(
			{
				"first_name": self.first_name or self.lead_name,
				"last_name": self.last_name,
				"gender": self.gender,
				"image": self.image or "",
			}
		)

		if self.email:
			contact.append("email_ids", {"email_id": self.email, "is_primary": 1})

		if self.mobile_no:
			contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

		contact.insert(ignore_permissions=True)
		contact.reload()  # load changes by hooks on contact

		return contact.name

	# def create_organization(self, existing_organization=None):
	# 	if not self.organization and not existing_organization:
	# 		return

	# 	existing_organization = existing_organization or frappe.db.exists(
	# 		"CRM Organization", {"organization_name": self.organization}
	# 	)
	# 	if existing_organization:
	# 		self.db_set("organization", existing_organization)
	# 		return existing_organization

	# 	organization = frappe.new_doc("CRM Organization")
	# 	organization.update(
	# 		{
	# 			"organization_name": self.organization,
	# 			"website": self.website,
	# 			"territory": self.territory,
	# 			"industry": self.industry,
	# 			"annual_revenue": self.annual_revenue,
	# 		}
	# 	)
	# 	organization.insert(ignore_permissions=True)
	# 	return organization.name

	def update_lead_contact(self, contact):
		contact = frappe.get_cached_doc("Contact", contact)
		frappe.db.set_value(
			"CRM Lead",
			self.name,
			{
				"first_name": contact.first_name,
				"last_name": contact.last_name,
				"email": contact.email_id,
				"mobile_no": contact.mobile_no,
				"instagram_id": contact.instagram_id,
			},
		)

	def contact_exists(self, throw=True):
		email_exist = frappe.db.exists("Contact Email", {"email_id": self.email})
		mobile_exist = frappe.db.exists("Contact Phone", {"phone": self.mobile_no})
		# Add instagram_id

		doctype = "Contact Email" if email_exist else "Contact Phone"
		name = email_exist or mobile_exist

		if name:
			text = "Email" if email_exist else "Mobile No"
			data = self.email if email_exist else self.mobile_no

			value = "{0}: {1}".format(text, data)

			contact = frappe.db.get_value(doctype, name, "parent")

			if throw:
				frappe.throw(
					_("Contact already exists with {0}").format(value),
					title=_("Contact Already Exists"),
				)
			return contact

		return False

	def create_deal(self, contact, deal=None):
		new_deal = frappe.new_doc("CRM Deal")

		lead_deal_map = {
			"lead_owner": "deal_owner",
		}

		restricted_fieldtypes = [
			"Tab Break",
			"Section Break",
			"Column Break",
			"HTML",
			"Button",
			"Attach",
		]
		restricted_map_fields = [
			"name",
			"naming_series",
			"creation",
			"owner",
			"modified",
			"modified_by",
			"idx",
			"docstatus",
			"status",
			"email",
			"mobile_no",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"communication_status",
			"status_change_log",
		]

		for field in self.meta.fields:
			if field.fieldtype in restricted_fieldtypes:
				continue
			if field.fieldname in restricted_map_fields:
				continue

			fieldname = field.fieldname
			if field.fieldname in lead_deal_map:
				fieldname = lead_deal_map[field.fieldname]

			if hasattr(new_deal, fieldname):
				new_deal.update({fieldname: self.get(field.fieldname)})

		new_deal.update(
			{
				"lead": self.name,
				"contacts": [{"contact": contact}],
			}
		)

		if self.first_responded_on:
			new_deal.update(
				{
					"sla_creation": self.sla_creation,
					"response_by": self.response_by,
					"sla_status": self.sla_status,
					"communication_status": self.communication_status,
					"first_response_time": self.first_response_time,
					"first_responded_on": self.first_responded_on,
				}
			)

		if deal:
			new_deal.update(deal)

		new_deal.insert(ignore_permissions=True)
		return new_deal.name

	# def convert_to_deal(self, deal=None):
	# 	return convert_to_deal(lead=self.name, doc=self, deal=deal)

	@staticmethod
	def get_non_filterable_fields():
		return ["converted"]

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Name",
				"type": "Data",
				"key": "lead_name",
				"width": "12rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "8rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email",
				"width": "12rem",
			},
			{
				"label": "Mobile No",
				"type": "Data",
				"key": "mobile_no",
				"width": "11rem",
			},
			{
				"label": "Assigned To",
				"type": "Text",
				"key": "_assign",
				"width": "10rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"lead_name",
			"status",
			"email",
			"mobile_no",
			"lead_owner",
			"first_name",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"modified",
			"_assign",
			"image",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "lead_name",
			"kanban_fields": '["email", "mobile_no", "_assign", "modified"]',
		}


# @frappe.whitelist()
# def convert_to_deal(lead, doc=None, deal=None, existing_contact=None, existing_organization=None):
# 	if not (doc and doc.flags.get("ignore_permissions")) and not frappe.has_permission(
# 		"CRM Lead", "write", lead
# 	):
# 		frappe.throw(_("Not allowed to convert Lead to Deal"), frappe.PermissionError)

# 	lead = frappe.get_cached_doc("CRM Lead", lead)
# 	if frappe.db.exists("CRM Lead Status", "Qualified"):
# 		lead.db_set("status", "Qualified")
# 	lead.db_set("converted", 1)
# 	if lead.sla and frappe.db.exists("CRM Communication Status", "Replied"):
# 		lead.db_set("communication_status", "Replied")
# 	contact = lead.create_contact(existing_contact, False)
# 	organization = lead.create_organization(existing_organization)
# 	_deal = lead.create_deal(contact, organization, deal)
# 	return _deal
