frappe.ui.form.on('Requirement', {
    // This function will run when the 'use_standard_package' field's value changes
    use_standard_package: function(frm) {
        
        // LOG 1: Check if the script is triggering
        console.log("🐛 Script triggered! Package field changed.");
        
        if (frm.doc.use_standard_package) {
            // LOG 2: Check the value of the selected package
            console.log("🐛 Selected Package:", frm.doc.use_standard_package);

            frappe.show_alert({ message: __('Fetching Package Details...'), indicator: 'gray' });
            frm.set_df_property('use_standard_package', 'read_only', 1);

            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Standard Package',
                    name: frm.doc.use_standard_package
                },
                callback: function(r) {
                    // LOG 3: IMPORTANT! Check the server's response
                    console.log("🐛 Server Response:", r);

                    if (r.message) {
                        console.log("✅ Server returned data. Populating form...");
                        let package_doc = r.message;

                        // Clear existing data first
                        frm.clear_table('destination_city');
                        frm.clear_table('activity');
                        frm.clear_table('daywise_plan');

                        // Populate the fields
                        frm.set_value('budget', package_doc.price);
                        
                        // Populate Child Tables
                        if (package_doc.destinations && package_doc.destinations.length > 0) {
                            package_doc.destinations.forEach(function(dest_row) {
                                frm.add_child('destination_city', {
                                    destination: dest_row.destination,
                                    number_of_nights: dest_row.number_of_nights
                                });
                            });
                        }

                        if (package_doc.activities && package_doc.activities.length > 0) {
                             package_doc.activities.forEach(function(act_row) {
                                frm.add_child('activity', {
                                    activity: act_row.activity
                                });
                            });
                        }
                        
                        if (package_doc.daywise_plan && package_doc.daywise_plan.length > 0) {
                             package_doc.daywise_plan.forEach(function(plan_row) {
                                frm.add_child('daywise_plan', {
                                    day: plan_row.day,
                                    description: plan_row.description
                                });
                            });
                        }

                        // Refresh the display
                        frm.refresh_field('destination_city');
                        frm.refresh_field('activity');
                        frm.refresh_field('daywise_plan');
                        
                        frappe.show_alert({ message: __('Package details loaded.'), indicator: 'green' });
                    } else {
                        console.error("❌ Server did not return any data in r.message.");
                    }
                },
                error: function(r) {
                    // LOG 4: Catch any server-side errors
                    console.error("❌ Error during server call:", r);
                },
                always: function() {
                    frm.set_df_property('use_standard_package', 'read_only', 0);
                }
            });
        } else {
            // LOG 5: Check if the field is being cleared
            console.log("🐛 Package field cleared. Clearing form data.");
            
            frm.set_value('budget', 0);
            frm.clear_table('destination_city');
            frm.clear_table('activity');
            frm.clear_table('daywise_plan');
            frm.refresh_field('destination_city');
            frm.refresh_field('activity');
            frm.refresh_field('daywise_plan');
        }
    }
});