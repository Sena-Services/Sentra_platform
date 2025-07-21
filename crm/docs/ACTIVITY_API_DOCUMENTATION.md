# 🏃‍♂️ ACTIVITY API DOCUMENTATION

**For Frontend Engineers working with Sentra CRM Activity APIs**

## 📋 Overview

This documentation covers custom Activity APIs built for the Sentra Travel Services CRM. These APIs handle all activity operations including CRUD operations, filtering, search, and statistics.

## 🎯 API Endpoints

### Base URL Pattern
```
/api/method/crm.sentra.api
```

### Available Endpoints

#### Core CRUD Operations
- **POST** `/api/method/crm.sentra.api.get_activities` - List activities with filtering
- **POST** `/api/method/crm.sentra.api.get_activity` - Get single activity
- **POST** `/api/method/crm.sentra.api.create_activity` - Create new activity
- **POST** `/api/method/crm.sentra.api.update_activity` - Update existing activity
- **POST** `/api/method/crm.sentra.api.delete_activity` - Delete activity

#### Specialized Queries
- **POST** `/api/method/crm.sentra.api.get_activities_by_city` - Get activities by city
- **POST** `/api/method/crm.sentra.api.get_activities_by_type` - Get activities by type
- **POST** `/api/method/crm.sentra.api.search_activities` - Search activities
- **POST** `/api/method/crm.sentra.api.get_activity_stats` - Get activity statistics

## 🔧 Authentication

All API calls require proper authentication headers:

```javascript
headers: {
  'Authorization': 'token your_api_key:your_api_secret',
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}
```

## 📊 Activity Data Model

### Core Fields
```javascript
{
  "name": "ACT-2025-00001",                    // Auto-generated ID
  "activity_name": "Dubai Desert Safari",      // Required
  "activity_code": "DDS001",                   // Required, unique
  "activity_type": "Adventure",                // Required
  "city": "Dubai",                             // Required (Link to Destination)
  "status": "Active",                          // Active|Inactive|Seasonal|Coming Soon
  "currency": "USD",                           // Required (Link to Currency)
  "pricing_type": "Per Person",               // Required
  
  // Pricing
  "adult_price": 150.00,
  "child_price": 100.00,
  "infant_price": 0.00,
  
  // Location
  "venue_name": "Al Maha Desert Resort",
  "address": "Desert Conservation Reserve",
  "latitude": 25.1234,
  "longitude": 55.5678,
  
  // Activity Details
  "description": "Experience authentic desert safari...",
  "difficulty_level": "Easy",                 // Easy|Moderate|Challenging|Extreme
  "duration_hours": 6,
  "duration_minutes": 30,
  "minimum_age": 3,
  "maximum_age": 70,
  "min_participants": 2,
  "max_participants": 20,
  
  // Operational
  "operating_days": "Daily",
  "timings": "4:00 PM - 10:30 PM",
  "seasonal_availability": "Year Round",
  
  // Vendor Information
  "vendor_type": "DMC",
  "vendor": "ABC Tours LLC",
  "commission_percentage": 10.5,
  "payment_terms": "Advance Payment",
  
  // Additional Info
  "inclusions": "Transportation, dinner, entertainment",
  "exclusions": "Personal expenses, alcohol",
  "safety_measures": "Safety briefing, first aid available",
  "insurance_required": true,
  "main_image": "/files/desert-safari.jpg"
}
```

## 🔍 API Usage Examples

### 1. Get Activities List

```javascript
fetch('/api/method/crm.sentra.api.get_activities', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  body: JSON.stringify({
    filters: {
      status: 'Active',
      city: ['in', ['Dubai', 'Abu Dhabi']]
    },
    fields: [
      'name', 'activity_name', 'activity_type', 'city', 
      'adult_price', 'currency', 'difficulty_level'
    ],
    order_by: 'activity_name asc',
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
        "name": "ACT-2025-00001",
        "activity_name": "Dubai Desert Safari",
        "activity_type": "Adventure",
        "city": "Dubai",
        "adult_price": 150.00,
        "currency": "USD",
        "difficulty_level": "Easy"
      }
    ],
    "count": 1,
    "total_count": 45,
    "limit_start": 0,
    "limit_page_length": 20
  }
}
```

### 2. Get Single Activity

```javascript
fetch('/api/method/crm.sentra.api.get_activity', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'ACT-2025-00001'
  })
})
```

### 3. Create New Activity

```javascript
fetch('/api/method/crm.sentra.api.create_activity', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    activity_data: {
      activity_name: 'Burj Khalifa At The Top',
      activity_code: 'BK001',
      activity_type: 'Sightseeing',
      city: 'Dubai',
      currency: 'USD',
      pricing_type: 'Per Person',
      adult_price: 45.00,
      child_price: 35.00,
      status: 'Active',
      venue_name: 'Burj Khalifa',
      difficulty_level: 'Easy',
      duration_hours: 2,
      min_participants: 1,
      max_participants: 50
    }
  })
})
```

