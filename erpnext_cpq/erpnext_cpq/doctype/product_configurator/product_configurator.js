// Copyright (c) 2024, washmoredevelopment and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Configurator', {
	refresh(frm) {
		update_option_choices_select(frm)
		sort_option_choices(frm)
	},
	options_add(frm, cdt, cdn) {
		// Update the Select options when a new option is added
		update_option_choices_select(frm)
	},
	options_remove(frm, cdt, cdn) {
		// Update the Select options when an option is removed
		update_option_choices_select(frm)
	},
})

frappe.ui.form.on('Configurator Option', {
	option_name(frm, cdt, cdn) {
		// Update the Select options when an option name changes
		update_option_choices_select(frm)
	},
})

frappe.ui.form.on('Option Choice', {
	option_name(frm, cdt, cdn) {
		sort_option_choices(frm)
	},
	option_choices_add(frm, cdt, cdn) {
		// Auto-fill option_name from last row for convenience
		const rows = frm.doc.option_choices || []
		if (rows.length > 1) {
			const prev_row = rows[rows.length - 2]
			const new_row = frappe.get_doc(cdt, cdn)
			if (prev_row.option_name && !new_row.option_name) {
				frappe.model.set_value(cdt, cdn, 'option_name', prev_row.option_name)
			}
		}
	},
})

function update_option_choices_select(frm) {
	// Build options list from the Options table
	const option_names = (frm.doc.options || []).map(opt => opt.option_name).filter(name => name) // Filter out empty names

	// Create newline-separated options string for Select field
	const options_str = option_names.join('\n')

	// Update the option_name field options in the Option Choice grid
	frm.fields_dict.option_choices.grid.update_docfield_property('option_name', 'options', options_str)

	// Refresh the grid to show updated options
	frm.fields_dict.option_choices.grid.refresh()
}

function sort_option_choices(frm) {
	if (!frm.doc.option_choices?.length) return

	// Sort by option_name to keep related choices grouped
	frm.doc.option_choices.sort((a, b) => (a.option_name || '').localeCompare(b.option_name || ''))

	// Update idx to match new order
	frm.doc.option_choices.forEach((row, index) => {
		row.idx = index + 1
	})

	frm.refresh_field('option_choices')
}
