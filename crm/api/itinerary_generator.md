# Itinerary Generator API Documentation

## Overview

The Itinerary Generator API is a comprehensive service for analyzing trips, matching them with standard packages, and automatically creating detailed itineraries using AI-powered selection. The API integrates with Frappe AI's LLM capabilities to provide intelligent service selection and customization based on trip requirements.

## Core Features

- **Package Matching**: Analyzes trip requirements against available standard packages
- **AI-Powered Selection**: Uses LLM to intelligently select and customize services
- **Automatic Itinerary Creation**: Creates Itinerary DocType records with populated services
- **Multi-destination Support**: Handles trips with multiple destinations
- **Service Distribution**: Intelligently distributes activities, meals, and transfers across days
- **Cost Calculation**: Calculates total costs based on selected services

## API Endpoints

### 1. `build_detailed_itinerary`

**Endpoint**: `/api/method/crm.api.itinerary_generator.build_detailed_itinerary`

**Method**: `POST`

**Description**: Main API that analyzes trip requirements, selects the best matching package, and creates a detailed itinerary with AI-selected services.

**Parameters**:
- `trip_name` (string, required): The Trip document ID/name
- `fill_itinerary` (boolean, default: `true`): Creates actual Itinerary DocType record
- `use_ai_selection` (boolean, default: `true`): Uses AI for intelligent service selection

**Request Example**:
```json
{
  "trip_name": "REQ-2025-00008"
}
```

**Response Example**:
```json
{
  "success": true,
  "message": "Successfully created itinerary ITIN-2025-00001",
  "itinerary": {
    "name": "ITIN-2025-00001",
    "itinerary_name": "London Discovery Tour - Itinerary 1",
    "itinerary_code": "REQ-2025-00008-ITIN-01",
    "trip": "REQ-2025-00008",
    "status": "Draft",
    "total_cost": 12500.00,
    "currency": "GBP",
    "interactive_day_wise_itinerary": [
      {
        "day": 1,
        "date": "2025-03-15",
        "title": "Arrival & Westminster Discovery",
        "destination": "London",
        "services": [
          {
            "service_type": "transfer",
            "service_name": "Airport Transfer - Heathrow to Central London",
            "service_id": "TRF-001",
            "time": "10:00",
            "duration": 1.5,
            "cost": 75.00,
            "provider": "London Transfers Ltd",
            "notes": "Private car transfer"
          },
          {
            "service_type": "hotel",
            "service_name": "The London Plaza Hotel",
            "service_id": "HTL-004",
            "check_in": "14:00",
            "star_rating": "4",
            "room_type": "Deluxe Double",
            "cost": 180.00,
            "provider": "London Plaza Hotels"
          },
          {
            "service_type": "activity",
            "service_name": "Westminster Walking Tour",
            "service_id": "ACT-001",
            "time": "15:30",
            "duration": 3,
            "cost": 45.00,
            "provider": "London Walking Tours",
            "included": "Professional guide, entrance to Westminster Abbey"
          },
          {
            "service_type": "meal",
            "service_name": "Welcome Dinner at The Ivy",
            "service_id": "MEL-002",
            "time": "19:00",
            "meal_type": "dinner",
            "cuisine": "British Modern",
            "cost": 65.00
          }
        ]
      },
      {
        "day": 2,
        "date": "2025-03-16",
        "title": "Royal London Experience",
        "destination": "London",
        "services": [
          {
            "service_type": "meal",
            "service_name": "English Breakfast",
            "service_id": "MEL-003",
            "time": "08:00",
            "meal_type": "breakfast",
            "included_in_hotel": true,
            "cost": 0
          },
          {
            "service_type": "activity",
            "service_name": "Tower of London & Crown Jewels",
            "service_id": "ACT-002",
            "time": "10:00",
            "duration": 3,
            "cost": 85.00,
            "provider": "Historic Royal Palaces",
            "included": "Entry ticket, Yeoman Warder tour"
          },
          {
            "service_type": "meal",
            "service_name": "Traditional Pub Lunch",
            "service_id": "MEL-004",
            "time": "13:30",
            "meal_type": "lunch",
            "cuisine": "Traditional British",
            "cost": 35.00
          },
          {
            "service_type": "activity",
            "service_name": "Thames River Cruise",
            "service_id": "ACT-003",
            "time": "15:30",
            "duration": 2,
            "cost": 25.00,
            "provider": "Thames Cruises"
          }
        ]
      }
    ],
    "notes": "AI-generated itinerary based on London Heritage Explorer package"
  },
  "package_analysis": {
    "selected_package": {
      "name": "PCK-2025-0001",
      "package_name": "London Heritage Explorer",
      "match_score": 85.5,
      "base_cost": 850.00,
      "currency": "GBP"
    },
    "ai_recommendations": [
      "Added extra day at Tower of London based on historical interest",
      "Upgraded hotel to 4-star based on comfort preference",
      "Included traditional British meals as requested",
      "Added Thames cruise for scenic experience"
    ]
  }
}
```

### 2. `analyze_trip_package_match`

