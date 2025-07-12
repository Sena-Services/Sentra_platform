import frappe
from frappe import _

@frappe.whitelist()
def get_current_user_permissions():
    """Get current user's CRM permissions"""
    user_email = frappe.session.user
    
    # Get user document
    user = frappe.get_doc("User", user_email)
    
    # Check if user is a Website User with CRM role
    if user.user_type != "Website User":
        return {
            "has_access": False,
            "message": "Only Website Users can access CRM"
        }
    
    if not user.crm_role:
        return {
            "has_access": False,
            "message": "No CRM role assigned"
        }
    
    if not user.enabled:
        return {
            "has_access": False,
            "message": "User account disabled"
        }
    
    # Get role permissions
    role = frappe.get_doc("CRM Role", user.crm_role)
    
    return {
        "has_access": True,
        "user": user_email,
        "full_name": user.full_name,
        "role": user.crm_role,
        "permissions": {
            "leads": {
                "read": role.can_access_leads,
                "create": role.can_create_leads,
                "write": role.can_edit_leads,
                "delete": role.can_delete_leads
            },
            "contacts": {
                "read": role.can_access_contacts,
                "create": role.can_create_contacts,
                "write": role.can_edit_contacts,
                "delete": role.can_delete_contacts
            },
            "trips": {
                "read": role.can_access_trips,
                "create": role.can_create_trips,
                "write": role.can_edit_trips,
                "delete": role.can_delete_trips
            },
            "invoices": {
                "read": role.can_access_invoices,
                "create": role.can_create_invoices,
                "write": role.can_edit_invoices,
                "delete": role.can_delete_invoices
            },
            "admin": {
                "is_admin": role.is_admin,
                "can_manage_users": role.can_manage_users,
                "can_manage_roles": role.can_manage_roles
            }
        },
        "territory_access": user.get("crm_territory_access", ""),
        "team_members": user.get("crm_team_members", "")
    }

@frappe.whitelist()
def check_permission(doctype, permission_type):
    """Check if current user has specific permission for a doctype"""
    permissions = get_current_user_permissions()
    
    if not permissions.get("has_access"):
        return False
    
    doctype_map = {
        "CRM Lead": "leads",
        "CRM Contact": "contacts",
        "Trip": "trips",
        "Sales Invoice": "invoices"
    }
    
    resource = doctype_map.get(doctype)
    if not resource:
        return False
    
    return permissions["permissions"][resource].get(permission_type, False)

@frappe.whitelist()
def create_crm_user(email, first_name, last_name, password, role, employee_id=None, department=None, territory_access=None, team_members=None):
    """Create a new CRM user (Website User) with CRM role"""
    
    # Check if current user can manage users
    current_permissions = get_current_user_permissions()
    if not current_permissions.get("permissions", {}).get("admin", {}).get("can_manage_users"):
        frappe.throw(_("You don't have permission to manage users"))
    
    # Create Website User
    user = frappe.new_doc("User")
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.full_name = f"{first_name} {last_name}"
    user.user_type = "Website User"  # Important: No desk access
    user.enabled = 1
    user.send_welcome_email = 0  # We'll handle our own welcome email
    user.new_password = password
    user.crm_role = role
    
    # Add custom fields if provided
    if territory_access:
        user.crm_territory_access = territory_access
    if team_members:
        user.crm_team_members = team_members
        
    # Store employee info in user_tags
    if employee_id or department:
        tags = []
        if employee_id:
            tags.append(f"emp_id:{employee_id}")
        if department:
            tags.append(f"dept:{department}")
        user.user_tags = ", ".join(tags)
    
    user.insert(ignore_permissions=True)
    
    frappe.db.commit()
    
    return {
        "success": True,
        "user": email,
        "message": "User created successfully"
    }

@frappe.whitelist()
def update_user_role(user_email, new_role):
    """Update user's CRM role"""
    
    # Check permissions
    current_permissions = get_current_user_permissions()
    if not current_permissions.get("permissions", {}).get("admin", {}).get("can_manage_users"):
        frappe.throw(_("You don't have permission to manage users"))
    
    user = frappe.get_doc("User", user_email)
    user.crm_role = new_role
    user.save(ignore_permissions=True)
    
    return {
        "success": True,
        "message": f"Role updated to {new_role}"
    }

