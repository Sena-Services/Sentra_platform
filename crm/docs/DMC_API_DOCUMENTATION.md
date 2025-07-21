# 🏢 DMC API DOCUMENTATION

**For Frontend Engineers working with Sentra CRM DMC (Destination Management Company) APIs**

## 📋 Overview

This documentation covers custom DMC APIs built for the Sentra Travel Services CRM. These APIs handle all DMC operations including CRUD operations, filtering, search, and statistics.

## 🎯 API Endpoints

### Base URL Pattern
```
/api/method/crm.sentra.api
```

### Available Endpoints

#### Core CRUD Operations
- **POST** `/api/method/crm.sentra.api.get_dmcs` - List DMCs with filtering
- **POST** `/api/method/crm.sentra.api.get_dmc` - Get single DMC
- **POST** `/api/method/crm.sentra.api.create_dmc` - Create new DMC
- **POST** `/api/method/crm.sentra.api.update_dmc` - Update existing DMC
- **POST** `/api/method/crm.sentra.api.delete_dmc` - Delete DMC

#### Specialized Queries
- **POST** `/api/method/crm.sentra.api.get_dmcs_by_city` - Get DMCs by city
- **POST** `/api/method/crm.sentra.api.get_dmcs_by_country` - Get DMCs by country
- **POST** `/api/method/crm.sentra.api.search_dmcs` - Search DMCs
- **POST** `/api/method/crm.sentra.api.get_dmc_stats` - Get DMC statistics

## 🔧 Authentication

All API calls require proper authentication headers:

```javascript
headers: {
  'Authorization': 'token your_api_key:your_api_secret',
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}
```

## 📊 DMC Data Model

### Core Fields
```javascript
{
  "name": "DMC-2025-00001",                    // Auto-generated ID
  "company_name": "Emirates Tourism LLC",      // Required
  "dmc_code": "ETL001",                        // Required, unique
  "registration_number": "123456789",
  "status": "Active",                          // Active|Inactive|Suspended|Blacklisted
  "established_year": 2015,
  "company_type": "Private Limited",
  
  // Contact Information
  "primary_contact_person": "Ahmed Al-Rashid",
  "designation": "General Manager", 
  "primary_email": "ahmed@emirates-tourism.com",  // Validated
  "primary_phone": "+971-4-123-4567",
  "secondary_contact_person": "Sarah Johnson",
  "secondary_email": "sarah@emirates-tourism.com",
  "secondary_phone": "+971-4-123-4568",
  
  // Address
  "address_line_1": "Office 2301, Burj Al Arab",  // Required
  "address_line_2": "Jumeirah Beach Road",
  "city": "Dubai",                             // Required (Link to Destination)
  "state": "Dubai",
  "country": "United Arab Emirates",           // Required (Link to Country)
  "pincode": "00000",
  "website": "https://emirates-tourism.com",
  "office_hours": "9:00 AM - 6:00 PM",
  
  // Operational Details
  "destinations_covered": "UAE, Oman, Qatar, Bahrain",
  "services_offered": "Hotel bookings, tours, transportation",
  "fleet_vehicles": "50 vehicles: sedans, SUVs, buses",
  "guide_languages": "English, Arabic, Hindi, Urdu, French",
  "specialization": "Luxury Travel, Adventure Tourism, Cultural Tours",
  
  // Financial Information
  "currency": "USD",                           // Link to Currency
  "payment_terms": "Net 30",                  // Advance|Net 30|Net 60|Net 90|50% Advance
  "commission_percentage": 12.5,
  "bank_name": "Emirates NBD",
  "bank_account": "1234567890123456",
  "ifsc_code": "EBILAEAD",
  "pan_number": "ABCDE1234F",
  "gst_number": "29ABCDE1234F1Z5",
  
  // Certifications & Insurance
  "licenses": "Tourism License: TL123456, Trade License: TR789012",
  "liability_insurance": true,
  "insurance_provider": "AXA Insurance",
  "policy_number": "POL123456789",
  "insurance_validity": "2025-12-31",
  "coverage_amount": 1000000.00,
  
  // Additional Information
  "notes": "Preferred partner for luxury segment",
  "documents": "License copy, insurance certificate uploaded"
}
```

## 🔍 API Usage Examples

### 1. Get DMCs List

```javascript
fetch('/api/method/crm.sentra.api.get_dmcs', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  body: JSON.stringify({
    filters: {
      status: 'Active',
      country: 'United Arab Emirates'
    },
    fields: [
      'name', 'company_name', 'dmc_code', 'city', 
      'primary_email', 'primary_phone', 'commission_percentage'
    ],
    order_by: 'company_name asc',
    limit_start: 0,
    limit_page_length: 20
  })
})
```

**Response:**
```javascript
{
  "message": {
    "data": [
      {
        "name": "DMC-2025-00001",
        "company_name": "Emirates Tourism LLC",
        "dmc_code": "ETL001",
        "city": "Dubai",
        "primary_email": "ahmed@emirates-tourism.com",
        "primary_phone": "+971-4-123-4567",
        "commission_percentage": 12.5
      }
    ],
    "count": 1,
    "total_count": 25,
    "limit_start": 0,
    "limit_page_length": 20
  }
}
```

### 2. Get Single DMC

```javascript
fetch('/api/method/crm.sentra.api.get_dmc', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'DMC-2025-00001'
  })
})
```

### 3. Create New DMC

