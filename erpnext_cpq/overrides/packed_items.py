# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def populate_cpq_packed_items(doc, method):
	"""
	Populate packed_items table with CPQ component items from Configuration Results.

	Runs during validate, AFTER ERPNext's own make_packing_list() has run.
	Appends CPQ component items to doc.packed_items and injects the
	_product_bundle_items cache so get_item_list() routes stock to components.
	"""
	if not doc.get("items"):
		return

	# Batch-check which items are configurable
	item_codes = list({item.item_code for item in doc.items if item.item_code})
	if not item_codes:
		return

	configurable_set = set(
		frappe.get_all(
			"Item",
			filters={"name": ("in", item_codes), "is_configurable": 1},
			pluck="name",
		)
	)

	if not configurable_set:
		return

	# Ensure _product_bundle_items cache exists
	if not hasattr(doc, "_product_bundle_items"):
		doc._product_bundle_items = {}

	for item in doc.items:
		if not item.item_code or item.item_code not in configurable_set:
			continue

		configuration_result = item.get("configuration_result")
		if not configuration_result:
			continue

		# Fetch Configuration Result items
		result_items = frappe.get_all(
			"Configuration Result Item",
			filters={"parent": configuration_result},
			fields=["item_code", "item_name", "qty", "uom", "rate", "description"],
		)

		if not result_items:
			continue

		# Remove any existing CPQ packed items for this parent row (from a previous validate).
		# Use doc.set() to preserve Frappe's child table management.
		existing = [
			pi for pi in (doc.get("packed_items") or [])
			if not (pi.parent_detail_docname == item.name and pi.parent_item == item.item_code)
		]
		doc.set("packed_items", existing)

		# Inject cache entry so get_item_list() treats this as a bundle
		doc._product_bundle_items[item.item_code] = True

		# Append component items to packed_items
		for comp in result_items:
			# Get stock item details
			item_data = frappe.get_cached_value(
				"Item", comp.item_code,
				["item_name", "stock_uom", "description", "is_stock_item"],
				as_dict=True,
			)

			if not item_data:
				continue

			pi = doc.append("packed_items", {})
			pi.parent_item = item.item_code
			pi.parent_detail_docname = item.name
			pi.item_code = comp.item_code
			pi.item_name = item_data.item_name or comp.item_name
			pi.uom = item_data.stock_uom or comp.uom
			pi.qty = flt(comp.qty) * flt(item.stock_qty)
			pi.conversion_factor = 1  # Packed items are in stock UOM
			pi.rate = comp.rate or 0
			pi.warehouse = item.warehouse
			pi.description = comp.description or item_data.description

			if hasattr(item, "target_warehouse"):
				pi.target_warehouse = item.target_warehouse
			if hasattr(item, "delivered_by_supplier"):
				pi.delivered_by_supplier = item.get("delivered_by_supplier")
