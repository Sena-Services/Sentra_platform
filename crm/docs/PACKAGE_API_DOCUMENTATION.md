# 📦 STANDARD PACKAGE API DOCUMENTATION

**For Frontend Engineers working with Sentra CRM Standard Package APIs**

## 📋 Overview

This documentation covers custom Standard Package APIs built for the Sentra Travel Services CRM. These APIs handle complete travel package management including CRUD operations, pricing calculations, itinerary management, and package duplication.

## 🎯 API Endpoints

### Base URL Pattern
```
/api/method/crm.sentra.api
```

### Available Endpoints

#### Core CRUD Operations
- **POST** `/api/method/crm.sentra.api.get_packages` - List packages with filtering
- **POST** `/api/method/crm.sentra.api.get_package` - Get single package with full details
- **POST** `/api/method/crm.sentra.api.create_package` - Create new package
- **POST** `/api/method/crm.sentra.api.update_package` - Update existing package
- **POST** `/api/method/crm.sentra.api.delete_package` - Delete package

#### Specialized Queries
- **POST** `/api/method/crm.sentra.api.get_active_packages` - Get currently active packages
- **POST** `/api/method/crm.sentra.api.get_packages_by_dmc` - Get packages by DMC provider
- **POST** `/api/method/crm.sentra.api.search_packages` - Search packages
- **POST** `/api/method/crm.sentra.api.get_package_stats` - Get package statistics
- **POST** `/api/method/crm.sentra.api.duplicate_package` - Duplicate an existing package

## 🔧 Authentication

All API calls require proper authentication headers:

```javascript
headers: {
  'Authorization': 'token your_api_key:your_api_secret',
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}
```

## 📊 Package Data Model

### Core Fields
```javascript
{
  "name": "PCK-2025-00001",                    // Auto-generated ID
  "package_name": "Dubai Explorer 5 Days",     // Required
  "package_code": "DXB5D",                     // Required, unique
  "status": "Active",                          // Draft|Active|Archived
  "dmc": "Contact-ID",                         // Required (Link to Contact as DMC)
  
  // Validity Period
  "valid_from": "2025-07-21",                  // Required
  "valid_to": "2026-07-21",                    // Required
  
  // Pricing
  "currency": "USD",                           // Required (Link to Currency)
  "base_cost": 800.00,                         // Required, per person
  "markup_percentage": 25.0,                   // Required
  "net_price": 1000.00,                        // Auto-calculated (read-only)
  
  // Group Information
  "min_group_size": 2,                         // Default: 1
  "max_group_size": 20,                        // Default: 10
  
                         // Table MultiSelect
  "operating_hours": "9:00 AM - 6:00 PM",
  "target_audience": [],                       // Table MultiSelect
  "exclusion_criteria": [],                    // Table MultiSelect
  
  // Content
  "description": "Complete Dubai experience...",
  "itinerary_data": {},                        // JSON field for day-wise itinerary
  "package_inclusions": [],                    // Table MultiSelect
  "package_exclusions": [],                    // Table MultiSelect
  "terms_and_conditions": "<p>Terms...</p>",   // HTML content
  "notes": "Internal notes",
  
  // Metadata
  "creation": "2025-07-21 10:00:00",
  "modified": "2025-07-21 11:00:00"
}
```

### Itinerary Data Structure (JSON)
```javascript
{
  "days": [
    {
      "day": 1,
      "title": "Arrival in Dubai",
      "activities": [
        {
          "time": "09:00",
          "activity": "Airport pickup",
          "duration": "1 hour",
          "location": "Dubai International Airport"
        },
        {
          "time": "14:00",
          "activity": "Hotel check-in",
          "duration": "30 mins",
          "location": "JBR Walk Hotel"
        }
      ],
      "meals": ["Lunch", "Dinner"],
      "accommodation": "5-star hotel at JBR"
    }
  ]
}
```

## 🔍 API Usage Examples

### 1. Get Packages List