**Endpoint**: `/api/method/crm.api.itinerary_generator.analyze_trip_package_match`

**Method**: `POST`

**Description**: Analyzes trip requirements and returns the best matching package with AI analysis.

**Parameters**:
- `trip_name` (string, required): The Trip document ID/name

**Request Example**:
```json
{
  "trip_name": "REQ-2025-00008"
}
```

**Response Example**:
```json
{
  "success": true,
  "selected_package": {
    "name": "PCK-2025-0001",
    "package_name": "London Heritage Explorer",
    "package_code": "LON5HE",
    "description": "Discover London's rich history...",
    "base_cost": 850.00,
    "currency": "GBP",
    "hotel_category": "4",
    "no_of_days": 5,
    "no_of_nights": 4
  },
  "match_score": 85.5,
  "match_score_breakdown": {
    "destination": {
      "score": 10.0,
      "percentage": 100,
      "weight": 30,
      "details": "Perfect match: London"
    },
    "dates": {
      "score": 8.5,
      "percentage": 85,
      "weight": 20,
      "details": "Package available for travel dates"
    },
    "budget": {
      "score": 7.0,
      "percentage": 70,
      "weight": 25,
      "details": "Within budget range"
    }
  },
  "ai_analysis": {
    "alignment_score": 88,
    "key_matches": [
      "Historical sites preference aligns with heritage tour",
      "4-star hotel matches comfort requirements",
      "Group size compatible"
    ],
    "potential_gaps": [
      "Package doesn't include Windsor Castle as requested",
      "Limited shopping time compared to preferences"
    ],
    "customization_suggestions": [
      "Add optional Windsor Castle day trip",
      "Extend shopping time on Day 5"
    ]
  },
  "recommendations": [
    "Consider adding Windsor Castle day trip (extra £120)",
    "Book theatre tickets in advance for West End show",
    "Upgrade to 5-star hotel for £50 per night extra"
  ],
  "alternative_packages": [
    {
      "name": "PCK-2025-0002",
      "package_name": "London Luxury Experience",
      "score": 72.3,
      "main_gaps": ["Over budget", "Too luxury-focused"]
    }
  ]
}
```

## Process Flow

### 1. Trip Analysis Phase
1. **Trip Validation**: Validates the trip document exists and has required fields
2. **Data Extraction**: Extracts trip requirements including:
   - Destinations and dates
   - Budget preferences
   - Group size
   - Special requirements from notes

### 2. Package Matching Phase
1. **Package Retrieval**: Fetches all active Standard Package documents
2. **Scoring Algorithm**: Scores each package based on:
   - **Destination Match** (30% weight): Exact match of destinations
   - **Date Availability** (20% weight): Package validity for travel dates
   - **Budget Alignment** (25% weight): Cost within budget range
   - **Duration Match** (15% weight): Number of days/nights alignment
   - **Group Size** (10% weight): Compatibility with min/max group size

3. **AI Analysis**: Sends top-matched package to LLM for detailed analysis

### 3. Service Selection Phase (when fill_itinerary=true)

1. **Service Retrieval**: Fetches available services:
   - Hotels (filtered by star rating)
   - Activities (filtered by destination)
   - Meals (various cuisine types)
   - Transfers (airport and local)
   - Transportation (between destinations)

2. **AI Service Selection**: 
   - Constructs detailed context with trip requirements and available services
   - Uses `analyze_with_llm` from frappe_ai.utils.llm_utils
   - AI selects appropriate services for each day
   - Returns structured JSON with selected services

3. **Service Distribution**:
   - Validates AI selections
   - Distributes services across trip days
   - Calculates costs for each service
   - Handles multi-destination logistics

### 4. Itinerary Creation Phase

1. **Document Creation**:
   - Creates new Itinerary DocType
   - Uses incremental naming (Trip Name - Itinerary 1, 2, 3...)
   - Sets status to "Draft"

2. **Field Population**:
   - Basic fields: trip link, dates, destinations
   - Cost fields: total cost, currency, markup
   - Service details in Interactive Day-wise Itinerary JSON field
   - AI analysis notes

3. **Validation**:
   - Ensures unique itinerary code
   - Validates all required fields
   - Calculates nights per destination

## AI Integration Details

### LLM Configuration
- **Model**: GPT-4o-mini (configurable)
- **Temperature**: 0.3 (for consistent selections)
- **Response Format**: Structured JSON

### Context Construction
The AI receives comprehensive context including:
1. **Trip Details**: Dates, destinations, budget, group size, requirements
2. **Package Information**: Selected package details and itinerary
3. **Available Services**: Complete list with costs and details
4. **Instructions**: Specific guidelines for selection logic

### AI Prompt Structure
```python
system_prompt = """You are a travel planning expert creating customized itineraries.
Your task is to select the most appropriate services for each day of the trip based on:
1. Trip requirements and preferences
2. Logical flow and timing
3. Budget constraints
4. Destination availability
"""

query = f"""Based on this trip and package, select services for each day:
Trip: {trip_details}
Package: {package_details}
Available Services: {services_list}

Return a JSON structure with selected services for each day.
"""
```

