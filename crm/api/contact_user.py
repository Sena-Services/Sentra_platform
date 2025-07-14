import frappe
from frappe import _

@frappe.whitelist()
def get_user_for_contact(contact_name):
    """Check if a contact has an associated user account"""
    contact = frappe.get_doc("Contact", contact_name)
    
    # Check if there's a user with this email
    if contact.email_id:
        user_exists = frappe.db.exists("User", contact.email_id)
        if user_exists:
            user = frappe.get_doc("User", contact.email_id)
            return {
                "has_user": True,
                "user_email": user.name,
                "user_type": user.user_type,
                "enabled": user.enabled,
                "crm_role": user.get("crm_role"),
                "full_name": user.full_name
            }
    
    return {"has_user": False}

@frappe.whitelist()
def create_user_from_contact(contact_name, password, crm_role, work_email=None):
    """Create a Website User from a Contact (Employee type)"""
    from .user_management import get_current_user_permissions
    
    # Check permissions
    current_permissions = get_current_user_permissions()
    if not current_permissions.get("permissions", {}).get("admin", {}).get("can_manage_users"):
        frappe.throw(_("You don't have permission to create users"))
    
    contact = frappe.get_doc("Contact", contact_name)
    
    # Validate contact is an employee
    if contact.primary_type != "Employee":
        frappe.throw(_("Only Employee contacts can be converted to users"))
    
    # Determine email to use
    email = work_email or contact.email_id
    if not email:
        frappe.throw(_("Contact must have an email address"))
    
    # Check if user already exists
    if frappe.db.exists("User", email):
        frappe.throw(_("User with this email already exists"))
    
    # Extract employee info from contact
    employee_id = contact.get('employee_code') or None
    department = contact.get('department') or None
    
    # Create user
    user = frappe.new_doc("User")
    user.email = email
    user.first_name = contact.first_name or contact.full_name.split()[0]
    user.last_name = contact.last_name or (contact.full_name.split()[1] if len(contact.full_name.split()) > 1 else "")
    user.full_name = contact.full_name
    user.user_type = "Website User"
    user.enabled = 1
    user.send_welcome_email = 0
    user.new_password = password
    user.crm_role = crm_role
    
    # Add phone if available
    if contact.mobile_no:
        user.mobile_no = contact.mobile_no
    
    # Store employee info in user_tags
    tags = []
    if employee_id:
        tags.append(f"emp_id:{employee_id}")
    if department:
        tags.append(f"dept:{department}")
    if tags:
        user.user_tags = ", ".join(tags)
    
    user.insert(ignore_permissions=True)
    
    # Update contact with user link
    contact.user = email
    contact.save(ignore_permissions=True)
    
    frappe.db.commit()
    
    return {
        "success": True,
        "user": email,
        "message": "User created successfully"
    }

@frappe.whitelist()
def update_contact_user(contact_name, updates):
    """Update user settings for a contact"""
    from .user_management import get_current_user_permissions
    
    # Check permissions
    current_permissions = get_current_user_permissions()
    if not current_permissions.get("permissions", {}).get("admin", {}).get("can_manage_users"):
        frappe.throw(_("You don't have permission to manage users"))
    
    contact = frappe.get_doc("Contact", contact_name)
    
    if not contact.user:
        frappe.throw(_("Contact does not have an associated user"))
    
    user = frappe.get_doc("User", contact.user)
    
    # Update allowed fields
    if "enabled" in updates:
        user.enabled = updates["enabled"]
    
    if "crm_role" in updates:
        user.crm_role = updates["crm_role"]
    
    if "new_password" in updates and updates["new_password"]:
        user.new_password = updates["new_password"]
    
    if "crm_territory_access" in updates:
        user.crm_territory_access = updates["crm_territory_access"]
    
    if "crm_team_members" in updates:
        user.crm_team_members = updates["crm_team_members"]
    
    user.save(ignore_permissions=True)
    
    return {
        "success": True,
        "message": "User updated successfully"
    }

@frappe.whitelist()
def remove_user_access(contact_name):
    """Disable user access for a contact"""
    from .user_management import get_current_user_permissions
    
    # Check permissions
    current_permissions = get_current_user_permissions()
    if not current_permissions.get("permissions", {}).get("admin", {}).get("can_manage_users"):
        frappe.throw(_("You don't have permission to manage users"))
    
    contact = frappe.get_doc("Contact", contact_name)
    
    if not contact.user:
        frappe.throw(_("Contact does not have an associated user"))
    
    user = frappe.get_doc("User", contact.user)
    user.enabled = 0
    user.save(ignore_permissions=True)
    
    return {
        "success": True,
        "message": "User access disabled"
    }