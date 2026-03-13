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
	// MutationObserver for watching .link-btn elements
	_observer: null,
	// Reference to the current form for cleanup
	_current_frm: null,

	/**
	 * Initialize CPQ handlers for a transaction form
	 * @param {Object} frm - Frappe form object
	 */
	init(frm) {
		// Clear cache on each init to avoid stale values across navigations
		this._configurable_cache = {}
		this._current_frm = frm

		// Inject CSS for inline button (only once)
		this.inject_styles()
		// Pre-cache configurability for all items
		this.cache_configurable_items(frm)
		// Setup MutationObserver to watch for .link-btn elements
		this.setup_link_btn_observer(frm)
		// Add visual indicators after a short delay to allow grid to render
		setTimeout(() => this.add_row_indicators(frm), 500)
	},

	/**
	 * Clean up observers and caches when navigating away
	 */
	cleanup() {
		if (this._observer) {
			this._observer.disconnect()
			this._observer = null
		}
		this._current_frm = null
	},

	/**
	 * Inject CSS styles for the configure button
	 */
	inject_styles() {
		if ($('#cpq-btn-style').length) return

		$('head').append(`
			<style id="cpq-btn-style">
				.cpq-configure-btn {
					padding: 2px 6px;
					font-size: 10px;
					background: var(--primary);
					color: white !important;
					border-radius: 3px;
					cursor: pointer;
					margin-right: 4px;
					text-decoration: none !important;
				}
				.cpq-configure-btn:hover {
					background: var(--primary);
				}
			</style>
		`)
	},

	/**
	 * Setup MutationObserver to watch for .link-btn elements appearing in the grid
	 * This hooks into Frappe's Link field creation when a row enters edit mode
	 * @param {Object} frm - Frappe form object
	 */
	setup_link_btn_observer(frm) {
		const grid = frm.fields_dict.items?.grid
		if (!grid) return

		// Disconnect any existing observer
		if (this._observer) {
			this._observer.disconnect()
			this._observer = null
		}

		// Watch for .link-btn elements appearing in the grid
		this._observer = new MutationObserver(mutations => {
			for (const mutation of mutations) {
				for (const node of mutation.addedNodes) {
					if (node.nodeType !== Node.ELEMENT_NODE) continue

					// Check if this is a link-btn or contains one
					const $node = $(node)
					const $linkBtns = $node.is('.link-btn') ? $node : $node.find('.link-btn')

					$linkBtns.each((_, el) => {
						this.maybe_inject_configure_button(frm, $(el))
					})
				}
			}
		})

		// Observe the grid body for DOM changes
		this._observer.observe(grid.wrapper[0], {
			childList: true,
			subtree: true,
		})
	},

	/**
	 * Check if the .link-btn is for item_code and if the item is configurable
	 * @param {Object} frm - Frappe form object
	 * @param {jQuery} $link_btn - The .link-btn jQuery element
	 */
	maybe_inject_configure_button(frm, $link_btn) {
		// Find the parent cell and check if this is for item_code
		const $cell = $link_btn.closest('[data-fieldname="item_code"]')
		if (!$cell.length) return

		const $row = $link_btn.closest('.grid-row')
		const row_idx = $row.data('idx')
		if (!row_idx) return

		const item = (frm.doc.items || []).find(i => i.idx === row_idx)
		if (!item?.item_code) return

		// Check configurability and add button
		const cached = this._configurable_cache[item.item_code]
		if (cached) {
			item._product_configurator = cached
			this.add_configure_button_to_link_btn(frm, item, $link_btn)
		} else if (cached === undefined) {
			// Fetch and cache if not yet known
			frappe.db.get_value('Item', item.item_code, ['is_configurable', 'product_configurator']).then(r => {
				if (r.message?.is_configurable) {
					this._configurable_cache[item.item_code] = r.message.product_configurator
					item._product_configurator = r.message.product_configurator
					this.add_configure_button_to_link_btn(frm, item, $link_btn)
				} else {
					this._configurable_cache[item.item_code] = false
				}
			})
		}
	},

	/**
	 * Get the appropriate button text for a given item
	 * @param {Object} frm - Frappe form object
	 * @param {Object} item - The item row doc
	 * @returns {string} The button text
	 */
	get_button_text(frm, item) {
		if (frm.doc.docstatus === 1) {
			return __('View Configuration')
		}
		return item.product_configuration ? __('Reconfigure') : __('Configure')
	},

	/**
	 * Add the configure button to a .link-btn span
	 * @param {Object} frm - Frappe form object
	 * @param {Object} item - The item row doc
	 * @param {jQuery} $link_btn - The .link-btn jQuery element
	 */
	add_configure_button_to_link_btn(frm, item, $link_btn) {
		// Don't add duplicate buttons
		if ($link_btn.find('.cpq-configure-btn').length) return

		// Create configure button
		const btn_text = this.get_button_text(frm, item)
		const $btn = $(`<a class="cpq-configure-btn" title="${btn_text}">${btn_text}</a>`)

		$btn.on('click', e => {
			e.stopPropagation()
			e.preventDefault()
			this.on_configure_click(frm, item.doctype, item.name)
		})

		// Prepend as first element in the link-btn span
		$link_btn.prepend($btn)

		// Add breakdown button after configure button if configuration exists
		if (item.configuration_result) {
			const $breakdown_btn = $(
				`<a class="cpq-configure-btn" title="${__('View Breakdown')}" style="background: var(--text-muted);">${__('Breakdown')}</a>`
			)
			$breakdown_btn.on('click', e => {
				e.stopPropagation()
				e.preventDefault()
				this.show_breakdown_dialog(frm, item.doctype, item.name)
			})
			$btn.after($breakdown_btn)
		}
	},

	/**
	 * Update the configure button text for a specific item row
	 * @param {Object} frm - Frappe form object
	 * @param {Object} item - The item row doc
	 */
	update_configure_button_text(frm, item) {
		const $grid = frm.fields_dict.items?.grid?.wrapper
		if (!$grid) return

		const $row = $grid.find(`.grid-row[data-idx="${item.idx}"]`)
		if (!$row.length) return

		const $btn = $row.find('[data-fieldname="item_code"] .link-btn .cpq-configure-btn')
		if (!$btn.length) return

		const btn_text = this.get_button_text(frm, item)
		$btn.text(btn_text).attr('title', btn_text)
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

			try {
				await frm.save()
			} catch (save_error) {
				frappe.msgprint({
					title: __('Save Failed'),
					message: __('Could not save the document. Please fix any errors and try again.'),
					indicator: 'red',
				})
				return
			}

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

		// Add template selector and read-only notice for submitted documents
		if (!is_submitted) {
			dialog_fields.unshift({
				fieldtype: 'HTML',
				fieldname: 'template_section',
				options: `<div class="cpq-template-section" style="margin-bottom: 15px;">
					<button class="btn btn-xs btn-default cpq-load-template-btn">${__('Load Template')}</button>
					<button class="btn btn-xs btn-default cpq-save-template-btn" style="margin-left: 5px;">${__('Save as Template')}</button>
				</div>`,
			})
		}

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

		// Bind template buttons
		if (!is_submitted) {
			dialog.$wrapper.find('.cpq-load-template-btn').on('click', () => {
				this._load_template(dialog, configurator, label_to_value_maps)
			})
			dialog.$wrapper.find('.cpq-save-template-btn').on('click', () => {
				this._save_as_template(dialog, configurator, label_to_value_maps)
			})
		}
	},

	/**
	 * Load a template into the configuration dialog
	 */
	async _load_template(dialog, configurator, label_to_value_maps) {
		const templates = await frappe.call({
			method: 'erpnext_cpq.api.configurator.get_templates',
			args: { configurator_name: configurator },
		})

		const template_list = templates.message || []
		if (!template_list.length) {
			frappe.msgprint(__('No templates found for this configurator.'))
			return
		}

		const template_dialog = new frappe.ui.Dialog({
			title: __('Select Template'),
			fields: [
				{
					fieldtype: 'Select',
					fieldname: 'template',
					label: __('Template'),
					options: template_list.map(t => t.template_name).join('\n'),
					reqd: 1,
				},
			],
			primary_action_label: __('Load'),
			primary_action: async values => {
				const selected = template_list.find(t => t.template_name === values.template)
				if (selected && selected.selections) {
					for (const sel of selected.selections) {
						let value = sel.value
						// Convert value to label for Select fields
						if (label_to_value_maps[sel.option_name]) {
							const map = label_to_value_maps[sel.option_name]
							for (const [label, val] of Object.entries(map)) {
								if (val === value) {
									value = label
									break
								}
							}
						}
						await dialog.set_value(sel.option_name, value)
					}
					frappe.show_alert({ message: __('Template loaded'), indicator: 'green' })
				}
				template_dialog.hide()
			},
		})
		template_dialog.show()
	},

	/**
	 * Save current dialog values as a template
	 */
	async _save_as_template(dialog, configurator, label_to_value_maps) {
		const raw_values = dialog.get_values()
		if (!raw_values) return
		const values = this.convert_labels_to_values(raw_values, label_to_value_maps)

		const name_dialog = new frappe.ui.Dialog({
			title: __('Save as Template'),
			fields: [
				{
					fieldtype: 'Data',
					fieldname: 'template_name',
					label: __('Template Name'),
					reqd: 1,
				},
			],
			primary_action_label: __('Save'),
			primary_action: async name_values => {
				await frappe.call({
					method: 'erpnext_cpq.api.configurator.save_as_template',
					args: {
						configurator_name: configurator,
						template_name: name_values.template_name,
						selections: values,
					},
				})
				frappe.show_alert({ message: __('Template saved'), indicator: 'green' })
				name_dialog.hide()
			},
		})
		name_dialog.show()
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

		dialog.disable_primary_action()

		frappe.show_alert({
			message: __('Applying configuration...'),
			indicator: 'blue',
		})

		try {
			let config_name
			let config_summary = ''
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
				const create_result = create_response.message
				config_name = create_result.name
				config_summary = create_result.configuration_summary || ''
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

			const eval_result = eval_response.message
			const result_name = eval_result.name
			const result_total = eval_result.total || 0
			const summary = config_summary || eval_result.configuration_summary || ''

			// Update line item - await each set_value for correct ordering
			await frappe.model.set_value(cdt, cdn, 'product_configuration', config_name)
			await frappe.model.set_value(cdt, cdn, 'configuration_result', result_name)

			// Update description with configuration summary
			let current_desc = item.description || ''
			if (summary) {
				current_desc = this.strip_configuration_block(current_desc)
				const wrapped_summary = `<!-- CPQ_CONFIG_START -->${summary}<!-- CPQ_CONFIG_END -->`
				const new_desc = current_desc ? current_desc + '\n\n' + wrapped_summary : wrapped_summary
				await frappe.model.set_value(cdt, cdn, 'description', new_desc)
			}

			// Set all rate fields to prevent ERPNext async handlers from overwriting
			const rate = result_total
			await frappe.model.set_value(cdt, cdn, 'price_list_rate', rate)
			await frappe.model.set_value(cdt, cdn, 'base_price_list_rate', rate)
			await frappe.model.set_value(cdt, cdn, 'base_rate', rate)
			await frappe.model.set_value(cdt, cdn, 'rate', rate)

			frm.dirty()
			frm.refresh_field('items')

			// Update button text to reflect new state
			const updated_item = frappe.get_doc(cdt, cdn)
			this.update_configure_button_text(frm, updated_item)

			frappe.show_alert(
				{
					message: __('Configuration applied successfully'),
					indicator: 'green',
				},
				5
			)

			dialog.hide()

			// Auto-save to persist configuration immediately
			await frm.save()
		} catch (error) {
			frappe.msgprint({
				title: __('Configuration Error'),
				message: error.message || __('Failed to apply configuration'),
				indicator: 'red',
			})
		} finally {
			dialog.enable_primary_action()
		}
	},

	/**
	 * Strip configuration summary block from a description string.
	 * Handles plain text, HTML-encoded content, and varying line endings.
	 * @param {string} desc - The current description
	 * @returns {string} Description with configuration block removed
	 */
	strip_configuration_block(desc) {
		if (!desc) return ''

		// Primary: use HTML comment markers
		const markerRegex = /<!-- CPQ_CONFIG_START -->[\s\S]*?<!-- CPQ_CONFIG_END -->/g
		desc = desc.replace(markerRegex, '')

		// Legacy fallback: handle old format (with ━ markers)
		const legacy_marker = '━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
		const firstMarkerIdx = desc.indexOf(legacy_marker)
		if (firstMarkerIdx !== -1) {
			const lastMarkerIdx = desc.lastIndexOf(legacy_marker)
			if (lastMarkerIdx > firstMarkerIdx) {
				desc = desc.substring(0, firstMarkerIdx) + desc.substring(lastMarkerIdx + legacy_marker.length)
			}
		}

		// Legacy fallback: "Configuration:" followed by bullet lines
		desc = desc.replace(
			/Configuration:\s*(?:(?:<br\s*\/?>|\r?\n)\s*(?:•|&#8226;|&bull;)\s*[^\n<]+)*/gi,
			''
		)

		// Clean up extra whitespace and line breaks
		desc = desc.replace(/(<br\s*\/?>){3,}/gi, '<br><br>')
		desc = desc.replace(/(\r?\n){3,}/g, '\n\n')
		desc = desc.trim()

		return desc
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
	/**
	 * Escape HTML special characters to prevent XSS
	 * @param {string} str - String to escape
	 * @returns {string} Escaped string
	 */
	escape_html(str) {
		if (!str) return ''
		const div = document.createElement('div')
		div.appendChild(document.createTextNode(str))
		return div.innerHTML
	},

	async post_change_comment(frm, item, diff) {
		if (!diff || diff.length === 0) return

		const esc = v => this.escape_html(String(v ?? ''))
		const changes = diff.map(d => `<li><strong>${esc(d.option)}</strong>: ${esc(d.from)} → ${esc(d.to)}</li>`).join('')

		const comment = `<p>Configuration updated for <strong>${esc(item.item_code)}</strong> (Row ${item.idx}):</p><ul>${changes}</ul>`

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

	/**
	 * Clear the configuration cache entry for a specific item code
	 * @param {string} item_code - The item code to clear
	 */
	clear_cache_for_item(item_code) {
		if (item_code && this._configurable_cache.hasOwnProperty(item_code)) {
			delete this._configurable_cache[item_code]
		}
	},

	/**
	 * Show breakdown dialog for a configured item
	 * @param {Object} frm - Frappe form object
	 * @param {string} cdt - Child DocType
	 * @param {string} cdn - Child DocType name
	 */
	async show_breakdown_dialog(frm, cdt, cdn) {
		const item = frappe.get_doc(cdt, cdn)
		if (!item.configuration_result) {
			frappe.msgprint(__('No configuration result found for this item.'))
			return
		}

		const response = await frappe.call({
			method: 'erpnext_cpq.api.breakdown.get_configuration_breakdown',
			args: { configuration_result_name: item.configuration_result },
		})

		const data = response.message
		if (!data || !data.items || !data.items.length) {
			frappe.msgprint(__('No component items found.'))
			return
		}

		// Build table HTML
		let table_html = `
			<table class="table table-bordered table-condensed" style="margin-bottom: 10px;">
				<thead>
					<tr>
						<th>${__('Item')}</th>
						<th>${__('Item Name')}</th>
						<th class="text-right">${__('Qty')}</th>
						<th>${__('UOM')}</th>
						<th class="text-right">${__('Rate')}</th>
						<th class="text-right">${__('Amount')}</th>
					</tr>
				</thead>
				<tbody>`

		const esc = v => this.escape_html(String(v ?? ''))
		const fmt = (val, currency) => format_currency(val, currency)

		for (const comp of data.items) {
			table_html += `
				<tr>
					<td>${esc(comp.item_code)}</td>
					<td>${esc(comp.item_name)}</td>
					<td class="text-right">${comp.qty}</td>
					<td>${esc(comp.uom)}</td>
					<td class="text-right">${fmt(comp.rate, data.currency)}</td>
					<td class="text-right">${fmt(comp.amount, data.currency)}</td>
				</tr>`
		}

		table_html += `
				</tbody>
				<tfoot>
					<tr>
						<td colspan="5" class="text-right"><strong>${__('Total')}</strong></td>
						<td class="text-right"><strong>${fmt(data.total, data.currency)}</strong></td>
					</tr>
				</tfoot>
			</table>`

		if (data.configuration_summary) {
			table_html += `<div class="text-muted" style="white-space: pre-line;">${esc(data.configuration_summary)}</div>`
		}

		const dialog = new frappe.ui.Dialog({
			title: __('Configuration Breakdown - {0} (Row {1})', [item.item_code, item.idx]),
			size: 'large',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'breakdown_html',
					options: table_html,
				},
			],
			primary_action_label: __('Close'),
			primary_action: () => dialog.hide(),
		})
		dialog.show()
	},

	/**
	 * Add visual indicators to configured item rows
	 * @param {Object} frm - Frappe form object
	 */
	add_row_indicators(frm) {
		const $grid = frm.fields_dict.items?.grid?.wrapper
		if (!$grid) return

		for (const item of frm.doc.items || []) {
			if (!item.item_code) continue

			const is_configurable = this._configurable_cache[item.item_code]
			if (!is_configurable) continue

			const $row = $grid.find(`.grid-row[data-idx="${item.idx}"]`)
			if (!$row.length) continue

			// Remove existing indicators
			$row.find('.cpq-indicator').remove()

			const has_config = !!item.product_configuration
			const color = has_config ? 'var(--green-600, green)' : 'var(--orange-500, orange)'
			const tooltip = has_config ? __('Configured') : __('Needs configuration')

			const $indicator = $(
				`<span class="cpq-indicator" style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${color}; margin-right: 4px; vertical-align: middle;" title="${tooltip}"></span>`
			)

			const $cell = $row.find('[data-fieldname="item_code"] .static-area')
			if ($cell.length && !$cell.find('.cpq-indicator').length) {
				$cell.prepend($indicator)
			}
		}
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
			// Cleanup observer when navigating away (SPA navigation)
			$(window).off('beforeunload.cpq').on('beforeunload.cpq', () => {
				CPQTransaction.cleanup()
			})
		},
		on_hide(frm) {
			CPQTransaction.cleanup()
		},
	})

	// Child table events
	frappe.ui.form.on(item_doctype, {
		item_code(frm, cdt, cdn) {
			CPQTransaction.on_item_code_change(frm, cdt, cdn)
		},
		before_items_remove(frm, cdt, cdn) {
			const item = frappe.get_doc(cdt, cdn)
			if (item?.item_code) {
				CPQTransaction.clear_cache_for_item(item.item_code)
			}
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

// Delivery Note
setup_cpq_handlers('Delivery Note', 'Delivery Note Item')