```javascript
fetch('/api/method/crm.sentra.api.get_packages', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  body: JSON.stringify({
    filters: {
      status: 'Active',
      currency: 'USD'
    },
    fields: [
      'name', 'package_name', 'package_code', 'status',
      'dmc', 'base_cost', 'net_price', 'currency',
      'valid_from', 'valid_to'
    ],
    order_by: 'package_name asc',
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
        "name": "PCK-2025-00001",
        "package_name": "Dubai Explorer 5 Days",
        "package_code": "DXB5D",
        "status": "Active",
        "dmc": "Contact-001",
        "base_cost": 800.00,
        "net_price": 1000.00,
        "currency": "USD",
        "valid_from": "2025-07-21",
        "valid_to": "2026-07-21"
      }
    ],
    "count": 1,
    "total_count": 25,
    "limit_start": 0,
    "limit_page_length": 20
  }
}
```

### 2. Get Single Package (Full Details)

```javascript
fetch('/api/method/crm.sentra.api.get_package', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'PCK-2025-00001'
  })
})
```

### 3. Create New Package

```javascript
fetch('/api/method/crm.sentra.api.create_package', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    package_data: {
      package_name: 'Singapore Delights 4 Days',
      package_code: 'SIN4D',
      dmc: 'Contact-001',
      status: 'Draft',
      valid_from: '2025-08-01',
      valid_to: '2026-07-31',
      currency: 'USD',
      base_cost: 1200.00,
      markup_percentage: 30.0,
      min_group_size: 2,
      max_group_size: 25,
      description: 'Experience the Lion City',
      operating_hours: '8:00 AM - 8:00 PM',
      itinerary_data: {
        days: [
          {
            day: 1,
            title: 'Arrival & Marina Bay',
            activities: [
              {
                time: '14:00',
                activity: 'Check-in at Marina Bay Sands',
                duration: '1 hour'
              }
            ]
          }
        ]
      }
    }
  })
})
```

### 4. Update Package

```javascript
fetch('/api/method/crm.sentra.api.update_package', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'PCK-2025-00001',
    package_data: {
      base_cost: 850.00,
      markup_percentage: 30.0,
      status: 'Active',
      notes: 'Price updated for peak season'
    }
  })
})
```

**Note:** Net price is automatically recalculated when base_cost or markup_percentage changes.

### 5. Search Packages

```javascript
fetch('/api/method/crm.sentra.api.search_packages', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'dubai',
    filters: {
      status: 'Active'
    },
    limit: 10
  })
})
```

### 6. Get Active Packages

```javascript
fetch('/api/method/crm.sentra.api.get_active_packages', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    filters: {
      currency: 'USD'
    },
    limit: 25
  })
})
```

**Note:** Active packages are those with status='Active' AND current date is between valid_from and valid_to.

### 7. Duplicate Package

```javascript
fetch('/api/method/crm.sentra.api.duplicate_package', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'PCK-2025-00001',
    new_package_code: 'DXB5D_V2'  // Optional
  })
})
```

**Response:**
```javascript
{
  "message": {
    "name": "PCK-2025-00002",
    "package_name": "Dubai Explorer 5 Days (Copy)",
    "package_code": "DXB5D_V2",
    "status": "Draft",  // Always Draft
    // ... all other fields copied
  }
}
```

### 8. Get Package Statistics

```javascript
fetch('/api/method/crm.sentra.api.get_package_stats', {
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
    "total_packages": 50,
    "active_packages": 35,
    "draft_packages": 10,
    "archived_packages": 5,
    "by_dmc": {
      "Contact-001": 15,
      "Contact-002": 12,
      "Contact-003": 8
    },
    "price_range": {
      "min": 400.00,
      "max": 5000.00,
      "average": 1250.50
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
  status: ['in', ['Active', 'Draft']],
  
  // DMC filters
  dmc: 'Contact-001',
  
  // Currency filters
  currency: 'USD',
  
  // Date filters
  valid_from: ['<=', '2025-08-01'],
  valid_to: ['>=', '2025-08-01'],
  
  // Price filters
  base_cost: ['>', 500],
  net_price: ['between', [500, 2000]],
  
  // Group size filters
  min_group_size: ['<=', 2],
  max_group_size: ['>=', 10],
  
  // Date range filters (for active packages)
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
  "message": "Field 'package_name' is required"
}
```

