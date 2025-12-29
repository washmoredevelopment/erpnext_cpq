// Copyright (c) 2024, washmoredevelopment and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Configurator', {
	refresh(frm) {
		update_option_choices_select(frm)
		update_item_rules_selects(frm)
		sort_option_choices(frm)
	},
	options_add(frm, cdt, cdn) {
		// Update the Select options when a new option is added
		update_option_choices_select(frm)
		update_item_rules_selects(frm)
	},
	options_remove(frm, cdt, cdn) {
		// Update the Select options when an option is removed
		update_option_choices_select(frm)
		update_item_rules_selects(frm)
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
		update_item_rules_selects(frm)
	},
	option_choices_remove(frm, cdt, cdn) {
		update_item_rules_selects(frm)
	},
})

frappe.ui.form.on('Configurator Option', {
	label(frm, cdt, cdn) {
		// Auto-generate option_name from label if option_name is empty or matches previous auto-generated value
		const row = frappe.get_doc(cdt, cdn)
		const new_slug = slugify(row.label || '')

		// Only auto-fill if option_name is empty or was previously auto-generated
		if (!row.option_name || row._auto_generated_name === row.option_name) {
			frappe.model.set_value(cdt, cdn, 'option_name', new_slug)
			row._auto_generated_name = new_slug
		}
		update_option_choices_select(frm)
	},
	option_name(frm, cdt, cdn) {
		// Update the Select options when an option name changes
		update_option_choices_select(frm)
	},
})

frappe.ui.form.on('Option Choice', {
	label(frm, cdt, cdn) {
		// Auto-generate value from label if value is empty or matches previous auto-generated value
		const row = frappe.get_doc(cdt, cdn)
		const new_slug = slugify(row.label || '')

		// Only auto-fill if value is empty or was previously auto-generated
		if (!row.value || row._auto_generated_value === row.value) {
			frappe.model.set_value(cdt, cdn, 'value', new_slug)
			row._auto_generated_value = new_slug
		}
	},
	option_name(frm, cdt, cdn) {
		sort_option_choices(frm)
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

frappe.ui.form.on('Configurator Item Rule', {
	option_name(frm, cdt, cdn) {
		// When option_name changes, update the option_value choices
		update_option_value_for_row(frm, cdt, cdn)
	},
})

/**
 * Update Item Rules Select fields (option_name, qty_from_option, description_from_option)
 */
function update_item_rules_selects(frm) {
	if (!frm.fields_dict.item_rules) return

	// Build options list from the Options table (with empty option at start)
	const option_names = [''].concat((frm.doc.options || []).map(opt => opt.option_name).filter(name => name))
	const options_str = option_names.join('\n')

	// Update all option-related Select fields in item_rules grid
	frm.fields_dict.item_rules.grid.update_docfield_property('option_name', 'options', options_str)
	frm.fields_dict.item_rules.grid.update_docfield_property('qty_from_option', 'options', options_str)
	frm.fields_dict.item_rules.grid.update_docfield_property('description_from_option', 'options', options_str)

	frm.fields_dict.item_rules.grid.refresh()
}

/**
 * Update option_value choices for a specific item rule row based on selected option_name
 */
function update_option_value_for_row(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn)
	const selected_option = row.option_name

	if (!selected_option) {
		// Clear option_value choices if no option selected
		return
	}

	// Get choices for the selected option
	const choices = (frm.doc.option_choices || [])
		.filter(c => c.option_name === selected_option)
		.map(c => c.value)
		.filter(v => v)

	// Add empty option at start
	const choices_str = [''].concat(choices).join('\n')

	// Update this specific row's option_value field
	// Since we can't update per-row, we update the grid column
	// But the available choices shown should still be helpful
	frm.fields_dict.item_rules.grid.update_docfield_property('option_value', 'options', choices_str)
	frm.fields_dict.item_rules.grid.refresh()
}

/**
 * Convert a label string to a slug (lowercase with underscores)
 * e.g., "Processor Type" -> "processor_type"
 */
function slugify(str) {
	return str
		.toLowerCase()
		.trim()
		.replace(/[^\w\s-]/g, '') // Remove non-word chars except spaces and hyphens
		.replace(/[\s-]+/g, '_') // Replace spaces and hyphens with underscores
		.replace(/^_+|_+$/g, '') // Remove leading/trailing underscores
}
