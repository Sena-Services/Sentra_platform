# List View Settings Guide

This guide explains how to use Frappe's built-in list view settings functionality to save and retrieve user preferences for sorting, filtering, and display options.

## Overview

Frappe provides two key functions in `frappe/desk/listview.py` for managing list view settings:
- `get_list_settings(doctype)` - Retrieves saved settings for a DocType
- `set_list_settings(doctype, values)` - Saves settings for a DocType

These settings are stored in the "List View Settings" DocType and are **DocType-wide** (not user-specific).

## Functions

### `get_list_settings(doctype)`
**Location:** `frappe/desk/listview.py:13`

Retrieves saved list view settings for a specific DocType.

**Parameters:**
- `doctype` (string): The DocType name to get settings for

**Returns:**
- Document object with saved settings, or `None` if no settings exist

### `set_list_settings(doctype, values)`
**Location:** `frappe/desk/listview.py:21`

Saves list view settings for a specific DocType. Creates a new "List View Settings" document if none exists, or updates the existing one.

**Parameters:**
- `doctype` (string): The DocType name to save settings for
- `values` (JSON string): Settings object containing filters, sorting, etc.

## Supported Settings

The "List View Settings" DocType supports these fields:
- `filters` - JSON array of filter conditions
- `order_by` - Sorting specification (e.g., "creation desc")
- `fields` - Column field configuration
- `disable_count` - Boolean to disable record count
- `disable_auto_refresh` - Boolean to disable auto refresh
- `disable_comment_count` - Boolean to disable comment count
- `disable_sidebar_stats` - Boolean to disable sidebar statistics
- `total_fields` - Maximum number of fields to display

## Usage Examples

### Basic Example
```python
from frappe.desk.listview import get_list_settings, set_list_settings
import json

# Save settings with filters and sorting
settings = {
    'filters': '[["User", "enabled", "=", 1]]',
    'order_by': 'creation desc'
}
set_list_settings('User', json.dumps(settings))

# Retrieve settings
saved_settings = get_list_settings('User')
if saved_settings:
    print('Filters:', saved_settings.filters)
    print('Order by:', saved_settings.order_by)
```

### Advanced Example
```python
# Save comprehensive settings
advanced_settings = {
    'filters': '[["DocType", "module", "=", "Core"]]',
    'order_by': 'modified desc',
    'disable_count': 1,
    'disable_auto_refresh': 1,
    'total_fields': '8'
}
set_list_settings('DocType', json.dumps(advanced_settings))
```

## Testing

### Console Testing
Use `bench console` to test the functionality:

```python
from frappe.desk.listview import get_list_settings, set_list_settings
import json

# Test with Contact DocType
test_settings = {
    'filters': '[["Contact", "status", "=", "Open"]]',
    'order_by': 'modified desc'
}

# Save settings
set_list_settings('Contact', json.dumps(test_settings))

# Retrieve and verify
contact_settings = get_list_settings('Contact')
print('Contact settings saved:', contact_settings.name if contact_settings else None)
print('Filters:', contact_settings.filters if contact_settings else None)
```

### Database Verification
Check if settings were saved to database:
```python
# Check existing List View Settings
existing = frappe.get_all('List View Settings', fields=['name', 'filters', 'order_by'])
print('Existing settings:', existing)
```

## Filter Format

Filters should be provided as JSON arrays in the format:
```json
[["DocType", "field", "operator", "value"]]
```

Examples:
- Single filter: `[["User", "enabled", "=", 1]]`
- Multiple filters: `[["User", "enabled", "=", 1], ["User", "user_type", "=", "System User"]]`
- Complex filters: `[["Contact", "creation", ">", "2024-01-01"], ["Contact", "status", "!=", "Disabled"]]`

## Important Notes

1. **DocType-wide Settings**: These settings apply to all users viewing the DocType, not individual users
2. **Automatic Creation**: Settings documents are created automatically when first saved
3. **Updates**: Calling `set_list_settings` on existing settings will update them
4. **Persistence**: Settings are stored in the database and persist across sessions
5. **User-specific**: For user-specific preferences, you would need to create a custom solution

## Extending for User-specific Settings

To create user-specific list view settings, you would need to:

1. Create a custom DocType with fields for user, doctype, and settings
2. Modify the save/retrieve logic to include user context
3. Update the frontend to call your custom functions instead

Example structure:
```python
# Custom user-specific settings
def set_user_list_settings(doctype, user, values):
    # Implementation for user-specific settings
    pass

def get_user_list_settings(doctype, user):
    # Implementation for user-specific retrieval
    pass
```

## Related Files

- **Main functions**: `/home/arvis/sentra_bench/apps/frappe/frappe/desk/listview.py`
- **DocType definition**: `/home/arvis/sentra_bench/apps/frappe/frappe/desk/doctype/list_view_settings/`
- **Tests**: `/home/arvis/sentra_bench/apps/frappe/frappe/tests/test_listview.py`