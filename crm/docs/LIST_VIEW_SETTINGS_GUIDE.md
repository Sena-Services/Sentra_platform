# List View Settings Guide

This guide provides a comprehensive overview of Frappe's List View Settings functionality, explaining how to programmatically save and retrieve user preferences for list views, including sorting, filtering, and display options.

## Overview

Frappe provides a built-in mechanism to store and manage settings for list views on a per-DocType basis. These settings are saved in a dedicated DocType called "List View Settings" and apply to all users who have access to that DocType's list view.

The core of this functionality revolves around two primary functions located in `frappe/desk/listview.py`:

-   `get_list_settings(doctype)`: Retrieves the saved settings for a specific DocType.
-   `set_list_settings(doctype, values)`: Saves or updates the settings for a specific DocType.

## Core Functions

### `get_list_settings(doctype)`

This function fetches the saved list view settings for a given DocType.

**Parameters:**

-   `doctype` (string): The name of the DocType for which to retrieve settings (e.g., 'Contact').

**Returns:**

A Document object containing the saved settings, or `None` if no settings have been saved for that DocType.

### `set_list_settings(doctype, values)`

This function saves or updates the list view settings for a specific DocType. If a settings document for the given DocType doesn't exist, a new one is created. Otherwise, the existing document is updated with the new values.

**Parameters:**

-   `doctype` (string): The name of the DocType for which to save settings (e.g., 'Lead').
-   `values` (JSON string): A JSON string containing the settings to be saved.

## Request Body Format (`values`)

The `values` parameter must be a JSON string that represents a dictionary of settings. The following keys are supported:

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `filters` | string | JSON string with filter conditions array | `'[["status", "=", "Open"]]'` |
| `order_by` | string | Field and sort direction | `'modified desc'` |
| `fields` | string | JSON string with fields array for display | `'["name", "status", "lead_owner"]'` |
| `disable_count` | boolean | Disable record count display | `true` |
| `disable_auto_refresh` | boolean | Disable automatic list refresh | `true` |
| `disable_comment_count` | boolean | Disable comment count display | `true` |
| `disable_sidebar_stats` | boolean | Disable sidebar statistics | `true` |
| `total_fields` | integer | Maximum fields to display | `8` |

### Filter Format

Filters must be provided as a JSON string containing an array of arrays, where each inner array represents a filter condition in the format `[field, operator, value]`.

**Examples:**

-   **Single Filter:** `'[["status", "=", "Open"]]'`
-   **Multiple Filters:** `'[["status", "=", "Open"], ["priority", "=", "High"]]'`
-   **Complex Filters:** `'[["creation", ">", "2024-01-01"], ["status", "!=", "Closed"]]'`

## Practical Examples

### Example 1: Simple Filter and Sort on Contact

This example sets the default filter for the 'Contact' list view to show only 'Lead' type contacts and sorts them by their creation date.

```python
# In bench console
import json
from frappe.desk.listview import set_list_settings, get_list_settings

# Define the settings
contact_settings = {
    "filters": '[["contact_type", "=", "Lead"]]',
    "order_by": "creation asc"
}

# Save the settings
set_list_settings('Contact', json.dumps(contact_settings))

# Verify the settings
saved_settings = get_list_settings('Contact')
print("Saved filters:", saved_settings.filters)
print("Saved order by:", saved_settings.order_by)
```

**Verifiable Result:**

Navigate to the 'Contact' list view in the UI. You will observe that the view is now filtered by "Contact Type = Lead" and sorted by "creation" in ascending order.

### Example 2: Advanced Settings on Lead

This example demonstrates setting multiple properties at once for the 'CRM Lead' DocType, including filters, fields, and disabling UI elements.

```python
# In bench console
import json
from frappe.desk.listview import set_list_settings, get_list_settings

# Define the settings
lead_settings = {
    "filters": '[["status", "=", "New"], ["priority", "=", "High"]]',
    "fields": '["name", "lead_name", "status", "priority", "lead_owner"]',
    "order_by": "modified desc",
    "disable_count": True,
    "disable_auto_refresh": True
}

# Save the settings
set_list_settings('CRM Lead', json.dumps(lead_settings))

# Verify the settings
saved_settings = get_list_settings('CRM Lead')
print("Saved settings for CRM Lead:", saved_settings.as_dict())
```

**Verifiable Result:**

Navigate to the 'CRM Lead' list view. You will see that:
-   The view is filtered by "Status = New" and "Priority = High".
-   The displayed columns are "name", "lead_name", "status", "priority", and "lead_owner".
-   The list is sorted by the last modified date in descending order.
-   The record count and auto-refresh functionality are disabled.

## Testing from the Browser Console

You can also test these functions directly from your browser's developer console.

1.  Open your Frappe instance in the browser and log in.
2.  Open the developer console (usually by pressing F12).
3.  Use the `frappe.call` method to interact with the functions.

**Example: Set settings for the 'ToDo' DocType**

```javascript
frappe.call({
    method: 'frappe.desk.listview.set_list_settings',
    args: {
        doctype: 'ToDo',
        values: JSON.stringify({
            filters: '[["status", "=", "Open"]]',
            order_by: 'priority desc'
        })
    },
    callback: function(r) {
        console.log('Settings saved:', r.message);
        // Now, get the settings to verify
        frappe.call({
            method: 'frappe.desk.listview.get_list_settings',
            args: {
                doctype: 'ToDo'
            },
            callback: function(r) {
                console.log('Saved settings:', r.message);
            }
        });
    }
});
```

**Verifiable Result:**

Go to the 'ToDo' list view. You will see that the list is filtered by "Status = Open" and sorted by priority in descending order.

## Important Notes

1.  **DocType-wide Settings**: These settings apply to all users viewing the DocType, not individual users.
2.  **Automatic Creation**: A "List View Settings" document is created automatically when settings are saved for the first time for a DocType.
3.  **Updates**: Calling `set_list_settings` on a DocType with existing settings will update them with the new values.
4.  **Persistence**: Settings are stored in the database and persist across sessions.
5.  **User-specific Settings**: For user-specific preferences, you would need to create a custom solution.

## Extending for User-specific Settings

To create user-specific list view settings, you would need to:

1.  Create a custom DocType with fields for user, doctype, and the settings.
2.  Implement custom functions to save and retrieve settings based on the current user.
3.  Update the frontend to call your custom functions instead of the standard ones.

## Related Files

-   **Main Functions**: `/home/arvis/sentra_bench/apps/frappe/frappe/desk/listview.py`
-   **DocType Definition**: `/home/arvis/sentra_bench/apps/frappe/frappe/desk/doctype/list_view_settings/`
-   **Tests**: `/home/arvis/sentra_bench/apps/frappe/frappe/tests/test_listview.py`