@frappe.whitelist()
def deactivate_user(user_email):
    """Deactivate a CRM user"""
    
    # Check permissions
    current_permissions = get_current_user_permissions()
    if not current_permissions.get("permissions", {}).get("admin", {}).get("can_manage_users"):
        frappe.throw(_("You don't have permission to manage users"))
    
    user = frappe.get_doc("User", user_email)
    user.enabled = 0
    user.save(ignore_permissions=True)
    
    return {
        "success": True,
        "message": "User deactivated"
    }

@frappe.whitelist()
def get_all_users():
    """Get all CRM users (for admin)"""
    
    # Check permissions
    current_permissions = get_current_user_permissions()
    if not current_permissions.get("permissions", {}).get("admin", {}).get("can_manage_users"):
        frappe.throw(_("You don't have permission to view users"))
    
    users = frappe.get_all("User",
        filters={"user_type": "Website User", "crm_role": ["!=", ""]},
        fields=["name as user", "full_name", "crm_role", "enabled as is_active", 
                "last_active as last_login", "user_tags", "crm_territory_access", 
                "crm_team_members"],
        order_by="full_name")
    
    # Parse employee info from user_tags
    for user in users:
        if user.get("user_tags"):
            tags = user["user_tags"].split(", ")
            for tag in tags:
                if tag.startswith("emp_id:"):
                    user["employee_id"] = tag.replace("emp_id:", "")
                elif tag.startswith("dept:"):
                    user["department"] = tag.replace("dept:", "")
        user.pop("user_tags", None)
    
    return users

@frappe.whitelist()
def get_all_roles():
    """Get all CRM roles (for admin)"""
    
    # Check permissions
    current_permissions = get_current_user_permissions()
    if not (current_permissions.get("permissions", {}).get("admin", {}).get("can_manage_users") or
            current_permissions.get("permissions", {}).get("admin", {}).get("can_manage_roles")):
        frappe.throw(_("You don't have permission to view roles"))
    
    roles = frappe.get_all("CRM Role",
        fields=["name", "description", "is_admin"],
        order_by="name")
    
    return roles

@frappe.whitelist(allow_guest=True)
def create_initial_admin_user(email, first_name, last_name, password):
    """Create the first admin user - only works if no CRM users exist"""
    
    # Check if any CRM users exist
    existing_crm_users = frappe.db.count("User", 
        filters={"user_type": "Website User", "crm_role": ["!=", ""]})
    
    if existing_crm_users > 0:
        frappe.throw(_("Initial admin user already exists"))
    
    # Create admin role if it doesn't exist
    if not frappe.db.exists("CRM Role", "CRM Admin"):
        admin_role = frappe.new_doc("CRM Role")
        admin_role.role_name = "CRM Admin"
        admin_role.description = "Full CRM Administrator"
        admin_role.can_access_leads = 1
        admin_role.can_create_leads = 1
        admin_role.can_edit_leads = 1
        admin_role.can_delete_leads = 1
        admin_role.can_access_contacts = 1
        admin_role.can_create_contacts = 1
        admin_role.can_edit_contacts = 1
        admin_role.can_delete_contacts = 1
        admin_role.can_access_trips = 1
        admin_role.can_create_trips = 1
        admin_role.can_edit_trips = 1
        admin_role.can_delete_trips = 1
        admin_role.can_access_invoices = 1
        admin_role.can_create_invoices = 1
        admin_role.can_edit_invoices = 1
        admin_role.can_delete_invoices = 1
        admin_role.is_admin = 1
        admin_role.can_manage_users = 1
        admin_role.can_manage_roles = 1
        admin_role.insert(ignore_permissions=True)
    
    # Create the admin user without permission check
    user = frappe.new_doc("User")
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.full_name = f"{first_name} {last_name}"
    user.user_type = "Website User"
    user.enabled = 1
    user.send_welcome_email = 0
    user.new_password = password
    user.crm_role = "CRM Admin"
    user.insert(ignore_permissions=True)
    
    frappe.db.commit()
    
    return {
        "success": True,
        "user": email,
        "message": "Admin user created successfully"
    }