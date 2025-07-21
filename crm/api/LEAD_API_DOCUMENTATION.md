# Lead with Requirements API Documentation

## Base URL
```
http://172.19.228.236:8000/api/method/crm.api.lead_with_requirements
```

## Authentication
All API endpoints require authentication. Use the Frappe session-based authentication by logging in first:

```javascript
// Login endpoint
POST http://172.19.228.236:8000/api/method/login
Content-Type: application/x-www-form-urlencoded

usr=your_username&pwd=your_password
```

---

## 1. Get List (Smart API)

**Endpoint:** `/api/method/crm.api.lead_with_requirements.get_list`  
**Method:** `POST`  
**Description:** Smart API that automatically optimizes performance based on your requirements. Supports both basic lead queries and complex queries with requirement data.

### Basic Usage (Lead fields only):
```json
{
  "fields": ["name", "lead_name", "status", "email", "mobile_no"],
  "filters": {
    "status": ["in", ["New", "Contacted"]]
  },
  "order_by": "creation desc",
  "limit_start": 0,
  "limit_page_length": 20
}
```

### Advanced Usage (With Requirements):
```json
{
  "fields": [
    "name", 
    "lead_name", 
    "status", 
    "requirement.title",
    "requirement.budget", 
    "requirement.departure",
    "requirement.start_date",
    "requirement.end_date"
  ],
  "filters": {
    "status": "New",
    "requirement.budget": [">", 50000],
    "requirement.departure": "Mumbai"
  },
  "order_by": "creation desc",
  "limit_start": 0,
  "limit_page_length": 20
}
```

### Response (With Requirements):
```json
{
  "message": [
    {
      "name": "CRM-LEAD-2025-00009",
      "lead_name": "Arun Vis",
      "status": "New",
      "requirement.title": "Europe Tour",
      "requirement.budget": 150000,
      "requirement.departure": "Mumbai",
      "requirement.start_date": "2025-06-01",
      "requirement.end_date": "2025-06-15"
    }
  ]
}
```

### Field Syntax:
- **Lead fields:** Use field name directly (e.g., `"name"`, `"status"`)
- **Requirement fields:** Prefix with `requirement.` (e.g., `"requirement.title"`)

### Filter Operators (For both Lead and Requirement fields):
```json
{
  "status": "New",                              // Equals
  "priority": ["!=", "Low"],                    // Not equals
  "creation": [">", "2025-01-01"],             // Greater than
  "requirement.budget": [">=", 10000],          // Requirement field filter
  "status": ["in", ["New", "Contacted"]],      // In list
  "requirement.title": ["like", "%Europe%"]    // Pattern matching on requirement
}
```

### Performance Optimization:
- ✅ **Lead-only queries:** Uses fast `frappe.get_all()` 
- ✅ **Requirement queries:** Uses optimized JOIN automatically
- 🎯 **Smart detection:** Automatically chooses best method based on fields/filters

---

## 2. Get View (Single Lead)

**Endpoint:** `/api/method/crm.api.lead_with_requirements.get_view`  
**Method:** `POST`  
**Description:** Get complete details of a single lead including all linked requirements with child tables.

### Request Body:
```json
{
  "name": "CRM-LEAD-2025-00016",
  "fields": {
    "lead": ["*"],
    "requirement": ["name", "title", "departure", "budget", "start_date", "end_date"]
  }
}
```

### Response:
```json
{
  "message": {
    "name": "CRM-LEAD-2025-00016",
    "lead_name": "Arun Vis",
    "status": "Contacted",
    "email": "check@gmail.com",
    "requirements": [
      {
        "name": "REQ-2025-00005",
        "title": "Trip for CRM-LEAD-2025-00016",
        "departure": "Mumbai",
        "budget": 50000,
        "destination_city": [
          {
            "destination": "Paris",
            "nights": 3,
            "sequence": 1
          },
          {
            "destination": "London",
            "nights": 4,
            "sequence": 2
          }
        ],
        "passenger_details": [
          {
            "passenger_type": "Adult",
            "age": 35
          },
          {
            "passenger_type": "Child",
            "age": 10
          }
        ],
        "activity": [
          {
            "activity": "Sightseeing"
          }
        ]
      }
    ],
    "_comment_count": 2,
    "_like_count": 1
  }
}
```

---

## 3. Create Lead

**Endpoint:** `/api/method/crm.api.lead_with_requirements.create`  
**Method:** `POST`  
**Description:** Create a new lead with optional requirement/trip details.

