import frappe
from frappe import _
import json


# Define default export fields for different doctypes
DEFAULT_EXPORT_FIELDS = {
    "Contact": [
        "name", "full_name", "first_name", "last_name", 
        "email_id", "mobile_no",
        "designation", "address_line1", "address_line2", "city", "state", "country",
        "pincode", "contact_type", "contact_category", "notes", "gender",
        "creation", "modified"
    ],
    "CRM Lead": [
        "name", "lead_name", "first_name", "last_name", 
        "email", "mobile_no", "status", "source", "service_type",
        "priority", "lead_owner", "notes",
        "creation", "modified"
    ],
    "Hotel": [
        "name", "hotel_name", "star_rating", "city", "state", "country",
        "address_line1", "address_line2", "pincode", "phone", "email", "website",
        "amenities", "description", "creation", "modified"
    ],
    "Package": [
        "name", "package_name", "destination", "duration", "category",
        "price", "description", "inclusions", "exclusions",
        "creation", "modified"
    ],
    "Activity": [
        "name", "activity_name", "destination", "category", "duration",
        "price", "description", "creation", "modified"
    ],
    "DMC": [
        "name", "contact_person", "email", "phone",
        "address_line1", "address_line2", "city", "state", "country", "specialization",
        "creation", "modified"
    ]
}


@frappe.whitelist()
def export_data(doctype, export_fields=None, filters=None, file_type="CSV"):
    """Generic export function for any doctype"""
    try:
        from frappe.core.doctype.data_import.exporter import Exporter
        
        # Validate doctype exists
        if not frappe.get_meta(doctype):
            frappe.throw(_("Invalid DocType: {0}").format(doctype))
        
        # Check permissions
        if not frappe.has_permission(doctype, "read"):
            frappe.throw(_("No permission to read {0}").format(doctype))
        
        # Use default fields if not provided
        if not export_fields:
            export_fields = {doctype: DEFAULT_EXPORT_FIELDS.get(doctype, ["name", "creation", "modified"])}
        
        # Parse filters if string
        if isinstance(filters, str):
            try:
                filters = json.loads(filters)
            except:
                filters = {}
        
        # Create exporter instance
        exporter = Exporter(
            doctype=doctype,
            export_fields=export_fields,
            export_data=True,
            export_filters=filters or {},
            file_type=file_type
        )
        
        # Build and return the response - this will trigger download
        exporter.build_response()
        # Note: build_response() directly sends the file, so we won't reach this return
        return {"success": True, "message": "Export started"}
        
    except Exception as e:
        frappe.log_error(f"Export failed: {str(e)}", "Export Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def download_template(doctype, file_type="CSV"):
    """Download import template for a doctype"""
    from frappe.core.doctype.data_import.data_import import download_template
    
    # Validate doctype
    if not frappe.get_meta(doctype):
        frappe.throw(_("Invalid DocType: {0}").format(doctype))
    
    # Check permissions
    if not frappe.has_permission(doctype, "create"):
        frappe.throw(_("No permission to create {0}").format(doctype))
    
    # Get default fields for template
    export_fields = {doctype: DEFAULT_EXPORT_FIELDS.get(doctype, ["name"])}
    
    return download_template(
        doctype=doctype,
        export_fields=export_fields,
        file_type=file_type
    )


@frappe.whitelist()
def upload_and_preview():
    """Upload and preview import file"""
    import pandas as pd
    import os
    from frappe.utils.file_manager import save_file
    
    # Handle file upload
    if not frappe.request.files:
        frappe.throw(_("No file uploaded"))
    
    file = frappe.request.files.get('file')
    if not file:
        frappe.throw(_("No file found in request"))
    
    # Save uploaded file
    file_doc = save_file(
        file.filename,
        file.read(),
        dt=None,
        dn=None,
        folder="Home/Attachments",
        is_private=1
    )
    
    file_path = frappe.get_site_path() + file_doc.file_url
    
    try:
        # Read file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            frappe.throw(_("Unsupported file format. Please use CSV or Excel files."))
        
        # Limit preview to first 5 rows
        preview_df = df.head(5)
        
        # Convert to dict format
        columns = df.columns.tolist()
        rows = []
        
        for _, row in preview_df.iterrows():
            row_dict = {}
            for col in columns:
                row_dict[col] = str(row[col]) if pd.notna(row[col]) else ""
            rows.append(row_dict)
        
        return {
            "columns": columns,
            "rows": rows,
            "file_path": file_doc.file_url,
            "total_rows": len(df)
        }
        
    except Exception as e:
        frappe.throw(_("Error processing file: {0}").format(str(e)))


@frappe.whitelist()
def start_import(doctype, file_path, field_mapping=None, import_type="Insert New Records"):
    """Start import process for any doctype"""
    
    # Validate doctype
    if not frappe.get_meta(doctype):
        frappe.throw(_("Invalid DocType: {0}").format(doctype))
    
    # Check permissions
    if not frappe.has_permission(doctype, "create"):
        frappe.throw(_("No permission to create {0}").format(doctype))
    
    # Create data import document
    data_import = frappe.new_doc("Data Import")
    data_import.reference_doctype = doctype
    data_import.import_file = file_path
    data_import.import_type = import_type
    
    if field_mapping:
        if isinstance(field_mapping, str):
            field_mapping = json.loads(field_mapping)
        data_import.template_options = json.dumps(field_mapping)
    
    data_import.save()
    
    # Start the import process in background
    frappe.enqueue(
        method="frappe.core.doctype.data_import.data_import.form_start_import",
        queue="default",
        timeout=3600,
        data_import=data_import.name
    )
    
    return {"name": data_import.name, "status": "Queued"}


@frappe.whitelist()
def get_import_status(data_import_name):
    """Get status of import process"""
    data_import = frappe.get_doc("Data Import", data_import_name)
    
    return {
        "status": data_import.status,
        "progress": getattr(data_import, 'progress', 0),
        "total_records": getattr(data_import, 'total_rows', 0),
        "success_count": getattr(data_import, 'success_count', 0),
        "error_count": getattr(data_import, 'error_count', 0),
        "error_message": getattr(data_import, 'error_message', None)
    }


@frappe.whitelist()
def get_field_options(doctype):
    """Get available fields for a doctype for mapping"""
    meta = frappe.get_meta(doctype)
    
    fields = []
    for field in meta.fields:
        if field.fieldtype not in ['Section Break', 'Column Break', 'Tab Break', 'HTML']:
            fields.append({
                "label": field.label or field.fieldname,
                "value": field.fieldname,
                "fieldtype": field.fieldtype,
                "required": field.reqd
            })
    
    # Add standard fields
    standard_fields = [
        {"label": "ID", "value": "name", "fieldtype": "Data", "required": False},
        {"label": "Created On", "value": "creation", "fieldtype": "Datetime", "required": False},
        {"label": "Modified On", "value": "modified", "fieldtype": "Datetime", "required": False}
    ]
    
    fields.extend(standard_fields)
    
    return sorted(fields, key=lambda x: x["label"])