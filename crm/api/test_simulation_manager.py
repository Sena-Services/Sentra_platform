"""
Test Simulation Manager for AI Agent Testing
Handles creation and management of test customers, messages, and conversations
"""

import frappe
import json
from datetime import datetime
import uuid
from typing import Dict, Any, List, Optional

class TestSimulationManager:
    """
    Manager class for handling test simulations of customer interactions
    """

    def __init__(self, session_id: str = None):
        """
        Initialize Test Simulation Manager

        Args:
            session_id: Unique session ID for this test session
        """
        self.session_id = session_id or self.generate_session_id()
        self.user = frappe.session.user

    @staticmethod
    def generate_session_id() -> str:
        """Generate a unique session ID for test tracking"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"TEST_{timestamp}_{unique_id}"

    def create_test_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a test customer (Contact) with test flags

        Args:
            customer_data: Dictionary containing customer details
                - name: Customer name
                - email: Email address
                - phone: Phone number
                - additional_fields: Any other Contact fields

        Returns:
            Dict with created customer details
        """
        try:
            # Prepare test customer name with TEST prefix
            test_name = f"TEST_{customer_data.get('name', 'Customer')}"

            # Generate a unique 10-digit test phone number starting with 9
            # Format: 9XXYYYYYYY where XX is random 2 digits and YYYYYYY is timestamp-based
            import random
            test_phone = customer_data.get('phone', f"9{random.randint(10, 99)}{datetime.now().strftime('%H%M%S')}")

            # Create Contact document with test flags
            contact = frappe.get_doc({
                "doctype": "Contact",
                "first_name": test_name.split()[0] if ' ' in test_name else test_name,
                "last_name": ' '.join(test_name.split()[1:]) if ' ' in test_name else '',
                # Test flags
                "is_test_customer": 1,
                "test_session_id": self.session_id,
                "test_created_by": self.user,
                **customer_data.get('additional_fields', {})
            })

            # Add phone number to the child table (required for Contact validation)
            contact.append("phone_nos", {
                "phone": test_phone,
                "is_primary_phone": 1
            })

            # Add email if provided
            if customer_data.get('email'):
                contact.append("email_ids", {
                    "email_id": customer_data.get('email'),
                    "is_primary": 1
                })

            contact.insert(ignore_permissions=True)
            frappe.db.commit()

            # Also create a Story for this test customer
            self._create_test_story(contact.name)

            return {
                "success": True,
                "customer_id": contact.name,
                "customer_name": contact.full_name or test_name,
                "email": customer_data.get('email'),
                "phone": test_phone,
                "session_id": self.session_id
            }

        except Exception as e:
            frappe.log_error(f"Error creating test customer: {str(e)}", "Test Simulation Manager")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_test_story(self, contact_name: str) -> None:
        """
        Create a test Story for the test customer

        Args:
            contact_name: Name of the Contact document
        """
        try:
            # Check if story already exists for this contact
            if frappe.db.exists("Story", contact_name):
                # Update existing story with test flags
                story = frappe.get_doc("Story", contact_name)
                story.is_test_story = 1
                story.test_session_id = self.session_id
                story.test_created_by = self.user
                story.save(ignore_permissions=True)
            else:
                # Create new story with test flags
                story = frappe.get_doc({
                    "doctype": "Story",
                    "contact": contact_name,
                    "is_test_story": 1,
                    "test_session_id": self.session_id,
                    "test_created_by": self.user,
                    "customer_stage": "welcome",
                    "story_version": "1.0"
                })
                story.insert(ignore_permissions=True)

            frappe.db.commit()

        except Exception as e:
            frappe.log_error(f"Error creating test story: {str(e)}", "Test Simulation Manager")

    def send_test_message(self, customer_id: str, message: str, channel: str = "WhatsApp") -> Dict[str, Any]:
        """
        Send a test message from customer to agent through webhook flow

        Args:
            customer_id: Contact document name
            message: Message text from customer
            channel: Communication channel (default: WhatsApp)

        Returns:
            Dict with message sending status
        """
        try:
            # Get customer details
            contact = frappe.get_doc("Contact", customer_id)

            # Get phone number from child table
            phone_number = None
            if contact.phone_nos:
                for phone in contact.phone_nos:
                    if phone.is_primary_phone:
                        phone_number = phone.phone
                        break
                if not phone_number and contact.phone_nos:
                    phone_number = contact.phone_nos[0].phone

            # If contact doesn't have a phone number, create a test one
            if not phone_number:
                import random
                test_phone = f"9{random.randint(10, 99)}{datetime.now().strftime('%H%M%S')}"
                contact.append("phone_nos", {
                    "phone": test_phone,
                    "is_primary_phone": 1
                })
                contact.save(ignore_permissions=True)
                frappe.db.commit()
                phone_number = test_phone

            # Trigger the WhatsApp webhook processing for this test message
            # We'll simulate the webhook directly with test flags
            result = self._trigger_whatsapp_webhook(contact, message, phone_number)

            return {
                "success": True,
                "message": message,
                "customer_id": customer_id,
                "session_id": self.session_id,
                "webhook_result": result
            }

        except Exception as e:
            frappe.log_error(f"Error sending test message: {str(e)}", "Test Simulation Manager")
            return {
                "success": False,
                "error": str(e)
            }

    def _trigger_whatsapp_webhook(self, contact: Any, message: str, phone_number: str = None) -> Dict[str, Any]:
        """
        Trigger WhatsApp webhook processing for test message

        Args:
            contact: Contact document
            message: Message text
            phone_number: Phone number to use for the test message

        Returns:
            Dict with processing result
        """
        try:
            # Import WhatsApp webhook handler
            from frappe_whatsapp.utils.webhook import process_messages

            # Generate a unique test message ID
            test_message_id = f"TEST_MSG_{self.session_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

            # Use provided phone number or generate a test one
            if not phone_number:
                import random
                phone_number = f"9{random.randint(10, 99)}{datetime.now().strftime('%H%M%S')}"

            # Clean phone number (remove any + prefix if present)
            clean_phone = phone_number.replace('+', '')

            # Prepare webhook payload similar to real WhatsApp with test flags
            test_payload = {
                "messages": [{
                    "from": clean_phone,
                    "id": test_message_id,
                    "timestamp": str(int(datetime.now().timestamp())),
                    "text": {
                        "body": message
                    },
                    "type": "text"
                }],
                "contacts": [{
                    "profile": {
                        "name": contact.full_name or contact.first_name
                    },
                    "wa_id": clean_phone
                }],
                # Test flags at the root level
                "is_test": True,
                "test_session_id": self.session_id,
                "test_created_by": self.user
            }

            # Process through webhook handler
            process_messages(test_payload)

            return {
                "success": True,
                "test_message_id": test_message_id
            }

        except ImportError:
            # If WhatsApp module not available, just log
            frappe.log_error("WhatsApp module not available for test processing", "Test Simulation Manager")
            return {
                "success": False,
                "error": "WhatsApp module not available"
            }
        except Exception as e:
            frappe.log_error(f"Error triggering WhatsApp processing: {str(e)}", "Test Simulation Manager")
            return {
                "success": False,
                "error": str(e)
            }

    def get_test_conversations(self, customer_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get test conversations for a customer or session

        Args:
            customer_id: Optional Contact document name
            limit: Maximum number of messages to return

        Returns:
            List of conversation messages
        """
        try:
            filters = {
                "is_test_message": 1,
                "test_session_id": self.session_id
            }

            if customer_id:
                filters["reference_name"] = customer_id
                filters["reference_doctype"] = "Contact"

            communications = frappe.get_all(
                "Communication",
                filters=filters,
                fields=["*"],
                order_by="creation DESC",
                limit=limit
            )

            # Reverse to get chronological order
            communications.reverse()

            return communications

        except Exception as e:
            frappe.log_error(f"Error getting test conversations: {str(e)}", "Test Simulation Manager")
            return []

    def cleanup_test_session(self) -> Dict[str, Any]:
        """
        Clean up all test data for this session

        Returns:
            Dict with cleanup status
        """
        try:
            # Delete test Communications
            comm_count = frappe.db.count("Communication", {
                "is_test_message": 1,
                "test_session_id": self.session_id
            })

            frappe.db.delete("Communication", {
                "is_test_message": 1,
                "test_session_id": self.session_id
            })

            # Delete test Stories
            story_count = frappe.db.count("Story", {
                "is_test_story": 1,
                "test_session_id": self.session_id
            })

            frappe.db.delete("Story", {
                "is_test_story": 1,
                "test_session_id": self.session_id
            })

            # Delete test Trips
            trip_count = frappe.db.count("Trip", {
                "is_test_trip": 1,
                "test_session_id": self.session_id
            })

            frappe.db.delete("Trip", {
                "is_test_trip": 1,
                "test_session_id": self.session_id
            })

            # Delete test Contacts
            contact_count = frappe.db.count("Contact", {
                "is_test_customer": 1,
                "test_session_id": self.session_id
            })

            frappe.db.delete("Contact", {
                "is_test_customer": 1,
                "test_session_id": self.session_id
            })

            frappe.db.commit()

            return {
                "success": True,
                "session_id": self.session_id,
                "deleted": {
                    "communications": comm_count,
                    "stories": story_count,
                    "trips": trip_count,
                    "contacts": contact_count
                }
            }

        except Exception as e:
            frappe.log_error(f"Error cleaning up test session: {str(e)}", "Test Simulation Manager")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def cleanup_all_test_data() -> Dict[str, Any]:
        """
        Clean up ALL test data across all sessions (admin function)

        Returns:
            Dict with cleanup status
        """
        try:
            # Delete all test Communications
            comm_count = frappe.db.count("Communication", {"is_test_message": 1})
            frappe.db.delete("Communication", {"is_test_message": 1})

            # Delete all test Stories
            story_count = frappe.db.count("Story", {"is_test_story": 1})
            frappe.db.delete("Story", {"is_test_story": 1})

            # Delete all test Trips
            trip_count = frappe.db.count("Trip", {"is_test_trip": 1})
            frappe.db.delete("Trip", {"is_test_trip": 1})

            # Delete all test Contacts
            contact_count = frappe.db.count("Contact", {"is_test_customer": 1})
            frappe.db.delete("Contact", {"is_test_customer": 1})

            frappe.db.commit()

            return {
                "success": True,
                "deleted": {
                    "communications": comm_count,
                    "stories": story_count,
                    "trips": trip_count,
                    "contacts": contact_count
                }
            }

        except Exception as e:
            frappe.log_error(f"Error cleaning up all test data: {str(e)}", "Test Simulation Manager")
            return {
                "success": False,
                "error": str(e)
            }

    def get_active_test_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all active test sessions for current user

        Returns:
            List of active test sessions
        """
        try:
            # Get unique test sessions
            sessions = frappe.db.sql("""
                SELECT DISTINCT
                    test_session_id,
                    MIN(creation) as started_at,
                    COUNT(*) as message_count
                FROM tabCommunication
                WHERE is_test_message = 1
                    AND test_created_by = %s
                GROUP BY test_session_id
                ORDER BY MIN(creation) DESC
            """, (self.user,), as_dict=True)

            return sessions

        except Exception as e:
            frappe.log_error(f"Error getting active test sessions: {str(e)}", "Test Simulation Manager")
            return []