⚠️ **Important**: The `link_to_contact` field is required and must reference a valid Contact. Personal fields like `lead_name`, `email`, `first_name`, etc. will be automatically populated from the linked contact via Frappe's fetch rules.

### Request Body:
```json
{
  "doc": {
    "doctype": "CRM Lead",
    "link_to_contact": "CONTACT-ID-HERE",
    "status": "New",
    "priority": "High",
    "source": "Website",
    "notes": "Customer inquiry about tour packages",
    "service_types": [
      {
        "service_type": "Tour Package"
      }
    ]
  },
  "with_requirement": true,
  "requirement_data": {
    "doctype": "Requirement",
    "title": "Europe Summer Tour",
    "departure": "Mumbai",
    "start_date": "2025-06-01",
    "end_date": "2025-06-15",
    "budget": 150000,
    "category": "5",
    "no_of_rooms": 2,
    "destination_city": [
      {
        "destination": "Paris",
        "nights": 5,
        "sequence": 1
      },
      {
        "destination": "Rome",
        "nights": 4,
        "sequence": 2
      }
    ],
    "passenger_details": [
      {
        "passenger_type": "Adult",
        "age": 35
      },
      {
        "passenger_type": "Adult",
        "age": 32
      }
    ],
    "activity": [
      {
        "activity": "Sightseeing"
      },
      {
        "activity": "Adventure Sports"
      }
    ]
  }
}
```

---

## 4. Update Lead

**Endpoint:** `/api/method/crm.api.lead_with_requirements.update`  
**Method:** `POST`  
**Description:** Update an existing lead and optionally its requirement.

### Request Body:
```json
{
  "name": "CRM-LEAD-2025-00016",
  "doc": {
    "status": "Contacted",
    "priority": "High",
    "notes": "Customer interested in premium package"
  },
  "update_requirement": true,
  "requirement_data": {
    "name": "REQ-2025-00005",
    "budget": 200000,
    "category": "5"
  }
}
```

---

## 5. Delete Lead(s)

**Endpoint:** `/api/method/crm.api.lead_with_requirements.delete`  
**Method:** `POST`  
**Description:** Delete one or more leads along with their linked requirements.

### Request Body:
```json
{
  "names": ["CRM-LEAD-2025-00016", "CRM-LEAD-2025-00017"]
}
```

### Response:
```json
{
  "message": {
    "deleted": ["CRM-LEAD-2025-00016", "CRM-LEAD-2025-00017"]
  }
}
```

---

## 6. Bulk Actions

**Endpoint:** `/api/method/crm.api.lead_with_requirements.bulk_action`  
**Method:** `POST`  
**Description:** Perform bulk operations on multiple leads.

### Update Status:
```json
{
  "action": "update_status",
  "names": ["CRM-LEAD-2025-00016", "CRM-LEAD-2025-00017"],
  "status": "Contacted"
}
```

### Assign Owner:
```json
{
  "action": "assign_owner",
  "names": ["CRM-LEAD-2025-00016", "CRM-LEAD-2025-00017"],
  "owner": "sales@example.com"
}
```

### Update Priority:
```json
{
  "action": "update_priority",
  "names": ["CRM-LEAD-2025-00016", "CRM-LEAD-2025-00017"],
  "priority": "High"
}
```

### Response:
```json
{
  "message": {
    "success": ["CRM-LEAD-2025-00016", "CRM-LEAD-2025-00017"],
    "failed": []
  }
}
```

---

## 7. Get Count

**Endpoint:** `/api/method/crm.api.lead_with_requirements.get_count`  
**Method:** `POST`  
**Description:** Get count of leads matching filters.

### Request Body:
```json
{
  "filters": {
    "status": "New",
    "priority": "High"
  }
}
```

### Response:
```json
{
  "message": {
    "total": 25,
    "by_status": {
      "New": 25
    }
  }
}
```

---

## 8. Get Statistics

**Endpoint:** `/api/method/crm.api.lead_with_requirements.get_stats`  
**Method:** `POST`  
**Description:** Get comprehensive statistics about leads.

### Request Body:
```json
{
  "filters": {}
}
```

