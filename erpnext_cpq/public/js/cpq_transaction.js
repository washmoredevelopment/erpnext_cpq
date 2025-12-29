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
	// Cache for item configurability to avoid repeated DB lookups
	_configurable_cache: {},

	/**
	 * Initialize CPQ handlers for a transaction form
	 * @param {Object} frm - Frappe form object
	 */
	init(frm) {
		// Add inline button hover handlers to the items grid
		this.setup_inline_buttons(frm)
		// Pre-cache configurability for all items
		this.cache_configurable_items(frm)
	},

	/**
	 * Setup hover-based inline configure buttons
	 * @param {Object} frm - Frappe form object
	 */
	setup_inline_buttons(frm) {
		const grid = frm.fields_dict.items?.grid
		if (!grid) return

		const $wrapper = grid.wrapper

		// Inject CSS for inline button (only once)
		if (!$('#cpq-inline-btn-style').length) {
			$('head').append(`
				<style id="cpq-inline-btn-style">
					.cpq-inline-configure-btn {
						position: absolute;
						right: 8px;
						top: 50%;
						transform: translateY(-50%);
						padding: 2px 8px;
						font-size: 11px;
						background: var(--primary);
						color: white;
						border: none;
						border-radius: 4px;
						cursor: pointer;
						z-index: 10;
						opacity: 0;
						transition: opacity 0.15s;
					}
					.cpq-inline-configure-btn:hover {
						background: var(--primary-dark);
					}
					.grid-row:hover .cpq-inline-configure-btn {
						opacity: 1;
					}
					.grid-row .item-code-cell {
						position: relative;
					}
				</style>
			`)
		}

		// Handle row rendering to inject buttons
		$wrapper.off('mouseenter.cpq', '.grid-row').on('mouseenter.cpq', '.grid-row', e => {
			const $row = $(e.currentTarget)
			const row_idx = $row.data('idx')
			if (!row_idx) return

			const item = (frm.doc.items || []).find(i => i.idx === row_idx)
			if (!item || !item.item_code) return

			// Check cache for configurability
			this.check_and_inject_button(frm, item, $row)
		})

		// Clean up buttons on mouse leave
		// Check relatedTarget to avoid removing button when moving to it
		$wrapper.off('mouseleave.cpq', '.grid-row').on('mouseleave.cpq', '.grid-row', e => {
			const $row = $(e.currentTarget)
			const $relatedTarget = $(e.relatedTarget)

			// Don't remove if moving to the button or its children
			if ($relatedTarget.closest('.cpq-inline-configure-btn').length) {
				return
			}
			// Don't remove if moving to a child of this row
			if ($relatedTarget.closest($row).length) {
				return
			}

			$row.find('.cpq-inline-configure-btn').remove()
		})
	},

	/**
	 * Check if item is configurable and inject button
	 */
	check_and_inject_button(frm, item, $row) {
		const item_code = item.item_code
		const cached = this._configurable_cache[item_code]

		if (cached === undefined) {
			// Not in cache yet - fetch and cache
			frappe.db.get_value('Item', item_code, ['is_configurable', 'product_configurator']).then(r => {
				if (r.message && r.message.is_configurable) {
					this._configurable_cache[item_code] = r.message.product_configurator
					item._is_configurable = true
					item._product_configurator = r.message.product_configurator
					this.inject_configure_button(frm, item, $row)
				} else {
					this._configurable_cache[item_code] = false
					item._is_configurable = false
				}
			})
		} else if (cached) {
			item._is_configurable = true
			item._product_configurator = cached
			this.inject_configure_button(frm, item, $row)
		}
	},

	/**
	 * Inject the configure button into the item_code cell
	 */
	inject_configure_button(frm, item, $row) {
		// Find the item_code cell
		const $item_code_cell = $row.find('[data-fieldname="item_code"]')
		if (!$item_code_cell.length) return

		// Don't add duplicate buttons
		if ($item_code_cell.find('.cpq-inline-configure-btn').length) return

		// Make cell relative for absolute positioning
		$item_code_cell.css('position', 'relative')

		// Create and inject button
		const btn_text = item.product_configuration ? __('Reconfigure') : __('Configure')
		const $btn = $(`<button class="cpq-inline-configure-btn">${btn_text}</button>`)

		$btn.on('click', e => {
			e.stopPropagation()
			e.preventDefault()
			const cdt = item.doctype
			const cdn = item.name
			// Use on_configure_click to ensure document is saved before opening dialog
			this.on_configure_click(frm, cdt, cdn)
		})

		// Remove button when leaving it to outside the row
		$btn.on('mouseleave', e => {
			const $relatedTarget = $(e.relatedTarget)
			// Only remove if not moving back into the row
			if (!$relatedTarget.closest($row).length) {
				$btn.remove()
			}
		})

		$item_code_cell.append($btn)
	},

	/**
	 * Cache configurability for all items on form load
	 * Uses async fetch to avoid blocking the UI thread.
	 * The check_and_inject_button fallback handles any items
	 * accessed before the cache is populated.
	 * @param {Object} frm - Frappe form object
	 */
	cache_configurable_items(frm) {
		const items = frm.doc.items || []
		const item_codes = [...new Set(items.map(i => i.item_code).filter(Boolean))]

		if (!item_codes.length) return

		// Batch fetch all item configurability asynchronously
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Item',
				filters: { name: ['in', item_codes], is_configurable: 1 },
				fields: ['name', 'product_configurator'],
			},
			callback: r => {
				if (r.message) {
					r.message.forEach(item => {
						this._configurable_cache[item.name] = item.product_configurator
					})
				}
				// Mark non-configurable items after async response
				item_codes.forEach(code => {
					if (this._configurable_cache[code] === undefined) {
						this._configurable_cache[code] = false
					}
				})
			},
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

		const item_code = item.item_code
		const cached = this._configurable_cache[item_code]

		const handle_configurable = configurator => {
			item._is_configurable = true
			item._product_configurator = configurator
			this._configurable_cache[item_code] = configurator

			// Auto-open configuration dialog for new configurable items
			// Use on_configure_click to ensure document is saved before opening dialog
			if (!item.product_configuration) {
				this.on_configure_click(frm, cdt, cdn)
			}
		}

		if (cached !== undefined) {
			if (cached) {
				handle_configurable(cached)
			} else {
				item._is_configurable = false
				item._product_configurator = null
			}
			return
		}

		frappe.db.get_value('Item', item_code, ['is_configurable', 'product_configurator']).then(r => {
			if (r.message && r.message.is_configurable) {
				handle_configurable(r.message.product_configurator)
			} else {
				item._is_configurable = false
				item._product_configurator = null
				this._configurable_cache[item_code] = false
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

		// Store configurator and idx before potential save (idx is stable across saves)
		const product_configurator = item._product_configurator
		const item_idx = item.idx

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

			// After save, temporary child names are replaced with permanent ones.
			// Re-fetch the item row by idx to get the correct cdn.
			const saved_item = (frm.doc.items || []).find(row => row.idx === item_idx)
			if (!saved_item) {
				frappe.msgprint(__('Could not find item row after save. Please try again.'))
				return
			}
			// Preserve the configurator info on the newly-named row
			saved_item._product_configurator = product_configurator
			cdn = saved_item.name
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
		// For Select fields, convert stored values back to display labels
		dialog_fields.forEach(field => {
			if (existing_selections.hasOwnProperty(field.fieldname)) {
				let value = existing_selections[field.fieldname]
				// If this is a Select field with label mapping, convert value to label
				if (field.label_to_value_map) {
					// Reverse lookup: find label for this value
					for (const [label, val] of Object.entries(field.label_to_value_map)) {
						if (val === value || val === String(value)) {
							value = label
							break
						}
					}
				}
				field.default = value
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

		// Build a combined label-to-value mapping for all Select fields
		const label_to_value_maps = {}
		dialog_fields.forEach(field => {
			if (field.label_to_value_map) {
				label_to_value_maps[field.fieldname] = field.label_to_value_map
			}
		})

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
				// Convert labels back to internal values for Select fields
				const converted_values = this.convert_labels_to_values(values, label_to_value_maps)
				this.apply_configuration(frm, cdt, cdn, converted_values, existing_config, before_state, dialog)
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

			// Update description with configuration summary
			// Remove any existing configuration summary first
			let current_desc = item.description || ''
			const summary = config_doc.configuration_summary || ''
			if (summary) {
				// Remove old configuration block if present
				// Handle legacy format (with ━ markers)
				const legacy_marker = '━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
				const firstMarkerIdx = current_desc.indexOf(legacy_marker)
				if (firstMarkerIdx !== -1) {
					const lastMarkerIdx = current_desc.lastIndexOf(legacy_marker)
					if (lastMarkerIdx > firstMarkerIdx) {
						current_desc =
							current_desc.substring(0, firstMarkerIdx) + current_desc.substring(lastMarkerIdx + legacy_marker.length)
					}
				}

				// Handle new format: "Configuration:" followed by bullet lines
				// Use regex to match the entire block
				current_desc = current_desc.replace(/Configuration:\n(• [^\n]+\n?)*/g, '')

				// Clean up extra newlines
				current_desc = current_desc.replace(/\n{3,}/g, '\n\n').trim()

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
	 * Convert Select field labels back to internal values
	 * @param {Object} values - Dialog values (may contain labels for Select fields)
	 * @param {Object} label_to_value_maps - Mapping per field {fieldname: {label: value}}
	 * @returns {Object} Values with labels converted to internal values
	 */
	convert_labels_to_values(values, label_to_value_maps) {
		const converted = { ...values }
		for (const [fieldname, mapping] of Object.entries(label_to_value_maps)) {
			if (converted.hasOwnProperty(fieldname)) {
				const label = converted[fieldname]
				if (mapping.hasOwnProperty(label)) {
					converted[fieldname] = mapping[label]
				}
			}
		}
		return converted
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
	})

	// Child table events
	frappe.ui.form.on(item_doctype, {
		item_code(frm, cdt, cdn) {
			CPQTransaction.on_item_code_change(frm, cdt, cdn)
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
