# 🏢 CONTACT API DOCUMENTATION

**For Frontend Engineers working with Frappe CRM Contact APIs**

## 📋 Overview

This documentation covers Frappe's built-in Contact APIs, which use the standard `/api/v2/document/` REST endpoints. These APIs handle all contact operations including CRUD operations, filtering, and bulk actions.

## 🎯 API Endpoints

### Base URL Pattern
```
/api/v2/document/Contact
```

### Available Endpoints
- **GET** `/api/v2/document/Contact` - List contacts
- **GET** `/api/v2/document/Contact/{id}` - Get single contact
- **POST** `/api/v2/document/Contact` - Create contact
- **PUT** `/api/v2/document/Contact/{id}` - Update contact
- **DELETE** `/api/v2/document/Contact/{id}` - Delete contact

## 🔧 Authentication

All API calls require proper authentication headers:

```javascript
headers: {
  'Authorization': 'token your_api_key:your_api_secret',
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}
```

## 📊 Request/Response Format

### ✅ Request Body Support
Frappe's Contact APIs accept data in **both** formats:
- **Request Body (JSON)** ← **Recommended**
- URL Parameters (legacy)

### Request Body Example (Recommended):
```javascript
fetch('/api/v2/document/Contact', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  body: JSON.stringify({
    doctype: 'Contact',
    first_name: 'John',
    last_name: 'Doe',
    email_ids: [{
      email_id: 'john.doe@example.com',
      is_primary: 1
    }],
    phone_nos: [{
      phone: '+1234567890',
      is_primary_mobile_no: 1
    }]
  })
})
```

## 📋 Contact Schema

### Core Fields
```javascript
{
  // Required fields
  "doctype": "Contact",
  "first_name": "John",           // Required
  
  // Basic information
  "last_name": "Doe",
  "full_name": "John Doe",        // Auto-computed
  "gender": "Male",               // Male/Female/Other
  "date_of_birth": "1990-01-01",
  "image": "/files/profile.jpg",
  
  // Contact details (Child tables)
  "email_ids": [
    {
      "email_id": "john@example.com",
      "is_primary": 1
    }
  ],
  "phone_nos": [
    {
      "phone": "+1234567890",
      "is_primary_mobile_no": 1,
      "is_primary_phone": 0
    }
  ],
  
  // Address information
  "address_line1": "123 Main Street",
  "address_line2": "Suite 100",
  "city": "New York",
  "state": "NY",
  "country": "United States",
  "pincode": "10001",
  
  // Business information
  "company_name": "ACME Corp",
  "designation": "Software Engineer",
  "department": "Engineering",
  
  // Social media
  "instagram": "@johndoe",
  
  // Flags
  "is_primary_contact": 0,        // 1 if customer contact
  "is_billing_contact": 0,
  "disabled": 0,
  
  // System fields
  "creation": "2024-01-01 10:00:00",
  "modified": "2024-01-01 10:00:00",
  "owner": "Administrator"
}
```

## 🔍 API Operations

### 1. List Contacts
```javascript
// GET /api/v2/document/Contact
const response = await fetch('/api/v2/document/Contact?' + new URLSearchParams({
  fields: JSON.stringify(['full_name', 'email_id', 'mobile_no', 'city']),
  filters: JSON.stringify([['disabled', '=', 0]]),
  order_by: 'modified desc',
  limit_page_length: 20,
  limit_start: 0
}))
```

### 2. Get Single Contact
```javascript
// GET /api/v2/document/Contact/{id}
const contact = await fetch('/api/v2/document/Contact/CONT-000001')
const data = await contact.json()
```

### 3. Create Contact
```javascript
// POST /api/v2/document/Contact
const newContact = await fetch('/api/v2/document/Contact', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  body: JSON.stringify({
    doctype: 'Contact',
    first_name: 'Jane',
    last_name: 'Smith',
    gender: 'Female',
    email_ids: [{
      email_id: 'jane.smith@example.com',
      is_primary: 1
    }],
    phone_nos: [{
      phone: '+0987654321',
      is_primary_mobile_no: 1
    }],
    address_line1: '456 Oak Avenue',
    city: 'San Francisco',
    state: 'CA',
    country: 'United States',
    company_name: 'Tech Startup Inc',
    designation: 'Product Manager'
  })
})
```

### 4. Update Contact
```javascript
// PUT /api/v2/document/Contact/{id}
const updatedContact = await fetch('/api/v2/document/Contact/CONT-000001', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    first_name: 'John',
    last_name: 'Smith',  // Changed last name
    designation: 'Senior Software Engineer'  // Promotion!
  })
})
```

### 5. Delete Contact
```javascript
// DELETE /api/v2/document/Contact/{id}
const deleted = await fetch('/api/v2/document/Contact/CONT-000001', {
  method: 'DELETE'
})
```

## 🔍 Advanced Filtering

### Complex Filters Example
```javascript
const filters = [
  ['disabled', '=', 0],                    // Active contacts only
  ['is_primary_contact', '=', 1],          // Customer contacts
  ['city', 'like', '%New York%'],          // City contains "New York"
  ['creation', '>', '2024-01-01'],         // Created this year
  ['gender', 'in', ['Male', 'Female']]     // Specific genders
]

const response = await fetch('/api/v2/document/Contact?' + new URLSearchParams({
  filters: JSON.stringify(filters),
  fields: JSON.stringify(['full_name', 'email_id', 'city', 'creation']),
  order_by: 'creation desc'
}))
```

### Available Filter Operators
- `=` - Equals
- `!=` - Not equals
- `>`, `<`, `>=`, `<=` - Comparisons
- `like` - Contains (use `%` wildcards)
- `not like` - Does not contain
- `in` - Value in list
- `not in` - Value not in list
- `is` - Is null/empty (`is`, `set`)
- `is not` - Is not null/empty (`is not`, `set`)

