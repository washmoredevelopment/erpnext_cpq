# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def validate_pricing_rule(doc, method):
	"""
	Validate that Pricing Rules cannot target configurable items.
	Configurable items get their pricing from component items, so pricing rules
	should be applied to those components instead.
	"""
	configurable_items = []

	# Check based on apply_on type
	if doc.apply_on == "Item Code":
		# Check items in the items child table
		for item_row in doc.get("items") or []:
			if item_row.item_code:
				is_configurable = frappe.db.get_value("Item", item_row.item_code, "is_configurable")
				if is_configurable:
					configurable_items.append(item_row.item_code)

	if configurable_items:
		frappe.throw(
			_(
				"The following items are configurable and cannot have pricing rules: {0}. "
				"Pricing rules should be applied to component items, not configurable parents."
			).format(", ".join(configurable_items))
		)
