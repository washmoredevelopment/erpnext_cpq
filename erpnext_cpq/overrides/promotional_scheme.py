# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def validate_promotional_scheme(doc, method):
	"""
	Validate that Promotional Schemes cannot target configurable items.
	Configurable items get their pricing from component items, so promotional
	schemes should be applied to those components instead.
	"""
	configurable_items = []

	# Check price discount slabs for item-based rules
	for slab in doc.get("price_discount_slabs") or []:
		if slab.apply_on == "Item Code":
			for item_row in doc.get("items") or []:
				if item_row.item_code:
					is_configurable = frappe.db.get_value("Item", item_row.item_code, "is_configurable")
					if is_configurable and item_row.item_code not in configurable_items:
						configurable_items.append(item_row.item_code)

	# Check product discount slabs for item-based rules
	for slab in doc.get("product_discount_slabs") or []:
		if slab.apply_on == "Item Code":
			for item_row in doc.get("items") or []:
				if item_row.item_code:
					is_configurable = frappe.db.get_value("Item", item_row.item_code, "is_configurable")
					if is_configurable and item_row.item_code not in configurable_items:
						configurable_items.append(item_row.item_code)

	if configurable_items:
		frappe.throw(
			_(
				"The following items are configurable and cannot have promotional schemes: {0}. "
				"Promotional schemes should be applied to component items, not configurable parents."
			).format(", ".join(configurable_items))
		)