## 📧 Child Tables (Email & Phone)

### Email Management
```javascript
// Adding multiple emails
{
  "email_ids": [
    {
      "email_id": "work@example.com",
      "is_primary": 1
    },
    {
      "email_id": "personal@gmail.com", 
      "is_primary": 0
    }
  ]
}
```

### Phone Management
```javascript
// Adding multiple phone numbers
{
  "phone_nos": [
    {
      "phone": "+1-555-123-4567",
      "is_primary_mobile_no": 1,
      "is_primary_phone": 0
    },
    {
      "phone": "+1-555-987-6543",
      "is_primary_mobile_no": 0,
      "is_primary_phone": 1
    }
  ]
}
```

## 🎯 Frontend Controller Integration

### Controller Configuration
```javascript
// From contactsListView.js
api: {
  baseUrl: '/api/v2/document/Contact',
  endpoints: {
    list: '{baseUrl}',              // GET /api/v2/document/Contact
    view: '{baseUrl}/{id}',         // GET /api/v2/document/Contact/{id}
    create: '{baseUrl}',            // POST /api/v2/document/Contact
    edit: '{baseUrl}/{id}',         // PUT /api/v2/document/Contact/{id}
    delete: '{baseUrl}/{id}',       // DELETE /api/v2/document/Contact/{id}
  },
  params: {
    fields: [
      'full_name', 'email_id', 'mobile_no', 'city',
      'state', 'country', 'company_name', 'designation'
    ],
    limit_page_length: 20,
    order_by: 'modified desc'
  }
}
```

## 🔐 Permissions

### Required Permissions
- **Read**: `read` permission on Contact doctype
- **Create**: `create` permission on Contact doctype  
- **Update**: `write` permission on Contact doctype
- **Delete**: `delete` permission on Contact doctype

### Permission Roles
- **All**: Read-only access
- **Sales User**: Full CRUD access
- **Sales Manager**: Full CRUD access + advanced operations

## ⚠️ Common Gotchas

### 1. Child Table Updates
When updating contacts, child tables (email_ids, phone_nos) are **replaced entirely**:

```javascript
// ❌ This will remove existing emails and add only this one
{
  "email_ids": [
    {"email_id": "new@example.com", "is_primary": 1}
  ]
}

// ✅ To add email, first GET existing contact, modify array, then PUT
const contact = await getContact('CONT-000001')
contact.email_ids.push({
  "email_id": "additional@example.com",
  "is_primary": 0
})
await updateContact('CONT-000001', contact)
```

### 2. Primary Email/Phone Logic
- Only ONE email can have `is_primary: 1`
- Only ONE phone can have `is_primary_mobile_no: 1`
- Frappe may automatically adjust if you set multiple primaries

### 3. Computed Fields
- `full_name` is auto-computed from `first_name + last_name`
- `email_id` and `mobile_no` are auto-populated from primary child records
- Don't try to manually set these computed fields

### 4. Address vs. Contact Address
- Basic address fields are directly on Contact
- For complex addresses, use separate Address doctype and link

## 🚀 Performance Tips

### 1. Field Selection
Always specify only needed fields:
```javascript
// ✅ Good - only get what you need
fields: ['full_name', 'email_id', 'mobile_no']

// ❌ Bad - fetches everything
// fields: '*'  or omitting fields parameter
```

### 2. Pagination
Use proper pagination for large datasets:
```javascript
{
  limit_page_length: 20,
  limit_start: 0    // 0, 20, 40, 60, ...
}
```

### 3. Caching
Enable caching in your frontend controller:
```javascript
cache: {
  enabled: true,
  ttl: 300000,  // 5 minutes
  keys: ['filters', 'sort', 'page']
}
```

## 📝 Error Handling

### Common Error Responses
```javascript
// 400 Bad Request - Validation error
{
  "message": "Mandatory field missing: first_name",
  "exc_type": "ValidationError"
}

// 403 Forbidden - Permission denied
{
  "message": "Not permitted to create Contact",
  "exc_type": "PermissionError"  
}

// 404 Not Found - Contact doesn't exist
{
  "message": "Contact CONT-999999 not found",
  "exc_type": "DoesNotExistError"
}

// 409 Conflict - Duplicate constraint
{
  "message": "Email already exists: duplicate@example.com",
  "exc_type": "DuplicateError"
}
```

### Error Handling Pattern
```javascript
try {
  const response = await fetch('/api/v2/document/Contact', {
    method: 'POST',
    body: JSON.stringify(contactData)
  })
  
  if (!response.ok) {
    const error = await response.json()
    console.error('API Error:', error.message)
    // Handle specific error types
    switch (error.exc_type) {
      case 'ValidationError':
        // Show form validation errors
        break
      case 'PermissionError': 
        // Redirect to login or show permission error
        break
      case 'DuplicateError':
        // Show duplicate warning
        break
      default:
        // Generic error handling
    }
  }
  
  const contact = await response.json()
  console.log('Contact created:', contact)
  
} catch (error) {
  console.error('Network error:', error)
}
```

## 🔗 Related Documentation

- [Frappe REST API Guide](https://docs.frappe.io/framework/user/en/api/rest)
- [Contact DocType Schema](https://github.com/frappe/frappe/blob/develop/frappe/contacts/doctype/contact/contact.json)
- [CRM Lead API Documentation](./LEAD_API_DOCUMENTATION.md)
- [Frontend Controller Pattern](../frontend/src/controllers/readListViewContactsController.js)

---

*This documentation is for the Sentra CRM frontend team. For backend API development, see the Frappe Framework documentation.*