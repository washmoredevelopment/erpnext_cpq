// Copyright (c) 2024, washmoredevelopment and contributors
// For license information, please see license.txt

/**
 * CPQ Transaction Integration
 *
 * This script handles configuration dialogs for Quotation, Sales Order, and Sales Invoice.
 * It detects configurable items, shows the Configure button, and manages the configuration flow.
 */

// =============================================================================
// CONFIGURATION DIALOG HANDLER
// =============================================================================

const CPQTransaction = {
	/**
	 * Initialize CPQ handlers for a transaction form
	 * @param {Object} frm - Frappe form object
	 */
	init(frm) {
		// Refresh configure buttons visibility on form load
		this.refresh_configure_buttons(frm)
	},

	/**
	 * Refresh visibility of configure buttons for all items
	 * @param {Object} frm - Frappe form object
	 */
	refresh_configure_buttons(frm) {
		const items = frm.doc.items || []
		items.forEach((item, idx) => {
			this.update_configure_button_visibility(frm, item)
		})
	},

	/**
	 * Update configure button visibility for a single item row
	 * @param {Object} frm - Frappe form object
	 * @param {Object} item - Item row
	 */
	update_configure_button_visibility(frm, item) {
		if (!item.item_code) return

		// Check if item is configurable
		frappe.db.get_value('Item', item.item_code, ['is_configurable', 'product_configurator']).then(r => {
			if (r.message && r.message.is_configurable) {
				// Item is configurable - store configurator info on row for later use
				item._is_configurable = true
				item._product_configurator = r.message.product_configurator
				frm.refresh_field('items')
			} else {
				item._is_configurable = false
				item._product_configurator = null
			}
		})
	},

	/**
	 * Handle item_code change - check if configurable
	 * @param {Object} frm - Frappe form object
	 * @param {string} cdt - Child DocType
	 * @param {string} cdn - Child DocType name
	 */
	on_item_code_change(frm, cdt, cdn) {
		const item = frappe.get_doc(cdt, cdn)
		if (!item.item_code) {
			item._is_configurable = false
			item._product_configurator = null
			return
		}

		frappe.db.get_value('Item', item.item_code, ['is_configurable', 'product_configurator']).then(r => {
			if (r.message && r.message.is_configurable) {
				item._is_configurable = true
				item._product_configurator = r.message.product_configurator
				frm.refresh_field('items')

				// Auto-open configuration dialog for new configurable items
				if (!item.product_configuration) {
					this.open_configuration_dialog(frm, cdt, cdn)
				}
			}
		})
	},

	/**
	 * Handle configure button click
	 * @param {Object} frm - Frappe form object
	 * @param {string} cdt - Child DocType
	 * @param {string} cdn - Child DocType name
	 */
	async on_configure_click(frm, cdt, cdn) {
		const item = frappe.get_doc(cdt, cdn)

		// Ensure we have configurator info
		if (!item._product_configurator) {
			const item_data = await frappe.db.get_value('Item', item.item_code, ['is_configurable', 'product_configurator'])
			if (!item_data.message || !item_data.message.is_configurable) {
				frappe.msgprint(__('This item is not configurable.'))
				return
			}
			item._product_configurator = item_data.message.product_configurator
		}

		if (!item._product_configurator) {
			frappe.msgprint(__('No Product Configurator is linked to this item.'))
			return
		}

		// Auto-save if document is new/unsaved
		if (frm.is_new()) {
			frappe.show_alert(
				{
					message: __('{0} saved automatically for configuration', [frm.doctype]),
					indicator: 'blue',
				},
				5
			)

			await frm.save()
		}

		this.open_configuration_dialog(frm, cdt, cdn)
	},

	/**
	 * Open the configuration dialog
	 * @param {Object} frm - Frappe form object
	 * @param {string} cdt - Child DocType
	 * @param {string} cdn - Child DocType name
	 */
	async open_configuration_dialog(frm, cdt, cdn) {
		const item = frappe.get_doc(cdt, cdn)
		const configurator = item._product_configurator

		// Get dialog fields from configurator
		const fields_response = await frappe.call({
			method: 'erpnext_cpq.api.configurator.get_configurator_dialog_fields',
			args: { configurator_name: configurator },
		})

		const dialog_fields = fields_response.message || []

		if (!dialog_fields.length) {
			frappe.msgprint(__('No configuration options defined for this product.'))
			return
		}

		// Check if document is submitted (read-only mode)
		const is_submitted = frm.doc.docstatus === 1
		const existing_config = item.product_configuration

		// Pre-fill with existing selections if re-configuring
		let existing_selections = {}
		let before_state = {}
		if (existing_config) {
			const selections_response = await frappe.call({
				method: 'erpnext_cpq.api.configurator.get_configuration_selections',
				args: { configuration_name: existing_config },
			})
			existing_selections = selections_response.message || {}
			// Store before state for change tracking
			before_state = JSON.parse(JSON.stringify(existing_selections))
		}

		// Apply existing values to fields
		dialog_fields.forEach(field => {
			if (existing_selections.hasOwnProperty(field.fieldname)) {
				field.default = existing_selections[field.fieldname]
			}
			// Make fields read-only if document is submitted
			if (is_submitted) {
				field.read_only = 1
			}
		})

		// Add read-only notice for submitted documents
		if (is_submitted) {
			dialog_fields.unshift({
				fieldtype: 'HTML',
				fieldname: 'submitted_notice',
				options:
					'<div class="alert alert-info">' +
					__('This configuration has been submitted and cannot be modified.') +
					'</div>',
			})
		}

		// Create dialog
		const dialog = new frappe.ui.Dialog({
			title: __('Configure Product'),
			fields: dialog_fields,
			size: 'large',
			primary_action_label: is_submitted ? __('Close') : __('Apply Configuration'),
			primary_action: values => {
				if (is_submitted) {
					dialog.hide()
					return
				}
				this.apply_configuration(frm, cdt, cdn, values, existing_config, before_state, dialog)
			},
		})

		// Hide secondary action for submitted documents
		if (is_submitted) {
			dialog.$wrapper.find('.btn-modal-secondary').hide()
		}

		dialog.show()
	},

	/**
	 * Apply configuration selections
	 * @param {Object} frm - Frappe form object
	 * @param {string} cdt - Child DocType
	 * @param {string} cdn - Child DocType name
	 * @param {Object} values - Dialog values
	 * @param {string|null} existing_config - Existing configuration name
	 * @param {Object} before_state - Selections before changes (for tracking)
	 * @param {Object} dialog - Dialog instance
	 */
	async apply_configuration(frm, cdt, cdn, values, existing_config, before_state, dialog) {
		const item = frappe.get_doc(cdt, cdn)
		const configurator = item._product_configurator

		frappe.show_alert({
			message: __('Applying configuration...'),
			indicator: 'blue',
		})

		try {
			let config_name
			let change_diff = null

			if (existing_config) {
				// Update existing configuration
				const update_response = await frappe.call({
					method: 'erpnext_cpq.api.configurator.update_configuration',
					args: {
						configuration_name: existing_config,
						selections: values,
					},
				})
				config_name = existing_config
				change_diff = update_response.message?.changes || null

				// Post change comment to parent document if there were changes
				if (change_diff && change_diff.length > 0) {
					await this.post_change_comment(frm, item, change_diff)
				}
			} else {
				// Create new configuration
				const create_response = await frappe.call({
					method: 'erpnext_cpq.api.configurator.create_configuration',
					args: {
						configurator: configurator,
						selections: values,
						parent_doctype: frm.doctype,
						parent_name: frm.doc.name,
						parent_item_row: cdn,
					},
				})
				config_name = create_response.message
			}

			// Evaluate configuration to get pricing
			const eval_response = await frappe.call({
				method: 'erpnext_cpq.api.configurator.evaluate_configuration',
				args: {
					configuration_name: config_name,
					price_list: frm.doc.selling_price_list || frm.doc.price_list,
					customer: frm.doc.customer || frm.doc.party_name,
					company: frm.doc.company,
				},
			})

			const result_name = eval_response.message

			// Get the result details
			const result_doc = await frappe.db.get_doc('Configuration Result', result_name)
			const config_doc = await frappe.db.get_doc('Product Configuration', config_name)

			// Update line item
			frappe.model.set_value(cdt, cdn, 'product_configuration', config_name)
			frappe.model.set_value(cdt, cdn, 'configuration_result', result_name)
			frappe.model.set_value(cdt, cdn, 'rate', result_doc.total || 0)

			// Append configuration summary to description
			const current_desc = item.description || ''
			const summary = config_doc.configuration_summary || ''
			if (summary) {
				const new_desc = current_desc ? current_desc + '\n\n' + summary : summary
				frappe.model.set_value(cdt, cdn, 'description', new_desc)
			}

			frm.refresh_field('items')

			frappe.show_alert(
				{
					message: __('Configuration applied successfully'),
					indicator: 'green',
				},
				5
			)

			dialog.hide()
		} catch (error) {
			frappe.msgprint({
				title: __('Configuration Error'),
				message: error.message || __('Failed to apply configuration'),
				indicator: 'red',
			})
		}
	},

	/**
	 * Post a comment to the document about configuration changes
	 * @param {Object} frm - Frappe form object
	 * @param {Object} item - Item row
	 * @param {Array} diff - Array of change objects
	 */
	async post_change_comment(frm, item, diff) {
		if (!diff || diff.length === 0) return

		const changes = diff.map(d => `<li><strong>${d.option}</strong>: ${d.from} → ${d.to}</li>`).join('')

		const comment = `<p>Configuration updated for <strong>${item.item_code}</strong> (Row ${item.idx}):</p><ul>${changes}</ul>`

		await frappe.call({
			method: 'frappe.desk.form.utils.add_comment',
			args: {
				reference_doctype: frm.doctype,
				reference_name: frm.doc.name,
				content: comment,
				comment_email: frappe.session.user,
			},
		})

		// Refresh comments
		frm.timeline.refresh()
	},
}