#### Date Validation Error (400)
```javascript
{
  "exc_type": "ValidationError",
  "message": "Valid From date cannot be after Valid To date"
}
```

#### Not Found (404)
```javascript
{
  "exc_type": "DoesNotExistError", 
  "message": "Package not found"
}
```

#### Duplicate Entry (409)
```javascript
{
  "exc_type": "DuplicateEntryError",
  "message": "Package Code 'DXB5D' already exists"
}
```

## 🚀 Best Practices

### 1. Price Calculations
```javascript
// ✅ Good: Let the API calculate net_price
{
  base_cost: 1000.00,
  markup_percentage: 25.0
  // net_price will be auto-calculated as 1250.00
}

// ❌ Bad: Don't set net_price manually
{
  base_cost: 1000.00,
  markup_percentage: 25.0,
  net_price: 1300.00  // Will be overridden
}
```

### 2. Date Validation
```javascript
// ✅ Good: Valid date range
{
  valid_from: '2025-08-01',
  valid_to: '2026-07-31'
}

// ❌ Bad: Invalid date range
{
  valid_from: '2025-08-01',
  valid_to: '2025-07-01'  // Before valid_from
}
```

### 3. Itinerary Data
```javascript
// ✅ Good: Structured itinerary data
{
  itinerary_data: {
    days: [
      {
        day: 1,
        title: 'Day 1',
        activities: [...]
      }
    ]
  }
}

// The API will automatically stringify the JSON
```

### 4. Package Duplication
```javascript
// ✅ Good: Duplicate with unique code
{
  name: 'PCK-2025-00001',
  new_package_code: 'DXB5D_SUMMER'
}

// If no code provided, auto-generates: DXB5D_COPY, DXB5D_COPY1, etc.
```

## 🔗 Related DocTypes

### Linked DocTypes
- **Contact** (dmc field) - DMC provider information
- **Currency** (currency field) - Package pricing currency

### Child Tables
- **Operating Day** - Days of operation
- **Target Audience** - Target customer segments
- **Exclusion Criteria** - Who cannot take this package
- **Package Inclusion** - What's included
- **Package Exclusion** - What's not included
- **Daywise Plan** - Legacy day-wise itinerary (use itinerary_data instead)

## 📝 Notes

1. **Required Fields**: package_name, package_code, dmc, valid_from, valid_to, currency, base_cost, markup_percentage
2. **Unique Constraints**: package_code must be unique across all packages
3. **Automatic Calculations**: net_price = base_cost * (1 + markup_percentage/100)
4. **Status Values**: Draft, Active, Archived
5. **DMC Field**: Links to Contact DocType (not DMC DocType)
6. **Itinerary Storage**: Use the JSON itinerary_data field for flexible itinerary structure
7. **Package Validity**: Active packages must have current date within valid_from and valid_to

## 🎯 Quick Reference

| Operation | Endpoint | Method | Key Parameters |
|-----------|----------|---------|---------------|
| List | `get_packages` | POST | filters, fields, pagination |
| Get One | `get_package` | POST | name |
| Create | `create_package` | POST | package_data |
| Update | `update_package` | POST | name, package_data |
| Delete | `delete_package` | POST | name |
| Search | `search_packages` | POST | query, filters |
| Active Only | `get_active_packages` | POST | filters, limit |
| By DMC | `get_packages_by_dmc` | POST | dmc, filters |
| Duplicate | `duplicate_package` | POST | name, new_package_code |
| Stats | `get_package_stats` | POST | - |