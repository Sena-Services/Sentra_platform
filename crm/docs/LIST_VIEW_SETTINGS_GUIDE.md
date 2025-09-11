# List View Settings Guide

This guide provides a comprehensive overview of Frappe's enhanced List View Settings functionality, explaining how to programmatically save and retrieve multiple, named user preferences for list views.

## Overview

Frappe's list view settings have been extended to allow storing multiple named configurations per DocType. This enables users to create and save different views with unique filters, sorting, and display options. These settings are stored in the "List View Settings" DocType and are available to all users with access to that DocType's list view.

The core of this functionality revolves around three primary functions in `frappe/desk/listview.py`:

-   `set_list_settings(doctype, settings_name, values)`: Saves or updates a named settings configuration.
-   `get_list_settings(doctype, settings_name)`: Retrieves a specific named settings configuration.
-   `get_all_list_settings(doctype)`: Retrieves all saved settings configurations for a DocType.

## Core Functions

### `set_list_settings(doctype, settings_name, values)`

This function saves or updates a named list view setting. If a setting with the given name doesn't exist, a new one is created.

-   **`doctype`**: The DocType for which to save settings (e.g., 'Contact').
-   **`settings_name`**: A unique name for the setting (e.g., 'Customers Only').
-   **`values`**: A JSON string with the settings to be saved.

### `get_list_settings(doctype, settings_name)`

Fetches a specific named list view setting.

-   **`doctype`**: The DocType for which to retrieve settings.
-   **`settings_name`**: The name of the setting to retrieve.

Returns a Document object or `None`.

### `get_all_list_settings(doctype)`

Retrieves all saved list view settings for a given DocType.

-   **`doctype`**: The DocType for which to retrieve all settings.

Returns a list of Document objects.

## Request Body Format (`values`)

The `values` parameter is a JSON string representing a dictionary of settings. Supported keys include:

| Key      | Type    | Description                            | Example                                |
|----------|---------|----------------------------------------|----------------------------------------|
| `filters`  | string  | JSON string of filter conditions       | `'[["is_customer", "=", 1]]'`          |
| `order_by` | string  | Field and sort direction               | `'modified desc'`                      |
| `fields`   | string  | JSON string of fields for display      | `'["name", "status", "lead_owner"]'`   |

## Practical Examples

### Example 1: Creating Multiple Views for Contacts

This example creates two named views for the 'Contact' DocType.

```python
# In bench console
import json
from frappe.desk.listview import set_list_settings

# 1. View for "Customers Only"
customer_settings = {
    "filters": '[["is_customer", "=", 1]]',
    "order_by": "modified desc"
}
set_list_settings('Contact', 'Customers Only', json.dumps(customer_settings))

# 2. View for "USA Suppliers"
supplier_settings = {
    "filters": '[["is_supplier", "=", 1], ["country", "=", "United States"]]',
    "order_by": "creation asc"
}
set_list_settings('Contact', 'USA Suppliers', json.dumps(supplier_settings))
```

### Example 2: Retrieving Settings

You can retrieve a specific setting by name or get all settings for a DocType.

```python
# In bench console
from frappe.desk.listview import get_list_settings, get_all_list_settings

# Get the "Customers Only" setting
customer_view = get_list_settings('Contact', 'Customers Only')
if customer_view:
    print("Filters for 'Customers Only':", customer_view.filters)

# Get all settings for 'Contact'
all_contact_views = get_all_list_settings('Contact')
print("\\nAll saved views for Contact:")
for view in all_contact_views:
    print(f"- {view.settings_name}")
```

## Testing from the Browser Console

You can also test these functions from the browser's developer console using `frappe.call`.

**Example: Create a "High-Priority Leads" view**

```javascript
frappe.call({
    method: 'frappe.desk.listview.set_list_settings',
    args: {
        doctype: 'Contact',
        settings_name: 'High-Priority Leads',
        values: JSON.stringify({
            filters: '[["is_lead", "=", 1], ["custom_priority", "=", "High"]]',
            order_by: 'modified desc'
        })
    },
    callback: function(r) {
        console.log('Settings saved:', r.message);
    }
});
```

## Important Notes

1.  **Named Settings**: Each list view setting must have a unique name for a given DocType.
2.  **DocType-wide**: Settings are available to all users with access to the DocType.
3.  **Updates**: Calling `set_list_settings` with an existing `settings_name` will overwrite the previous configuration.
4.  **UI Integration**: The Desk UI must be updated to provide a way for users to select from and manage these saved views.

## Extending for User-specific Settings

To create user-specific list view settings, you would need to:

1.  Create a custom DocType with fields for user, doctype, and the settings.
2.  Implement custom functions to save and retrieve settings based on the current user.
3.  Update the frontend to call your custom functions instead of the standard ones.

## Related Files

-   **Main Functions**: `/home/arvis/sentra_bench/apps/frappe/frappe/desk/listview.py`
-   **DocType Definition**: `/home/arvis/sentra_bench/apps/frappe/frappe/desk/doctype/list_view_settings/`
-   **Tests**: `/home/arvis/sentra_bench/apps/frappe/frappe/tests/test_listview.py`