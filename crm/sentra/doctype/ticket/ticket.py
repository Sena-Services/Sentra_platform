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
		Works for all platforms: WhatsApp, Instagram, and Email.
		"""
		print(f"\n{'='*80}")
		print(f"🎫 NEW TICKET CREATED: {self.name}")
		print(f"   Contact: {self.contact} ({self.contact_name})")
		print(f"   Request Type: {self.request_type}")
		print(f"   Status: {self.ticket_status}")
		print(f"   Platform: Detecting from contact...")

		# Detect platform from contact
		try:
			contact = frappe.get_doc("Contact", self.contact)
			has_phone = bool(contact.get("phone_nos"))
			has_instagram = bool(contact.get("instagram"))
			platform = "WhatsApp" if has_phone else ("Instagram" if has_instagram else "Email")
			print(f"   Platform Detected: {platform}")
		except:
			print(f"   Platform: Unknown")

		print(f"{'='*80}\n")

		# Only process if status is "Not Resolved"
		if self.ticket_status != "Not Resolved":
			print(f"⏭️ Skipping auto-processing - status is {self.ticket_status}")
			return

		# IMPORTANT: Use after_commit to ensure ticket is fully saved before queuing job
		# This prevents race conditions where worker tries to process before commit
		frappe.enqueue(
			method="frappe_whatsapp.agents.ticket_processor_agent.process_ticket",
			queue="default",
			timeout=300,  # 5 minutes timeout
			is_async=True,
			ticket_id=self.name,
			enqueue_after_commit=True  # CRITICAL: Wait for commit before queuing
		)

		print(f"✅ Ticket processing job queued for {self.name} (will execute after commit)")
