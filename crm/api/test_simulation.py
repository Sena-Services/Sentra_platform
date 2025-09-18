"""
API endpoints for AI Agent Test Simulation
"""

import frappe
from typing import Dict, Any
from crm.api.test_simulation_manager import TestSimulationManager

@frappe.whitelist()
def create_test_session() -> Dict[str, Any]:
    """
    Create a new test simulation session

    Returns:
        Dict with session details
    """
    try:
        manager = TestSimulationManager()
        return {
            "success": True,
            "session_id": manager.session_id,
            "user": manager.user,
            "message": "Test session created successfully"
        }
    except Exception as e:
        frappe.log_error(f"Error creating test session: {str(e)}", "Test Simulation API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def create_test_customer(
    name: str,
    email: str = None,
    phone: str = None,
    session_id: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test customer for simulation

    Args:
        name: Customer name
        email: Customer email (optional)
        phone: Customer phone (optional)
        session_id: Test session ID (optional, creates new if not provided)
        **kwargs: Additional customer fields

    Returns:
        Dict with created customer details
    """
    try:
        manager = TestSimulationManager(session_id=session_id)

        customer_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "additional_fields": kwargs
        }

        result = manager.create_test_customer(customer_data)
        return result

    except Exception as e:
        frappe.log_error(f"Error creating test customer: {str(e)}", "Test Simulation API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def send_test_message(
    customer_id: str,
    message: str,
    session_id: str = None,
    channel: str = "WhatsApp",
    customer_info: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Send a test message from customer to agent

    Args:
        customer_id: Contact document name or 'auto-create' to create new
        message: Message text
        session_id: Test session ID (optional)
        channel: Communication channel (default: WhatsApp)
        customer_info: Customer info for creating new test customer

    Returns:
        Dict with message status
    """
    try:
        if not message:
            return {
                "success": False,
                "error": "Message is required"
            }

        manager = TestSimulationManager(session_id=session_id)

        # Handle auto-creation of test customer
        if customer_id == 'auto-create' or not customer_id:
            # Create a new test customer
            if not customer_info:
                customer_info = {}

            customer_data = {
                "name": customer_info.get("name", "Test Customer"),
                "email": customer_info.get("email"),
                "phone": customer_info.get("phone")
            }

            customer_result = manager.create_test_customer(customer_data)
            if not customer_result.get("success"):
                return customer_result

            customer_id = customer_result["customer_id"]

        result = manager.send_test_message(customer_id, message, channel)
        result["customer_id"] = customer_id  # Include customer ID in response
        return result

    except Exception as e:
        frappe.log_error(f"Error sending test message: {str(e)}", "Test Simulation API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_test_conversations(
    customer_id: str = None,
    session_id: str = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get test conversation history

    Args:
        customer_id: Optional Contact document name
        session_id: Test session ID
        limit: Maximum number of messages

    Returns:
        Dict with conversation messages
    """
    try:
        manager = TestSimulationManager(session_id=session_id)
        conversations = manager.get_test_conversations(customer_id, limit)

        return {
            "success": True,
            "conversations": conversations,
            "count": len(conversations),
            "session_id": manager.session_id
        }

    except Exception as e:
        frappe.log_error(f"Error getting test conversations: {str(e)}", "Test Simulation API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def cleanup_test_session(session_id: str) -> Dict[str, Any]:
    """
    Clean up all test data for a specific session

    Args:
        session_id: Test session ID to clean up

    Returns:
        Dict with cleanup status
    """
    try:
        if not session_id:
            return {
                "success": False,
                "error": "Session ID is required"
            }

        manager = TestSimulationManager(session_id=session_id)
        result = manager.cleanup_test_session()
        return result

    except Exception as e:
        frappe.log_error(f"Error cleaning up test session: {str(e)}", "Test Simulation API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def cleanup_all_test_data() -> Dict[str, Any]:
    """
    Clean up ALL test data across all sessions
    Admin function - requires appropriate permissions

    Returns:
        Dict with cleanup status
    """
    try:
        # Check if user has permission
        if "System Manager" not in frappe.get_roles():
            return {
                "success": False,
                "error": "Insufficient permissions. System Manager role required."
            }

        result = TestSimulationManager.cleanup_all_test_data()
        return result

    except Exception as e:
        frappe.log_error(f"Error cleaning up all test data: {str(e)}", "Test Simulation API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_active_test_sessions() -> Dict[str, Any]:
    """
    Get all active test sessions for current user

    Returns:
        Dict with list of active sessions
    """
    try:
        manager = TestSimulationManager()
        sessions = manager.get_active_test_sessions()

        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }

    except Exception as e:
        frappe.log_error(f"Error getting active test sessions: {str(e)}", "Test Simulation API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_test_customers(session_id: str = None) -> Dict[str, Any]:
    """
    Get all test customers for a session or all test customers

    Args:
        session_id: Optional test session ID

    Returns:
        Dict with list of test customers
    """
    try:
        filters = {"is_test_customer": 1}
        if session_id:
            filters["test_session_id"] = session_id

        customers = frappe.get_all(
            "Contact",
            filters=filters,
            fields=["name", "full_name", "first_name", "last_name", "email_id",
                   "mobile_no", "test_session_id", "creation", "test_created_by"],
            order_by="creation DESC"
        )

        return {
            "success": True,
            "customers": customers,
            "count": len(customers)
        }

    except Exception as e:
        frappe.log_error(f"Error getting test customers: {str(e)}", "Test Simulation API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def simulate_customer_message(
    customer_type: str,
    customer_data: Dict[str, Any] = None,
    message: str = None,
    session_id: str = None
) -> Dict[str, Any]:
    """
    Complete flow: Create/select customer and send message

    Args:
        customer_type: "new" or "existing"
        customer_data: Customer details if creating new
        message: Initial message to send
        session_id: Test session ID

    Returns:
        Dict with customer and message details
    """
    try:
        manager = TestSimulationManager(session_id=session_id)

        # Handle customer creation or selection
        if customer_type == "new":
            if not customer_data:
                return {
                    "success": False,
                    "error": "Customer data required for new customer"
                }

            # Create new test customer
            customer_result = manager.create_test_customer(customer_data)
            if not customer_result.get("success"):
                return customer_result

            customer_id = customer_result["customer_id"]
        else:
            # Use existing customer
            customer_id = customer_data.get("customer_id") if customer_data else None
            if not customer_id:
                return {
                    "success": False,
                    "error": "Customer ID required for existing customer"
                }

        # Send message if provided
        message_result = None
        if message:
            message_result = manager.send_test_message(customer_id, message)

        return {
            "success": True,
            "session_id": manager.session_id,
            "customer_id": customer_id,
            "customer_type": customer_type,
            "message_sent": message_result is not None,
            "message_result": message_result
        }

    except Exception as e:
        frappe.log_error(f"Error simulating customer message: {str(e)}", "Test Simulation API")
        return {
            "success": False,
            "error": str(e)
        }