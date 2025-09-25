"""
Authentication endpoints for CRM Users
Handles signup, login, logout, and session management
"""

import frappe
from frappe import _
from frappe.auth import LoginManager
from frappe.utils.password import check_password
import json


@frappe.whitelist(allow_guest=True)
def register(email=None, first_name=None, last_name=None, password=None, company=None):
    """
    Register a new CRM user
    Creates a Website User with CRM permissions
    """
    try:
        # Validate required fields
        if not email or not password or not first_name:
            frappe.throw(_("Email, first name, and password are required"))

        # Check if user already exists
        if frappe.db.exists("User", email):
            frappe.throw(_("An account with this email already exists"))

        # Create full name
        full_name = f"{first_name} {last_name}" if last_name else first_name

        # Create new Website User
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name or "",
            "full_name": full_name,
            "username": email,
            "user_type": "Website User",
            "enabled": 1,
            "send_welcome_email": 0,
            "new_password": password
        })

        user.flags.ignore_permissions = True
        user.flags.ignore_password_policy = True
        user.insert()

        # Add CRM User role (create if it doesn't exist)
        try:
            user.add_roles("CRM User")
        except frappe.DoesNotExistError:
            # Create CRM User role if it doesn't exist
            frappe.get_doc({
                "doctype": "Role",
                "role_name": "CRM User",
                "desk_access": 1
            }).insert(ignore_permissions=True)
            user.add_roles("CRM User")

        # Create CRM User Permission record if company specified
        if company:
            create_crm_user_permission(email, company)

        frappe.db.commit()

        # Auto-login after registration
        login_manager = LoginManager()
        login_manager.user = email
        login_manager.post_login()

        return {
            "success": True,
            "user": {
                "email": email,
                "full_name": full_name,
                "first_name": first_name,
                "last_name": last_name or "",
                "user_type": "Website User",
                "roles": ["CRM User"]
            }
        }

    except frappe.ValidationError as e:
        frappe.log_error(f"Registration validation error: {str(e)}", "CRM Registration Error")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        frappe.log_error(f"Registration error: {str(e)}", "CRM Registration Error")
        frappe.db.rollback()
        return {
            "success": False,
            "error": _("Registration failed. Please try again.")
        }


@frappe.whitelist(allow_guest=True)
def login(email=None, password=None):
    """
    Login with email and password
    Creates Frappe session for CRM access
    """
    try:
        if not email or not password:
            frappe.throw(_("Email and password are required"))

        # Use Frappe's check_password function
        try:
            user_doc = check_password(email, password)
            if not user_doc:
                frappe.throw(_("Invalid email or password"))
        except frappe.AuthenticationError:
            frappe.throw(_("Invalid email or password"))

        # Create session
        login_manager = LoginManager()
        login_manager.user = email
        login_manager.post_login()

        # Get user details
        user = frappe.get_doc("User", email)

        return {
            "success": True,
            "user": {
                "email": user.email,
                "full_name": user.full_name,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_type": user.user_type,
                "roles": [r.role for r in user.roles],
                "user_image": user.user_image
            }
        }

    except frappe.AuthenticationError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        frappe.log_error(f"Login error: {str(e)}", "CRM Login Error")
        return {
            "success": False,
            "error": _("Login failed. Please check your credentials.")
        }


@frappe.whitelist()
def logout():
    """
    Logout current user and clear session
    """
    try:
        frappe.local.login_manager.logout()
        frappe.db.commit()
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        frappe.log_error(f"Logout error: {str(e)}", "CRM Logout Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_current_user():
    """
    Get current logged-in user details
    """
    try:
        if frappe.session.user == "Guest":
            return {
                "success": False,
                "user": None,
                "is_guest": True
            }

        user = frappe.get_doc("User", frappe.session.user)

        # Get CRM specific permissions if available
        crm_permissions = get_user_crm_permissions(frappe.session.user)

        return {
            "success": True,
            "user": {
                "email": user.email,
                "full_name": user.full_name,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_type": user.user_type,
                "roles": [r.role for r in user.roles],
                "user_image": user.user_image,
                "crm_permissions": crm_permissions
            }
        }
    except Exception as e:
        frappe.log_error(f"Get current user error: {str(e)}", "CRM Auth Error")
        return {
            "success": False,
            "error": str(e),
            "user": None
        }


@frappe.whitelist(allow_guest=True)
def validate_session():
    """
    Check if current session is valid
    """
    try:
        if frappe.session.user and frappe.session.user != "Guest":
            return {
                "valid": True,
                "user": frappe.session.user,
                "session_status": "active"
            }
        return {
            "valid": False,
            "user": None,
            "session_status": "guest"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "session_status": "error"
        }


def create_crm_user_permission(email, company):
    """
    Helper function to create CRM User Permission record
    """
    try:
        # Check if CRM User Permission doctype exists
        if not frappe.db.table_exists("CRM User Permission"):
            return

        # Create permission record
        permission = frappe.get_doc({
            "doctype": "CRM User Permission",
            "user": email,
            "company": company,
            "can_read": 1,
            "can_create": 1,
            "can_write": 1,
            "can_delete": 0
        })
        permission.insert(ignore_permissions=True)

    except Exception as e:
        # Log but don't fail registration if permission creation fails
        frappe.log_error(f"Failed to create CRM permission: {str(e)}", "CRM Permission Error")


def get_user_crm_permissions(email):
    """
    Get CRM specific permissions for a user
    """
    try:
        # Check if user has CRM User role
        roles = frappe.get_roles(email)
        if "CRM User" not in roles and "System Manager" not in roles:
            return {"has_access": False}

        # Get specific CRM permissions if doctype exists
        permissions = {
            "has_access": True,
            "is_admin": "System Manager" in roles or "CRM Manager" in roles,
            "roles": roles
        }

        # Add doctype specific permissions
        if frappe.db.table_exists("CRM User Permission"):
            user_perms = frappe.get_all(
                "CRM User Permission",
                filters={"user": email},
                fields=["can_read", "can_create", "can_write", "can_delete", "company"]
            )
            if user_perms:
                permissions.update(user_perms[0])

        return permissions

    except Exception as e:
        frappe.log_error(f"Error getting CRM permissions: {str(e)}", "CRM Permission Error")
        return {"has_access": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def forgot_password(email):
    """
    Send password reset link to user email
    """
    try:
        if not email:
            frappe.throw(_("Email is required"))

        if not frappe.db.exists("User", email):
            # Don't reveal if user exists or not for security
            return {
                "success": True,
                "message": _("If an account exists with this email, you will receive a password reset link.")
            }

        user = frappe.get_doc("User", email)
        user.send_password_reset_email()

        return {
            "success": True,
            "message": _("Password reset link has been sent to your email.")
        }

    except Exception as e:
        frappe.log_error(f"Forgot password error: {str(e)}", "CRM Auth Error")
        return {
            "success": False,
            "error": _("Failed to send reset link. Please try again.")
        }


@frappe.whitelist(allow_guest=True)
def get_login_redirect_url():
    """
    Get the URL to redirect to after successful login
    Based on environment and configuration
    """
    try:
        # Check if we have a configured CRM frontend URL
        crm_frontend_url = frappe.conf.get("crm_frontend_url", "")

        if not crm_frontend_url:
            # Default URLs based on environment
            if frappe.conf.developer_mode:
                # Development environment
                crm_frontend_url = "http://localhost:8080"
            else:
                # Production - use same domain with /crm path
                site_url = frappe.utils.get_url()
                crm_frontend_url = f"{site_url}/crm"

        return {
            "success": True,
            "redirect_url": crm_frontend_url
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "redirect_url": "/crm"
        }