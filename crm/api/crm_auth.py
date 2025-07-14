import functools
import frappe
from frappe import _

def crm_permission_required(doctype=None, permission_type="read"):
    """Decorator to check CRM permissions before executing a function"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from .user_management import check_permission, get_current_user_permissions
            
            # First check if user has CRM access at all
            permissions = get_current_user_permissions()
            if not permissions.get("has_access"):
                frappe.throw(_("No CRM access"), frappe.PermissionError)
            
            # If doctype specified, check specific permission
            if doctype:
                if not check_permission(doctype, permission_type):
                    frappe.throw(
                        _("You don't have {0} permission for {1}").format(
                            permission_type, doctype
                        ),
                        frappe.PermissionError
                    )
            
            # Execute the function
            return func(*args, **kwargs)
        return wrapper
    return decorator

def crm_admin_required(func):
    """Decorator to check if user is CRM admin"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from .user_management import get_current_user_permissions
        
        permissions = get_current_user_permissions()
        if not permissions.get("permissions", {}).get("admin", {}).get("is_admin"):
            frappe.throw(_("Admin access required"), frappe.PermissionError)
        
        return func(*args, **kwargs)
    return wrapper

def apply_crm_filters(doctype, filters=None):
    """Apply CRM-specific filters based on user permissions"""
    from .user_management import get_current_user_permissions
    
    if filters is None:
        filters = {}
    
    permissions = get_current_user_permissions()
    
    # Apply territory filters if specified
    if permissions.get("territory_access"):
        territories = [t.strip() for t in permissions["territory_access"].split(",") if t.strip()]
        if territories and doctype in ["CRM Lead", "CRM Contact"]:
            filters["territory"] = ["in", territories]
    
    # Apply team member filters if specified
    if permissions.get("team_members"):
        team_members = [m.strip() for m in permissions["team_members"].split(",") if m.strip()]
        if team_members and doctype in ["CRM Lead", "CRM Contact", "Trip"]:
            filters["owner"] = ["in", team_members + [frappe.session.user]]
    
    return filters

# Example usage in API endpoints:
"""
@frappe.whitelist()
@crm_permission_required("CRM Lead", "read")
def get_leads():
    filters = apply_crm_filters("CRM Lead")
    return frappe.get_all("CRM Lead", filters=filters, fields=["*"])

@frappe.whitelist()
@crm_permission_required("CRM Lead", "create")
def create_lead(data):
    lead = frappe.new_doc("CRM Lead")
    lead.update(data)
    lead.insert()
    return lead

@frappe.whitelist()
@crm_admin_required
def manage_users():
    # Admin only function
    pass
"""