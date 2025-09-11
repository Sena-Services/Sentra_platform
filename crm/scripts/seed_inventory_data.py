#!/usr/bin/env python3
"""
Seed script to create sample inventory data for testing
Run this script to populate the database with sample hotels, activities, meals, etc.
"""

import frappe
from frappe import _

def create_sample_hotels():
    """Create sample hotel data"""
    sample_hotels = [
        {
            "hotel_name": "Marina Bay Sands",
            "star_rating": "5 Star",
            "category": "Luxury",
            "city": "Singapore",
            "address_line_1": "10 Bayfront Avenue",
            "total_rooms": 2560,
            "currency": "SGD",
            "base_display_price": 450,
            "rating": 4.7,
            "short_description": "Iconic luxury resort with infinity pool and stunning city views",
            "is_featured": 1,
            "status": "Active"
        },
        {
            "hotel_name": "Raffles Hotel",
            "star_rating": "5 Star Deluxe",
            "category": "Heritage",
            "city": "Singapore",
            "address_line_1": "1 Beach Road",
            "total_rooms": 115,
            "currency": "SGD",
            "base_display_price": 650,
            "rating": 4.8,
            "short_description": "Historic luxury hotel with colonial charm and heritage suites",
            "is_featured": 1,
            "status": "Active"
        },
        {
            "hotel_name": "Shangri-La Singapore",
            "star_rating": "5 Star",
            "category": "Luxury",
            "city": "Singapore",
            "address_line_1": "22 Orange Grove Road",
            "total_rooms": 750,
            "currency": "SGD",
            "base_display_price": 380,
            "rating": 4.6,
            "short_description": "Garden oasis in the city with luxury amenities and spa",
            "is_featured": 0,
            "status": "Active"
        },
        {
            "hotel_name": "The Fullerton Hotel",
            "star_rating": "5 Star",
            "category": "Heritage",
            "city": "Singapore", 
            "address_line_1": "1 Fullerton Square",
            "total_rooms": 400,
            "currency": "SGD",
            "base_display_price": 420,
            "rating": 4.5,
            "short_description": "Historic waterfront hotel with neoclassical architecture",
            "is_featured": 0,
            "status": "Active"
        },
        {
            "hotel_name": "Capella Singapore",
            "star_rating": "5 Star Deluxe",
            "category": "Resort",
            "city": "Singapore",
            "address_line_1": "1 The Knolls, Sentosa Island",
            "total_rooms": 112,
            "currency": "SGD", 
            "base_display_price": 560,
            "rating": 5.0,
            "short_description": "Ultra-luxury resort on Sentosa Island with personalized service",
            "is_featured": 1,
            "status": "Active"
        }
    ]
    
    created_count = 0
    for hotel_data in sample_hotels:
        # Check if hotel already exists
        if not frappe.db.exists("Hotel", {"hotel_name": hotel_data["hotel_name"]}):
            try:
                hotel = frappe.get_doc({
                    "doctype": "Hotel",
                    **hotel_data
                })
                hotel.insert()
                created_count += 1
                print(f"✅ Created hotel: {hotel_data['hotel_name']}")
            except Exception as e:
                print(f"❌ Failed to create hotel {hotel_data['hotel_name']}: {str(e)}")
        else:
            print(f"⏭️  Hotel already exists: {hotel_data['hotel_name']}")
    
    frappe.db.commit()
    return created_count

def create_sample_activities():
    """Create sample activity data"""
    sample_activities = [
        {
            "activity_name": "Singapore Zoo",
            "activity_type": "Nature",
            "city": "Singapore",
            "venue_name": "Singapore Zoo",
            "address": "80 Mandai Lake Rd",
            "duration_hours": 4,
            "duration_minutes": 0,
            "adult_price": 45,
            "child_price": 35,
            "currency": "SGD",
            "pricing_type": "Per Person",
            "base_display_price": 45,
            "rating": 4.5,
            "short_description": "World-class zoo with over 2,800 animals in naturalistic habitats",
            "is_featured": 1,
            "status": "Active"
        },
        {
            "activity_name": "Gardens by the Bay",
            "activity_type": "Sightseeing",
            "city": "Singapore",
            "venue_name": "Gardens by the Bay",
            "address": "18 Marina Gardens Dr",
            "duration_hours": 3,
            "duration_minutes": 0,
            "adult_price": 35,
            "child_price": 25,
            "currency": "SGD",
            "pricing_type": "Per Person",
            "base_display_price": 35,
            "rating": 4.6,
            "short_description": "Futuristic park with iconic Supertrees and climate-controlled conservatories",
            "is_featured": 1,
            "status": "Active"
        },
        {
            "activity_name": "Universal Studios Singapore",
            "activity_type": "Theme Park",
            "city": "Singapore",
            "venue_name": "Universal Studios Singapore",
            "address": "8 Sentosa Gateway, Sentosa Island",
            "duration_hours": 8,
            "duration_minutes": 0,
            "adult_price": 85,
            "child_price": 75,
            "currency": "SGD",
            "pricing_type": "Per Person",
            "base_display_price": 85,
            "rating": 4.4,
            "short_description": "Hollywood movie-themed park with thrilling rides and shows",
            "is_featured": 1,
            "status": "Active"
        },
        {
            "activity_name": "Night Safari",
            "activity_type": "Nature",
            "city": "Singapore",
            "venue_name": "Night Safari",
            "address": "80 Mandai Lake Rd",
            "duration_hours": 3,
            "duration_minutes": 30,
            "adult_price": 55,
            "child_price": 40,
            "currency": "SGD",
            "pricing_type": "Per Person",
            "base_display_price": 55,
            "rating": 4.3,
            "short_description": "World's first nocturnal zoo experience with animals in natural habitat",
            "is_featured": 0,
            "status": "Active"
        },
        {
            "activity_name": "River Safari",
            "activity_type": "Nature",
            "city": "Singapore",
            "venue_name": "River Safari",
            "address": "80 Mandai Lake Rd",
            "duration_hours": 3,
            "duration_minutes": 0,
            "adult_price": 42,
            "child_price": 32,
            "currency": "SGD",
            "pricing_type": "Per Person",
            "base_display_price": 42,
            "rating": 4.2,
            "short_description": "River-themed wildlife park with giant pandas and boat rides",
            "is_featured": 0,
            "status": "Active"
        }
    ]
    
    created_count = 0
    for activity_data in sample_activities:
        # Check if activity already exists
        if not frappe.db.exists("Activity", {"activity_name": activity_data["activity_name"]}):
            try:
                activity = frappe.get_doc({
                    "doctype": "Activity",
                    **activity_data
                })
                activity.insert()
                created_count += 1
                print(f"✅ Created activity: {activity_data['activity_name']}")
            except Exception as e:
                print(f"❌ Failed to create activity {activity_data['activity_name']}: {str(e)}")
        else:
            print(f"⏭️  Activity already exists: {activity_data['activity_name']}")
    
    frappe.db.commit()
    return created_count

