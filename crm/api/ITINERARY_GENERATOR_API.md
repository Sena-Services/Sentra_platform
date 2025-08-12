# Trip Package Matching API Documentation

## Overview
The Trip Package Matching API analyzes trip requirements and automatically matches them with the most suitable standard package using AI-powered analysis. It evaluates destinations, dates, activities, group size, and budget to find the best match and provides detailed recommendations.

## API Endpoint

### Method: `analyze_trip_package_match`

**Full Path:** `/api/method/crm.api.itinerary_generator.analyze_trip_package_match`

**HTTP Method:** POST

**Authentication:** Required (Frappe API key/token)

---

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trip_name` | string | Yes | The name/ID of the Trip document (e.g., "REQ-2025-00008") |

### Example Request

```bash
curl -X POST https://your-site.com/api/method/crm.api.itinerary_generator.analyze_trip_package_match \
  -H "Content-Type: application/json" \
  -H "Authorization: token API_KEY:API_SECRET" \
  -d '{"trip_name": "REQ-2025-00008"}'
```

---

## Trip Document Requirements

For the API to work effectively, the Trip document should have the following fields populated:

### Required Fields
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `customer` | Link (Contact) | The customer making the trip request | "John Doe" |
| `destination_city` | Table (Trip Destination) | List of destinations for the trip | [{"destination": "Singapore"}] |

### Recommended Fields for Better Matching
| Field | Type | Description | Example | Impact |
|-------|------|-------------|---------|--------|
| `start_date` | Date | Trip start date | "2025-03-15" | Affects date compatibility scoring (25% weight) |
| `end_date` | Date | Trip end date | "2025-03-20" | Affects date compatibility scoring (25% weight) |
| `flexible_days` | Select | Date flexibility preference | "Within the week" | Adjusts date matching tolerance |
| `passenger_details` | Table (Trip Passenger) | List of passengers | [{"name": "John"}, {"name": "Jane"}] | Used to calculate group size (15% weight) |
| `budget` | Currency | Total budget for the trip | 5000 | Affects budget alignment scoring (10% weight) |
| `activity` | Table MultiSelect | Preferred activities | [{"activity": "City Tour"}, {"activity": "Shopping"}] | Affects activity matching (20% weight) |
| `departure` | Data | Departure city | "Mumbai" | Used for logistics planning |
| `priority` | Select | Trip priority | "High" | Used for urgency assessment |
| `category` | Select | Hotel category preference | "4" | Used for accommodation matching |

### Date Flexibility Options
- `"Exact dates"` - Package must match exact dates
- `"Within the week"` - Allows ±3 days flexibility
- `"Within the month"` - Allows ±15 days flexibility  
- `"Fully flexible"` - Any date within package validity

---

## Scoring Algorithm

The API uses a weighted scoring system to match packages:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Destination Match** | 30% | Percentage of trip destinations covered by package |
| **Date Compatibility** | 25% | How well package dates align with trip dates (considers flexibility) |
| **Activity Match** | 20% | Percentage of requested activities available in package |
| **Group Size** | 15% | Compatibility of group size with package min/max limits |
| **Budget Alignment** | 10% | How well package price fits within budget |

**Total Score:** 0-100 points (minimum threshold: 10 points)

---

## Response Structure

### Success Response

```json
{
  "success": true,
  "selected_package": {
    "name": "PCK-2025-00005",
    "package_name": "Singapore City Lights",
    "package_code": "SIN4CL",
    "description": "Experience the vibrant city of Singapore...",
    "base_cost": 1200,
    "currency": "USD",
    "dmc": "Singapore Tours Pte Ltd",
    "hotel_category": "4",
    "no_of_days": 5,
    "no_of_nights": 4
  },
  "match_score": 81.0,
  "match_score_breakdown": {
    "destination": {
      "score": 30.0,
      "max_score": 30,
      "percentage": 100.0
    },
    "dates": {
      "score": 25.0,
      "max_score": 25,
      "percentage": 100.0
    },
    "activities": {
      "score": 10.0,
      "max_score": 20,
      "percentage": 50.0,
    },
    "group_size": {
      "score": 15.0,
      "max_score": 15,
      "percentage": 100.0,
      "group_size": 2
    },
    "budget": {
      "score": 1.0,
      "max_score": 10,
      "percentage": 10.0
    }
  },
  "destination_mismatch_warning": false,
  "ai_analysis": {
    "alignment_score": 85,
    "satisfaction_analysis": {
      "strengths": [
        "Perfect destination match for Singapore",
        "Dates align perfectly with travel period",
        "Group size fits within package limits"
      ],
      "gaps": [
        "Budget significantly exceeds package cost",
        "Some requested activities not explicitly included"
      ]
    },
    "customization_recommendations": [
      "Add premium dining experiences to utilize budget",
      "Include adventure activities as requested",
      "Consider upgrading to 5-star hotels"
    ],
    "risk_factors": [
      "Budget underutilization may indicate preference mismatch"
    ]
  },
  "recommendations": [
    "Add custom activities to meet specific requirements",
    "Consider premium add-ons to better utilize budget"
  ],
  "alternative_packages": [
    {
      "name": "PCK-2025-00003",
      "package_name": "Malaysia Heritage Tour",
      "score": 65.5,
      "main_gaps": [
        "destination: 0% match",
        "activities: 25% match"
      ]
    }
  ]
}
```

### Error Response

```json
{
  "success": false,
  "message": "No active standard packages found",
  "selected_package": null,
  "ai_analysis": null
}
```

### Field Descriptions

#### Main Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the API call was successful |
| `selected_package` | object | Details of the best matching package |
| `match_score` | float | Overall matching score (0-100) |
| `match_score_breakdown` | object | Detailed scoring for each criterion |
| `destination_mismatch_warning` | boolean | True if selected package doesn't match destinations |
| `ai_analysis` | object | AI-generated analysis of requirement alignment |
| `ai_analysis_raw` | string | Raw AI response if parsing failed |
| `ai_error` | string | Error message if AI analysis failed |
| `recommendations` | array | List of actionable recommendations |
| `alternative_packages` | array | Top 3 alternative packages with scores |

#### AI Analysis Structure
| Field | Type | Description |
|-------|------|-------------|
| `alignment_score` | integer | Overall alignment percentage (0-100) |
| `satisfaction_analysis` | object | Detailed analysis of strengths and gaps |
| `satisfaction_analysis.strengths` | array | List of requirements well-satisfied |
| `satisfaction_analysis.gaps` | array | List of unmet requirements |
| `customization_recommendations` | array | Specific customization suggestions |
| `risk_factors` | array | Potential issues or concerns |

---

## Usage Examples

### Python Example

```python
import requests
import json

