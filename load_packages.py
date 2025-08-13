#!/usr/bin/env python3
"""
Script to load Standard Package fixtures into the database
"""
import frappe
import json
from frappe.utils import now

# Connect to Frappe
frappe.init(site="sentra.localhost")
frappe.connect()

def load_standard_packages():
    """Load standard packages from fixture file"""
    
    # Read the fixture file
    with open("crm/fixtures/standard_package.json", "r") as f:
        packages_data = json.load(f)
    
    success_count = 0
    error_count = 0
    
    for pkg_data in packages_data:
        try:
            # Check if package already exists
            if frappe.db.exists("Standard Package", pkg_data["name"]):
                print(f"Package {pkg_data['name']} already exists, skipping...")
                continue
            
            # Create the package document
            package = frappe.new_doc("Standard Package")
            
            # Set basic fields
            for field in ["name", "package_name", "package_code", "status", "dmc", "description", 
                         "valid_from", "valid_to", "min_group_size", "max_group_size", 
                         "no_of_days", "no_of_nights", "currency", "base_cost", 
                         "markup_percentage", "hotel", "terms_and_conditions", "notes"]:
                if field in pkg_data:
                    setattr(package, field, pkg_data[field])
            
            # Set itinerary_data as JSON
            if "itinerary_data" in pkg_data:
                package.itinerary_data = json.dumps(pkg_data["itinerary_data"])
            
            # Add destinations with proper structure
            if "destinations" in pkg_data:
                for dest in pkg_data["destinations"]:
                    package.append("destinations", {
                        "destination": dest["destination"],
                        "nights": dest["nights"],
                        "sequence": dest.get("sequence", 1)
                    })
            
            # Save the package
            package.insert(ignore_permissions=True)
            frappe.db.commit()
            
            print(f"✅ Successfully loaded: {package.package_name} ({package.name})")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error loading {pkg_data.get('name', 'unknown')}: {str(e)}")
            error_count += 1
            frappe.db.rollback()
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Successfully loaded: {success_count} packages")
    print(f"   ❌ Failed: {error_count} packages")
    
    return success_count, error_count

if __name__ == "__main__":
    print("🚀 Loading Standard Packages...")
    print("=" * 50)
    
    try:
        success, errors = load_standard_packages()
        
        if success > 0:
            print(f"\n✨ Done! {success} packages are now available in the system.")
        else:
            print("\n⚠️ No packages were loaded. They might already exist.")
            
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
    finally:
        frappe.destroy()