import frappe
from frappe import _

@frappe.whitelist()
def get_packages_with_destinations():
    """Get all Standard Packages with their destinations in a single API call"""

    # Get all packages
    packages = frappe.get_list(
        "Standard Package",
        fields=[
            'name', 'package_name', 'package_code', 'status', 'package_type',
            'no_of_days', 'no_of_nights', 'base_cost', 'currency',
            'hero_image', 'hero_description', 'description',
            'highlights', 'gallery_images', 'modified',
            'popularity_score', 'rating', 'review_count', 'category'
        ],
        order_by='modified desc',
        limit=100
    )

    # For each package, get its destinations
    for pkg in packages:
        # Get destinations child table
        destinations = frappe.get_all(
            "Trip Destination",
            filters={"parent": pkg["name"], "parenttype": "Standard Package"},
            fields=["destination", "nights", "sequence"],
            order_by="idx"
        )

        # Add destinations list to package
        pkg["destinations"] = destinations

        # Create a comma-separated string for easy display
        pkg["destinations_text"] = ", ".join([d["destination"] for d in destinations])

    return packages