# API credentials
api_key = "your_api_key"
api_secret = "your_api_secret"
site_url = "https://your-site.com"

# Make API call
response = requests.post(
    f"{site_url}/api/method/crm.api.itinerary_generator.analyze_trip_package_match",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{api_secret}"
    },
    json={"trip_name": "REQ-2025-00008"}
)

# Process response
if response.status_code == 200:
    data = response.json()
    if data["success"]:
        print(f"Selected Package: {data['selected_package']['package_name']}")
        print(f"Match Score: {data['match_score']:.1f}%")
        print(f"AI Recommendations:")
        for rec in data.get("recommendations", []):
            print(f"  - {rec}")
    else:
        print(f"Error: {data['message']}")
else:
    print(f"HTTP Error: {response.status_code}")
```

### JavaScript Example

```javascript
// Using fetch API
const analyzeTrip = async (tripName) => {
    const response = await fetch(
        'https://your-site.com/api/method/crm.api.itinerary_generator.analyze_trip_package_match',
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'token API_KEY:API_SECRET'
            },
            body: JSON.stringify({ trip_name: tripName })
        }
    );
    
    const data = await response.json();
    
    if (data.success) {
        console.log(`Selected: ${data.selected_package.package_name}`);
        console.log(`Score: ${data.match_score}`);
        
        // Display AI analysis
        if (data.ai_analysis) {
            console.log('Strengths:', data.ai_analysis.satisfaction_analysis.strengths);
            console.log('Gaps:', data.ai_analysis.satisfaction_analysis.gaps);
        }
    } else {
        console.error('Error:', data.message);
    }
};

// Usage
analyzeTrip('REQ-2025-00008');
```

### Using in Frappe/ERPNext

```python
# Server-side (Python)
import frappe
from crm.api.itinerary_generator import analyze_trip_package_match

@frappe.whitelist()
def get_package_recommendation(trip_name):
    """Get package recommendation for a trip"""
    result = analyze_trip_package_match(trip_name)
    
    if result["success"]:
        # Update trip with selected package
        trip = frappe.get_doc("Trip", trip_name)
        trip.use_standard_package = result["selected_package"]["name"]
        trip.save()
        
        frappe.msgprint(
            f"Recommended: {result['selected_package']['package_name']} "
            f"(Score: {result['match_score']:.0f}%)"
        )
    
    return result
