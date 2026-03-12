// Copyright (c) 2024, washmoredevelopment and contributors
// For license information, please see license.txt

frappe.ui.form.on('Configuration Result', {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.items && frm.doc.items.length > 0) {
			// Add Create BOM button if no BOM linked yet
			if (!frm.doc.bom) {
				frm.add_custom_button(__('Create BOM'), () => {
					frappe.call({
						method: 'erpnext_cpq.api.manufacturing.create_bom_from_configuration',
						args: {
							configuration_result_name: frm.doc.name,
						},
						callback: r => {
							if (r.message) {
								frappe.show_alert({
									message: __('BOM {0} created', [r.message.bom]),
									indicator: 'green',
								})
								frm.reload_doc()
							}
						},
					})
				}, __('Manufacturing'))
			} else {
				// Show link to existing BOM
				frm.add_custom_button(__('View BOM'), () => {
					frappe.set_route('Form', 'BOM', frm.doc.bom)
				}, __('Manufacturing'))
			}
		}
	},
})