### 4. Update Activity

```javascript
fetch('/api/method/crm.sentra.api.update_activity', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'ACT-2025-00001',
    activity_data: {
      adult_price: 175.00,
      child_price: 125.00,
      status: 'Active'
    }
  })
})
```

### 5. Search Activities

```javascript
fetch('/api/method/crm.sentra.api.search_activities', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'desert safari',
    filters: {
      status: 'Active'
    },
    limit: 10
  })
})
```

### 6. Get Activities by City

```javascript
fetch('/api/method/crm.sentra.api.get_activities_by_city', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    city: 'Dubai',
    filters: {
      activity_type: 'Adventure'
    },
    limit: 25
  })
})
```

### 7. Get Activity Statistics

```javascript
fetch('/api/method/crm.sentra.api.get_activity_stats', {
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
    "total_activities": 150,
    "active_activities": 142,
    "by_type": {
      "Adventure": 45,
      "Sightseeing": 38,
      "Cultural Experience": 25,
      "Water Activities": 20,
      "Entertainment": 14
    },
    "by_city": {
      "Dubai": 65,
      "Abu Dhabi": 32,
      "Sharjah": 18,
      "Ras Al Khaimah": 15,
      "Fujairah": 12
    },
    "by_difficulty": {
      "Easy": 89,
      "Moderate": 35,
      "Challenging": 12,
      "Extreme": 6
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
  status: ['in', ['Active', 'Seasonal']],
  
  // Location filters
  city: 'Dubai',
  city: ['in', ['Dubai', 'Abu Dhabi']],
  
  // Type filters
  activity_type: 'Adventure',
  activity_type: ['in', ['Adventure', 'Sightseeing']],
  
  // Price filters
  adult_price: ['>', 50],
  adult_price: ['between', [50, 200]],
  
  // Difficulty filters
  difficulty_level: ['in', ['Easy', 'Moderate']],
  
  // Duration filters
  duration_hours: ['<=', 4],
  
  // Participant filters
  min_participants: ['<=', 2],
  max_participants: ['>=', 10],
  
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
  "message": "Field 'activity_name' is required"
}
```

#### Not Found (404)
```javascript
{
  "exc_type": "DoesNotExistError", 
  "message": "Activity not found"
}
```

#### Duplicate Entry (409)
```javascript
{
  "exc_type": "DuplicateEntryError",
  "message": "Activity Code 'DDS001' already exists"
}
```

## 🚀 Best Practices

### 1. Efficient Querying
```javascript
// ✅ Good: Specify only needed fields
{
  fields: ['name', 'activity_name', 'city', 'adult_price'],
  limit_page_length: 20
}

// ❌ Bad: Fetching all fields and too many records
{
  limit_page_length: 1000  // Too many records
}
```

### 2. Proper Filtering
```javascript
// ✅ Good: Use specific filters
{
  filters: {
    status: 'Active',
    city: 'Dubai',
    activity_type: 'Adventure'
  }
}

// ❌ Bad: No filters (returns all records)
{
  filters: {}
}
```

### 3. Error Handling
```javascript
try {
  const response = await fetch('/api/method/crm.sentra.api.get_activities', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || 'API request failed');
  }
  
  return data.message;
} catch (error) {
  console.error('Activity API Error:', error);
  // Handle error appropriately
}
```

## 🔗 Related DocTypes

### Linked DocTypes
- **Destination** (city field) - City/location information
- **Currency** (currency field) - Pricing currency
- **Vendor Types** (vendor_type field) - Supplier categories

### Child Tables
- **Activity Timing** - Multiple time slots/schedules
- **Activity Requirements** - Prerequisites and restrictions

## 📝 Notes

1. **Required Fields**: All create operations must include activity_name, activity_code, activity_type, city, currency, and pricing_type
2. **Unique Constraints**: activity_code must be unique across all activities
3. **Pricing**: Supports multiple pricing types (Per Person, Per Group, Per Hour, Fixed Price, Custom)
4. **Status Management**: Activities can be Active, Inactive, Seasonal, or Coming Soon
5. **Geographic Linking**: city field links to Destination DocType for consistency
6. **Vendor Integration**: Supports linking to various vendor types (DMC, Hotel, Restaurant, etc.)

## 🎯 Quick Reference

| Operation | Endpoint | Method | Key Parameters |
|-----------|----------|---------|---------------|
| List | `get_activities` | POST | filters, fields, pagination |
| Get One | `get_activity` | POST | name |
| Create | `create_activity` | POST | activity_data |
| Update | `update_activity` | POST | name, activity_data |
| Delete | `delete_activity` | POST | name |
| Search | `search_activities` | POST | query, filters |
| By City | `get_activities_by_city` | POST | city, filters |
| By Type | `get_activities_by_type` | POST | activity_type, filters |
| Stats | `get_activity_stats` | POST | - |