```

```javascript
// Client-side (JavaScript)
frappe.ui.form.on('Trip', {
    find_matching_package: function(frm) {
        frappe.call({
            method: 'crm.api.itinerary_generator.analyze_trip_package_match',
            args: {
                trip_name: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    const pkg = r.message.selected_package;
                    const score = r.message.match_score;
                    
                    // Show recommendation dialog
                    frappe.msgprint({
                        title: 'Package Recommendation',
                        message: `
                            <b>Recommended Package:</b> ${pkg.package_name}<br>
                            <b>Match Score:</b> ${score.toFixed(0)}%<br>
                            <b>Price:</b> ${pkg.currency} ${pkg.base_cost} per person<br>
                            <br>
                            <b>AI Analysis:</b><br>
                            ${r.message.recommendations.join('<br>')}
                        `,
                        indicator: score > 70 ? 'green' : 'orange'
                    });
                    
                    // Optionally set the package
                    frm.set_value('use_standard_package', pkg.name);
                }
            }
        });
    }
});
```

---

## Error Handling

### Common Error Scenarios

1. **Trip Not Found**
   ```json
   {
     "success": false,
     "error": "Trip REQ-2025-00999 not found",
     "message": "An error occurred while analyzing the trip"
   }
   ```

2. **No Active Packages**
   ```json
   {
     "success": false,
     "message": "No active standard packages found",
     "selected_package": null
   }
   ```

3. **No Suitable Match**
   ```json
   {
     "success": false,
     "message": "No suitable package found for the trip requirements",
     "all_scores": [...]
   }
   ```

4. **AI Analysis Failure**
   ```json
   {
     "success": true,
     "selected_package": {...},
     "ai_analysis": null,
     "ai_error": "OpenAI API error: Rate limit exceeded"
   }
   ```

---

## Best Practices

1. **Complete Trip Information**: Populate as many Trip fields as possible for better matching accuracy

2. **Date Flexibility**: Set appropriate date flexibility to increase matching options

3. **Budget Considerations**: 
   - Enter realistic budgets for better matches
   - Budget is per person if group size is specified
   - Consider including a budget range tolerance

4. **Activities**: Be specific about required vs. optional activities

5. **Error Handling**: Always check the `success` field before processing results

6. **Caching**: Consider caching results for identical requests to reduce API calls

7. **Batch Processing**: For multiple trips, process them sequentially to avoid rate limits

---

## API Limits and Performance

- **Response Time**: Typically 2-5 seconds (depends on AI analysis)
- **Rate Limits**: Subject to Frappe and OpenAI API rate limits
- **Max Package Evaluation**: All active packages are evaluated
- **Timeout**: 30 seconds for complete processing

---

## Troubleshooting

### Issue: Low Match Scores
- **Cause**: Trip requirements don't align with available packages
- **Solution**: Review trip requirements, especially destinations and dates

### Issue: AI Analysis Missing
- **Cause**: OpenAI API key not configured or API error
- **Solution**: Check LLM settings in Frappe AI app

### Issue: Wrong Package Selected
- **Cause**: Scoring weights may not match business priorities
- **Solution**: Adjust scoring weights in `calculate_package_score()` function

### Issue: Slow Response
- **Cause**: Large number of packages or slow AI response
- **Solution**: Limit active packages, implement caching

---

## Configuration

### Environment Variables
```bash
# OpenAI API Key (required for AI analysis)
OPENAI_API_KEY=sk-...

# Optional: Custom AI model
AI_MODEL=gpt-4o-mini
```

### Frappe AI Settings
Configure in Frappe AI app settings:
- OpenAI API Key
- Model selection
- Temperature settings
- Max tokens limit

---

## Support and Updates

For issues, enhancements, or questions:
1. Check error logs in Frappe: **Error Log List**
2. Review API logs: **Activity Log**
3. Contact system administrator for configuration issues

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-12 | Initial release with core matching and AI analysis |

---

## Related Documentation

- [Trip DocType Documentation](./trip_doctype.md)
- [Standard Package DocType Documentation](./standard_package_doctype.md)
- [Frappe API Authentication](https://frappeframework.com/docs/user/en/api/rest)
- [OpenAI API Reference](https://platform.openai.com/docs)