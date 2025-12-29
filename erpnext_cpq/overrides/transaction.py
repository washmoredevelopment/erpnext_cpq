# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def validate_configurable_items(doc, method):
	"""
	Validate configurable items in sales transactions.

	1. Ensure configurable items have a configuration linked
	2. Validate discount doesn't exceed Configuration Result max_discount
	"""
	if not doc.get("items"):
		return

	for item in doc.items:
		# Skip if no item_code
		if not item.item_code:
			continue

		# Check if this item is configurable
		is_configurable = frappe.db.get_value("Item", item.item_code, "is_configurable")

		if not is_configurable:
			continue

		# Configurable item must have a product_configuration linked
		if not item.get("product_configuration"):
			frappe.throw(
				_(
					"Please configure item '{0}' (Row {1}) before saving. "
					"Click the Configure button to set up the configuration."
				).format(item.item_code, item.idx)
			)

		# If configuration_result exists, validate max discount
		if item.get("configuration_result"):
			_validate_max_discount(doc, item)


def _validate_max_discount(doc, item):
	"""
	Validate that the effective discount on a configured item doesn't exceed
	the weighted average max discount from the Configuration Result.
	"""
	# Get max_discount from Configuration Result
	max_discount = frappe.db.get_value(
		"Configuration Result", item.configuration_result, "max_discount"
	)

	if not max_discount:
		# No max discount set - skip validation
		return

	# Calculate effective discount on this line item
	# Compare the configuration total (original rate) vs current rate
	config_total = frappe.db.get_value("Configuration Result", item.configuration_result, "total")

	if not config_total or config_total <= 0:
		return

	# Current rate on the line item
	current_rate = item.rate or 0

	# Calculate discount percentage
	if current_rate < config_total:
		effective_discount = ((config_total - current_rate) / config_total) * 100
	else:
		# No discount applied (rate is same or higher)
		effective_discount = 0

	# Check if discount exceeds max allowed
	if effective_discount > max_discount:
		frappe.throw(
			_(
				"Max discount allowed for configured item '{0}' (Row {1}) is {2}%. "
				"Current discount is {3}%."
			).format(
				item.item_code,
				item.idx,
				frappe.utils.flt(max_discount, 2),
				frappe.utils.flt(effective_discount, 2),
			)
		)