### Response:
```json
{
  "message": {
    "total_leads": 150,
    "total_requirements": 85,
    "avg_budget": 125000.0,
    "by_status": {
      "New": 50,
      "Contacted": 30,
      "Negotiating": 40,
      "Converted": 20,
      "Lost": 10
    },
    "by_priority": {
      "High": 60,
      "Medium": 70,
      "Low": 20
    },
    "by_source": {
      "Website": 80,
      "Referral": 40,
      "Direct": 30
    },
    "by_service_type": {
      "Tour Package": 100,
      "Hotel Booking": 30,
      "Flight Booking": 20
    },
    "conversion_rate": 13.33
  }
}
```

---

## 9. Export Data

**Endpoint:** `/api/method/crm.api.lead_with_requirements.export`  
**Method:** `POST`  
**Description:** Export leads data to CSV or Excel format.

### Request Body:
```json
{
  "fields": ["name", "lead_name", "status", "email", "mobile_no"],
  "filters": {
    "status": "New"
  },
  "file_type": "CSV"
}
```

---

## 10. Import Data

**Endpoint:** `/api/method/crm.api.lead_with_requirements.import_data`  
**Method:** `POST`  
**Description:** Import leads from file or data array.

### Request Body (with file):
```json
{
  "file_url": "/files/leads_import.csv",
  "import_type": "Insert New Records"
}
```

### Request Body (with data):
```json
{
  "data": [
    {
      "lead_name": "Jane Smith",
      "email": "jane@example.com",
      "mobile_no": "+1234567890",
      "status": "New"
    }
  ],
  "import_type": "Insert New Records"
}
```

### Response:
```json
{
  "message": {
    "name": "IMP-00001",
    "status": "Success",
    "total_rows": 10,
    "success_count": 10,
    "failed_count": 0
  }
}
```

---

## Frontend Integration Example

```javascript
// Using Axios
import axios from 'axios';

const API_BASE = 'http://172.19.228.236:8000/api/method/crm.api.lead_with_requirements';

// Create axios instance with defaults
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for session cookies
});

// Example: Get leads with requirements (using the smart get_list API)
async function getLeadsWithRequirements(page = 0, pageSize = 20) {
  try {
    const response = await api.post('.get_list', {
      fields: [
        'name',
        'lead_name',
        'status',
        'requirement.title',
        'requirement.budget'
      ],
      limit_start: page * pageSize,
      limit_page_length: pageSize
    });
    
    return response.data.message;
  } catch (error) {
    console.error('Error fetching leads:', error);
    throw error;
  }
}

// Example: Create lead with requirement
async function createLeadWithTrip(leadData, tripData) {
  try {
    const response = await api.post('.create', {
      doc: leadData,
      with_requirement: true,
      requirement_data: tripData
    });
    
    return response.data.message;
  } catch (error) {
    console.error('Error creating lead:', error);
    throw error;
  }
}
```

---

## Frontend Controller Configuration

```javascript
api: {
    baseUrl: '/api/method/crm.api.lead_with_requirements',
    endpoints: {
      list: '{baseUrl}.get_list',
      view: '{baseUrl}.get_view',
      create: '{baseUrl}.create',
      edit: '{baseUrl}.update',
      delete: '{baseUrl}.delete',
      bulk: '{baseUrl}.bulk_action',
      export: '{baseUrl}.export',
      import: '{baseUrl}.import_data',
      count: '{baseUrl}.get_count',
      stats: '{baseUrl}.get_stats'
    },
    params: {
      fields: [
        'name',
        'lead_name',
        'status',
        'email',
        'mobile_no',
        'requirement.title',
        'requirement.departure',
        'requirement.budget',
        'requirement.start_date',
        'requirement.end_date'
      ],
      limit_page_length: 20,
      order_by: 'modified desc',
    }
}
```

---

## Error Handling

All APIs return errors in this format:

```json
{
  "exception": "Error message here",
  "exc_type": "ValidationError",
  "_exc_source": "crm (app)"
}
```

Common HTTP status codes:
- `200`: Success
- `401`: Authentication required
- `403`: Permission denied
- `417`: Validation error
- `500`: Server error

---

## Notes

1. **Authentication**: Always ensure the user is logged in before making API calls
2. **JSON Strings**: When passing complex objects as parameters, they may need to be JSON stringified
3. **Permissions**: All operations respect Frappe's role-based permissions
4. **Field Names**: Use exact field names as defined in the DocType
5. **Smart Performance**: The `get_list` API automatically optimizes based on your field/filter requirements
6. **Requirement Fields**: Use dot notation (e.g., `requirement.title`) to access requirement data