## Error Handling

### Common Errors and Solutions

1. **Missing Trip Document**
   - Error: "Trip REQ-2025-00008 not found"
   - Solution: Verify trip exists in system

2. **No Active Packages**
   - Error: "No active standard packages found"
   - Solution: Ensure packages have status="Active"

3. **AI Service Unavailable**
   - Error: "Failed to get AI recommendations"
   - Solution: Falls back to returning package without AI analysis

4. **Duplicate Itinerary Code**
   - Error: "Duplicate entry 'REQ-2025-00008-ITIN-01'"
   - Solution: Automatically increments to next number

5. **Missing Required Fields**
   - Error: "Missing required field: nights"
   - Solution: Calculates nights from trip dates

## Database Schema

### Related DocTypes

1. **Trip**
   - Contains trip requirements
   - Links to Contact (traveler)
   - Has child table: destination_city

2. **Standard Package**
   - Template packages
   - Contains itinerary_data JSON
   - Has child table: destinations

3. **Itinerary**
   - Generated itinerary document
   - Links to Trip
   - Contains interactive_day_wise_itinerary JSON

4. **Service DocTypes**
   - Hotel
   - Activity  
   - Meal
   - Transfer
   - Transportation

## Performance Considerations

1. **Caching**: Package data cached during scoring phase
2. **Batch Processing**: Services fetched in single queries
3. **AI Timeout**: 30-second timeout for LLM calls
4. **Transaction Management**: Proper commit/rollback on errors

## Configuration

### Settings (via Frappe)
- `itinerary_generator.use_ai`: Enable/disable AI features
- `itinerary_generator.default_currency`: Default currency for costs
- `itinerary_generator.markup_percentage`: Default markup on services

### Environment Variables
- `OPENAI_API_KEY`: Required for AI features
- `AI_MODEL`: Override default model (optional)

## Usage Examples

### Frontend Integration (JavaScript)

```javascript
// Create itinerary with AI selection
frappe.call({
    method: 'crm.api.itinerary_generator.build_detailed_itinerary',
    args: {
        trip_name: 'REQ-2025-00008'
        // fill_itinerary defaults to true
        // use_ai_selection defaults to true
    },
    callback: function(response) {
        if (response.message.success) {
            console.log('Itinerary created:', response.message.itinerary.name);
            // Navigate to the new itinerary
            frappe.set_route('Form', 'Itinerary', response.message.itinerary.name);
        } else {
            frappe.msgprint(response.message.error);
        }
    }
});

// Just analyze without creating itinerary
frappe.call({
    method: 'crm.api.itinerary_generator.analyze_trip_package_match',
    args: {
        trip_name: 'REQ-2025-00008'
    },
    callback: function(response) {
        console.log('Best match:', response.message.selected_package);
        console.log('AI Analysis:', response.message.ai_analysis);
    }
});
```

### Python Integration

```python
import frappe

# Create itinerary programmatically
result = frappe.get_doc({
    "doctype": "Trip",
    "name": "REQ-2025-00008"
}).run_method("build_detailed_itinerary")

if result["success"]:
    itinerary_name = result["itinerary"]["name"]
    print(f"Created itinerary: {itinerary_name}")
```

## Testing

### Test Scenarios

1. **Single Destination Trip**
   - London only, 5 days
   - Should match London packages

2. **Multi-Destination Trip**
   - London + Singapore, 8 days
   - Should match combined packages

3. **Budget Constraints**
   - Low budget trips
   - Should filter expensive packages

4. **Date Availability**
   - Off-season dates
   - Should handle package validity

### Sample Test Data

```python
# Create test trip
test_trip = frappe.get_doc({
    "doctype": "Trip",
    "title": "Test London Trip",
    "contact": "CONT-001",
    "start_date": "2025-03-15",
    "end_date": "2025-03-19",
    "destination_city": [
        {"destination": "London"}
    ],
    "notes": "Prefer historical sites and museums"
}).insert()

# Generate itinerary
result = build_detailed_itinerary(
    trip_name=test_trip.name,
    fill_itinerary=True,
    use_ai_selection=True
)
```

## Troubleshooting

### Debug Mode
Enable debug logging:
```python
frappe.conf.developer_mode = 1
frappe.conf.logging_level = "DEBUG"
```

### Common Issues

1. **Services Not Populating**
   - Check if services exist in database
   - Verify destination names match exactly
   - Check AI response format

2. **AI Timeout**
   - Reduce service list size
   - Simplify selection criteria
   - Check API key validity

3. **Cost Calculation Errors**
   - Ensure all services have base_price field
   - Check currency conversions
   - Verify markup calculations

## Version History

### v2.0.0 (Current)
- AI-powered service selection by default
- Automatic itinerary creation by default
- Enhanced multi-destination support
- Improved error handling

### v1.0.0
- Basic package matching
- Manual service selection
- Simple scoring algorithm

## Support

For issues or questions:
- GitHub Issues: [CRM Repository]
- Documentation: This file
- Logs: Check Error Log List in Frappe

## License

Part of Frappe CRM - AGPLv3 License