```javascript
fetch('/api/method/crm.sentra.api.create_dmc', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    dmc_data: {
      company_name: 'Al Haramain Tourism',
      dmc_code: 'AHT001',
      city: 'Abu Dhabi',
      country: 'United Arab Emirates',
      address_line_1: '123 Sheikh Zayed Road',
      status: 'Active',
      primary_email: 'info@alharamain.com',
      primary_phone: '+971-2-555-0123',
      specialization: 'Religious Tourism, Cultural Tours',
      commission_percentage: 10.0,
      payment_terms: 'Net 30'
    }
  })
})
```

### 4. Update DMC

```javascript
fetch('/api/method/crm.sentra.api.update_dmc', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'DMC-2025-00001',
    dmc_data: {
      commission_percentage: 15.0,
      payment_terms: 'Net 60',
      status: 'Active'
    }
  })
})
```

### 5. Search DMCs

```javascript
fetch('/api/method/crm.sentra.api.search_dmcs', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'emirates tourism',
    filters: {
      status: 'Active',
      country: 'United Arab Emirates'
    },
    limit: 10
  })
})
```

### 6. Get DMCs by City

```javascript
fetch('/api/method/crm.sentra.api.get_dmcs_by_city', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    city: 'Dubai',
    filters: {
      commission_percentage: ['>=', 10]
    },
    limit: 25
  })
})
```

### 7. Get DMC Statistics

```javascript
fetch('/api/method/crm.sentra.api.get_dmc_stats', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
})
```

**Response:**
```javascript
{
  "message": {
    "total_dmcs": 45,
    "active_dmcs": 42,
    "by_country": {
      "United Arab Emirates": 28,
      "Saudi Arabia": 8,
      "Qatar": 4,
      "Bahrain": 3,
      "Oman": 2
    },
    "by_city": {
      "Dubai": 15,
      "Abu Dhabi": 8,
      "Riyadh": 6,
      "Doha": 4,
      "Sharjah": 3
    },
    "by_specialization": {
      "Luxury Travel": 18,
      "Adventure Tourism": 12,
      "Cultural Tourism": 8,
      "Religious Tourism": 5,
      "Other": 2
    }
  }
}
```

## 🎛️ Filter Options

### Common Filters
```javascript
{
  // Status filters
  status: 'Active',
  status: ['in', ['Active', 'Suspended']],
  
  // Location filters
  city: 'Dubai',
  country: 'United Arab Emirates',
  city: ['in', ['Dubai', 'Abu Dhabi']],
  
  // Business filters
  company_type: 'Private Limited',
  established_year: ['>', 2010],
  
  // Financial filters
  commission_percentage: ['>=', 10],
  commission_percentage: ['between', [10, 20]],
  payment_terms: 'Net 30',
  
  // Insurance filters
  liability_insurance: 1,
  insurance_validity: ['>', '2025-01-01'],
  
  // Date filters
  creation: ['>', '2025-01-01'],
  modified: ['>', '2025-07-01']
}
```

## ⚠️ Error Handling

### Common Error Responses

#### Validation Error (400)
```javascript
{
  "exc_type": "ValidationError",
  "message": "Field 'company_name' is required"
}
```

#### Invalid Email (400)
```javascript
{
  "exc_type": "ValidationError",
  "message": "Invalid email address"
}
```

#### Not Found (404)
```javascript
{
  "exc_type": "DoesNotExistError", 
  "message": "DMC not found"
}
```

#### Duplicate Entry (409)
```javascript
{
  "exc_type": "DuplicateEntryError",
  "message": "DMC Code 'ETL001' already exists"
}
```

## 🚀 Best Practices

### 1. Email Validation
```javascript
// ✅ Good: Valid email format
{
  primary_email: "contact@company.com"
}

// ❌ Bad: Invalid email format
{
  primary_email: "invalid-email"
}
```

### 2. Efficient Querying
```javascript
// ✅ Good: Specify needed fields and reasonable limits
{
  fields: ['name', 'company_name', 'city', 'primary_email'],
  limit_page_length: 25
}

// ❌ Bad: Fetching all fields and too many records
{
  limit_page_length: 500
}
```

### 3. Status Management
```javascript
// ✅ Good: Use specific status values
{
  status: 'Active'  // Active, Inactive, Suspended, Blacklisted
}

// ❌ Bad: Invalid status
{
  status: 'Unknown'
}
```

## 🔗 Related DocTypes

### Linked DocTypes
- **Destination** (city field) - City/location information
- **Country** (country field) - Country information
- **Currency** (currency field) - Default currency

### Child Tables
- **DMC Specialization** - Multiple specialization categories

## 📝 Notes

1. **Required Fields**: company_name, dmc_code, city, country, address_line_1 are mandatory
2. **Unique Constraints**: dmc_code must be unique across all DMCs
3. **Email Validation**: Primary and secondary emails are automatically validated
4. **Status Values**: Active, Inactive, Suspended, Blacklisted
5. **Payment Terms**: Advance Payment, Net 30, Net 60, Net 90, 50% Advance
6. **Insurance Tracking**: Supports liability insurance details and validity tracking
7. **Multi-contact Support**: Primary and secondary contact information

## 🎯 Quick Reference

| Operation | Endpoint | Method | Key Parameters |
|-----------|----------|---------|---------------|
| List | `get_dmcs` | POST | filters, fields, pagination |
| Get One | `get_dmc` | POST | name |
| Create | `create_dmc` | POST | dmc_data |
| Update | `update_dmc` | POST | name, dmc_data |
| Delete | `delete_dmc` | POST | name |
| Search | `search_dmcs` | POST | query, filters |
| By City | `get_dmcs_by_city` | POST | city, filters |
| By Country | `get_dmcs_by_country` | POST | country, filters |
| Stats | `get_dmc_stats` | POST | - |