// =============================================================================
// FORM EVENT HANDLERS
// =============================================================================

/**
 * Setup CPQ handlers for a transaction doctype
 * @param {string} doctype - Parent doctype (Quotation, Sales Order, Sales Invoice)
 * @param {string} item_doctype - Child doctype (Quotation Item, Sales Order Item, etc.)
 */
function setup_cpq_handlers(doctype, item_doctype) {
	// Parent form events
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			CPQTransaction.init(frm)
		},

		onload(frm) {
			CPQTransaction.refresh_configure_buttons(frm)
		},
	})

	// Child table events
	frappe.ui.form.on(item_doctype, {
		item_code(frm, cdt, cdn) {
			CPQTransaction.on_item_code_change(frm, cdt, cdn)
		},

		configure_btn(frm, cdt, cdn) {
			CPQTransaction.on_configure_click(frm, cdt, cdn)
		},

		items_add(frm, cdt, cdn) {
			// Handle new row added
		},

		items_remove(frm, cdt, cdn) {
			// Handle row removed - could clean up orphan configurations
		},
	})
}

// =============================================================================
// REGISTER HANDLERS FOR ALL TRANSACTION TYPES
// =============================================================================

// Quotation
setup_cpq_handlers('Quotation', 'Quotation Item')

// Sales Order
setup_cpq_handlers('Sales Order', 'Sales Order Item')

// Sales Invoice
setup_cpq_handlers('Sales Invoice', 'Sales Invoice Item')
