# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Ticket(Document):
	def validate(self):
		"""Validate ticket before saving"""
		# Auto-resolve if status changed to Resolved
		if self.ticket_status == "Resolved" and not self.resolved_at:
			self.resolved_at = frappe.utils.now_datetime()

	def before_save(self):
		"""Before save hook"""
		# Clear resolved_at if status changed back to Not Resolved or Processing
		if self.ticket_status in ["Not Resolved", "Processing"] and self.resolved_at:
			self.resolved_at = None

	def after_insert(self):
		"""
		Triggered immediately after a new ticket is created.
		Automatically processes the ticket using the Ticket Processor Agent.
		"""
		print(f"\n{'='*80}")
		print(f"🎫 NEW TICKET CREATED: {self.name}")
		print(f"   Contact: {self.contact} ({self.contact_name})")
		print(f"   Request Type: {self.request_type}")
		print(f"   Status: {self.ticket_status}")
		print(f"{'='*80}\n")

		# Only process if status is "Not Resolved"
		if self.ticket_status != "Not Resolved":
			print(f"⏭️ Skipping auto-processing - status is {self.ticket_status}")
			return

		# Process ticket asynchronously to avoid blocking the creation
		frappe.enqueue(
			method="frappe_whatsapp.agents.ticket_processor_agent.process_ticket",
			queue="default",
			timeout=300,  # 5 minutes timeout
			is_async=True,
			ticket_id=self.name
		)

		print(f"✅ Ticket processing job queued for {self.name}")
