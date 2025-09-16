#!/usr/bin/env python3
import frappe
import json
from datetime import datetime, timedelta

def create_standard_packages():
    """Create 3 standard package documents based on dummy data from Vue component"""

    # Package 1: Singapore City Explorer
    singapore_package = {
        "doctype": "Standard Package",
        "package_name": "Singapore City Explorer",
        "package_code": "PKG-SG-001",
        "status": "Active",
        "package_type": "City",
        "dmc": "Administrator",  # You may need to replace with actual DMC contact
        "description": "Discover Singapore's incredible diversity - from the iconic Marina Bay Sands to the mystical Gardens by the Bay, from thrilling Universal Studios to vibrant cultural districts. This package offers the perfect introduction to Asia's most modern city-state.",
        "hero_image": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
        "hero_description": "Experience the Lion City's perfect blend of futuristic architecture, lush gardens, and world-class attractions in this comprehensive Singapore adventure.",
        "category": "City Tours",
        "image_url": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        "highlights": """Marina Bay Sands SkyPark Experience
Gardens by the Bay with Supertree Grove
Universal Studios Singapore Full Day Pass
Sentosa Island Cable Car & Beaches
Singapore Zoo & Night Safari
Chinatown & Little India Cultural Tour
Orchard Road Shopping Experience
Singapore Flyer & River Cruise""",
        "gallery_images": """https://images.unsplash.com/photo-1525625293386-3f8f99389edd?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1496939376851-89342e90adcd?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1555217851-6141535bd771?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1565967511849-76a60a516170?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1600664356348-10686526af4f?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1542114740389-9b46fb1e5be7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80""",
        "valid_from": datetime.now().date(),
        "valid_to": (datetime.now() + timedelta(days=365)).date(),
        "no_of_days": 5,
        "no_of_nights": 4,
        "min_group_size": 2,
        "max_group_size": 20,
        "currency": "USD",
        "base_cost": 1899,
        "markup_percentage": 20,
        "popularity_score": 85,
        "rating": 4.5,
        "review_count": 124,
        "hotel": "4",
        "destinations": [
            {
                "destination": "Singapore",
                "days": 5
            }
        ],
        "package_inclusions": """<ul>
<li>4 Nights accommodation in 4-star hotel</li>
<li>Daily breakfast at hotel</li>
<li>Airport transfers</li>
<li>City tour with English-speaking guide</li>
<li>Universal Studios entrance ticket</li>
<li>Gardens by the Bay entrance</li>
<li>Singapore Flyer ticket</li>
<li>River cruise ticket</li>
</ul>""",
        "package_exclusions": """<ul>
<li>International flights</li>
<li>Lunch and dinner</li>
<li>Personal expenses</li>
<li>Travel insurance</li>
<li>Visa fees</li>
<li>Tips and gratuities</li>
</ul>""",
        "terms_and_conditions": """<p>Booking requires 30% advance payment. Full payment due 14 days before travel. Cancellation charges apply as per policy. Package rates are subject to availability and seasonal variations.</p>"""
    }

    # Package 2: Dubai Luxury Experience
    dubai_package = {
        "doctype": "Standard Package",
        "package_name": "Dubai Luxury Experience",
        "package_code": "PKG-DXB-001",
        "status": "Active",
        "package_type": "Luxury",
        "dmc": "Administrator",
        "description": "Dubai offers an unparalleled blend of modern luxury and Arabian tradition. From the world's tallest building to pristine beaches, from traditional souks to futuristic attractions, this package showcases the very best of the Emirates.",
        "hero_image": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
        "hero_description": "Experience the pinnacle of luxury in the UAE - from Dubai's towering skyscrapers to Abu Dhabi's cultural grandeur, indulge in world-class shopping, dining, and entertainment.",
        "category": "Luxury",
        "image_url": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        "highlights": """Burj Khalifa - At The Top Experience
Desert Safari with BBQ Dinner
Dubai Mall & Dubai Fountain Show
Abu Dhabi Sheikh Zayed Grand Mosque
Palm Jumeirah & Atlantis Aquaventure
Dubai Marina Yacht Cruise
Gold & Spice Souk Shopping Tour
Ferrari World Abu Dhabi""",
        "gallery_images": """https://images.unsplash.com/photo-1512453979798-5ea266f8880c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1518684079-3c830dcef090?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1580674684081-7617fbf3d745?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1582672060674-bc2bd808a8b5?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1609037532069-6143d0cd4a5e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1578895101408-1a36b834405b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80""",
        "valid_from": datetime.now().date(),
        "valid_to": (datetime.now() + timedelta(days=365)).date(),
        "no_of_days": 6,
        "no_of_nights": 5,
        "min_group_size": 2,
        "max_group_size": 15,
        "currency": "USD",
        "base_cost": 2499,
        "markup_percentage": 25,
        "popularity_score": 90,
        "rating": 4.7,
        "review_count": 189,
        "hotel": "5",
        "destinations": [
            {
                "destination": "Dubai",
                "days": 4
            },
            {
                "destination": "Abu Dhabi",
                "days": 2
            }
        ],
        "package_inclusions": """<ul>
<li>5 Nights accommodation in 5-star hotel</li>
<li>Daily breakfast and one lunch</li>
<li>Airport transfers in luxury vehicle</li>
<li>Desert Safari with BBQ dinner</li>
<li>Burj Khalifa entrance ticket</li>
<li>Abu Dhabi city tour</li>
<li>Dubai Marina dinner cruise</li>
<li>All entrance fees mentioned in itinerary</li>
</ul>""",
        "package_exclusions": """<ul>
<li>International flights</li>
<li>Remaining meals</li>
<li>Personal expenses</li>
<li>Travel insurance</li>
<li>UAE visa fees</li>
<li>Tips and gratuities</li>
<li>Optional activities</li>
</ul>""",
        "terms_and_conditions": """<p>Booking requires 40% advance payment. Full payment due 21 days before travel. Luxury package includes complimentary airport lounge access. Cancellation charges apply as per policy.</p>"""
    }

    # Package 3: Bali Island Paradise
    bali_package = {
        "doctype": "Standard Package",
        "package_name": "Bali Island Paradise",
        "package_code": "PKG-BALI-001",
        "status": "Active",
        "package_type": "Beach",
        "dmc": "Administrator",
        "description": "Bali offers a perfect blend of culture, nature, and relaxation. From ancient temples perched on clifftops to vibrant coral reefs, from traditional villages to world-class beach clubs, experience the magic that makes Bali one of the world's most beloved destinations.",
        "hero_image": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
        "hero_description": "Discover Bali's mystical temples, emerald rice terraces, pristine beaches, and warm Balinese hospitality in this unforgettable journey through the Island of the Gods.",
        "category": "Beach & Island",
        "image_url": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        "highlights": """Tanah Lot Temple Sunset Experience
Ubud Rice Terraces & Monkey Forest
Mount Batur Sunrise Trekking
Seminyak Beach Club Experience
Traditional Balinese Spa Treatment
Nusa Penida Island Day Trip
Water Temple Purification Ceremony
Balinese Cooking Class & Market Tour""",
        "gallery_images": """https://images.unsplash.com/photo-1537996194471-e657df975ab4?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1577717903315-1691ae25ab3f?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1544551763-46a013bb70d5?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80
https://images.unsplash.com/photo-1602002418816-5c0aeef426aa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80""",
        "valid_from": datetime.now().date(),
        "valid_to": (datetime.now() + timedelta(days=365)).date(),
        "no_of_days": 7,
        "no_of_nights": 6,
        "min_group_size": 2,
        "max_group_size": 25,
        "currency": "USD",
        "base_cost": 1599,
        "markup_percentage": 20,
        "popularity_score": 88,
        "rating": 4.6,
        "review_count": 215,
        "hotel": "4",
        "destinations": [
            {
                "destination": "Ubud",
                "days": 3
            },
            {
                "destination": "Seminyak",
                "days": 2
            },
            {
                "destination": "Nusa Dua",
                "days": 2
            }
        ],
        "package_inclusions": """<ul>
<li>6 Nights accommodation in 4-star resort</li>
<li>Daily breakfast at resort</li>
<li>Airport transfers</li>
<li>Ubud cultural tour</li>
<li>Mount Batur sunrise trek with breakfast</li>
<li>Nusa Penida island tour</li>
<li>One traditional Balinese spa session</li>
<li>Balinese cooking class</li>
</ul>""",
        "package_exclusions": """<ul>
<li>International flights</li>
<li>Lunch and dinner (except mentioned)</li>
<li>Personal expenses</li>
<li>Travel insurance</li>
<li>Indonesia visa fees</li>
<li>Tips and gratuities</li>
<li>Water sports activities</li>
</ul>""",
        "terms_and_conditions": """<p>Booking requires 30% advance payment. Full payment due 14 days before travel. Package includes complimentary flower garland welcome. Cancellation charges apply as per policy.</p>"""
    }

    packages = [singapore_package, dubai_package, bali_package]
    created_packages = []

    for package_data in packages:
        try:
            # Check if package already exists
            if frappe.db.exists("Standard Package", {"package_code": package_data["package_code"]}):
                print(f"Package {package_data['package_code']} already exists, skipping...")
                continue

            # Create the document
            doc = frappe.get_doc(package_data)
            doc.insert(ignore_permissions=True)
            frappe.db.commit()

            created_packages.append(doc.name)
            print(f"Successfully created package: {doc.package_name} ({doc.name})")

        except Exception as e:
            print(f"Error creating package {package_data.get('package_name', 'Unknown')}: {str(e)}")
            frappe.db.rollback()

    return created_packages

if __name__ == "__main__":
    # Initialize Frappe
    import sys
    sys.path.insert(0, '/Users/aakashchid/workshop/sentraBench')

    frappe.init(site='sentrav0.1.localhost')
    frappe.connect()

    try:
        created = create_standard_packages()
        print(f"\nTotal packages created: {len(created)}")
        if created:
            print(f"Package names: {', '.join(created)}")
    finally:
        frappe.destroy()