def create_sample_meals():
    """Create sample meal data"""
    sample_meals = [
        {
            "meal_name": "Hawker Chan Soya Sauce Chicken",
            "meal_type": "Lunch",
            "cuisine_type": "Local",
            "city": "Singapore",
            "venue_type": "Hawker Centre",
            "venue_name": "Hawker Chan",
            "restaurant_name": "Hawker Chan",
            "address": "Various Locations",
            "duration_hours": 1,
            "duration_minutes": 0,
            "adult_price": 25,
            "child_price": 20,
            "currency": "SGD",
            "pricing_type": "Per Person",
            "base_display_price": 25,
            "rating": 4.0,
            "short_description": "Michelin-starred hawker stall famous for soya sauce chicken rice",
            "is_featured": 1,
            "status": "Active"
        },
        {
            "meal_name": "Marina Bay Dining Experience",
            "meal_type": "Dinner",
            "cuisine_type": "International",
            "city": "Singapore",
            "venue_type": "Rooftop",
            "venue_name": "Ce La Vie",
            "restaurant_name": "Ce La Vie",
            "address": "1 Bayfront Ave, Level 57",
            "duration_hours": 2,
            "duration_minutes": 30,
            "adult_price": 95,
            "child_price": 65,
            "currency": "SGD",
            "pricing_type": "Per Person",
            "base_display_price": 95,
            "rating": 4.4,
            "short_description": "Rooftop fine dining with panoramic city views and modern cuisine",
            "is_featured": 1,
            "status": "Active"
        },
        {
            "meal_name": "Clarke Quay River Dining",
            "meal_type": "Dinner",
            "cuisine_type": "Fusion",
            "city": "Singapore",
            "venue_type": "Restaurant",
            "venue_name": "Jumbo Seafood",
            "restaurant_name": "Jumbo Seafood",
            "address": "30 Merchant Rd, #01-01/02",
            "duration_hours": 2,
            "duration_minutes": 0,
            "adult_price": 70,
            "child_price": 50,
            "currency": "SGD",
            "pricing_type": "Per Person",
            "base_display_price": 70,
            "rating": 4.2,
            "short_description": "Riverside seafood dining with signature chili crab and pepper crab",
            "is_featured": 0,
            "status": "Active"
        }
    ]
    
    created_count = 0
    for meal_data in sample_meals:
        # Check if meal already exists
        if not frappe.db.exists("Meal", {"meal_name": meal_data["meal_name"]}):
            try:
                meal = frappe.get_doc({
                    "doctype": "Meal",
                    **meal_data
                })
                meal.insert()
                created_count += 1
                print(f"✅ Created meal: {meal_data['meal_name']}")
            except Exception as e:
                print(f"❌ Failed to create meal {meal_data['meal_name']}: {str(e)}")
        else:
            print(f"⏭️  Meal already exists: {meal_data['meal_name']}")
    
    frappe.db.commit()
    return created_count

def seed_all_data():
    """Seed all inventory data"""
    print("🌱 Starting inventory data seeding...")
    
    total_created = 0
    
    print("\n🏨 Creating sample hotels...")
    total_created += create_sample_hotels()
    
    print("\n🎢 Creating sample activities...")
    total_created += create_sample_activities()
    
    print("\n🍽️ Creating sample meals...")
    total_created += create_sample_meals()
    
    print(f"\n✅ Seeding complete! Created {total_created} new inventory items.")
    print("🔄 You can now test the inventory API with real data.")

if __name__ == "__main__":
    # Run this script via: bench --site [sitename] execute crm.scripts.seed_inventory_data.seed_all_data
    seed_all_data()