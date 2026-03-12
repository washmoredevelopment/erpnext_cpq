# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe


def get_configuration_breakdown(item_row):
	"""
	Get component items for a configured line item.
	Used in Jinja print formats.

	Args:
		item_row: Item row dict from the transaction

	Returns:
		list of component item dicts, or empty list
	"""
	configuration_result = item_row.get("configuration_result")
	if not configuration_result:
		return []

	return frappe.get_all(
		"Configuration Result Item",
		filters={"parent": configuration_result},
		fields=["item_code", "item_name", "description", "qty", "uom", "rate", "amount"],
		order_by="idx",
	)


def is_configured_item(item_row):
	"""
	Check if a transaction item row has a CPQ configuration.
	Used in Jinja print formats.

	Args:
		item_row: Item row dict from the transaction

	Returns:
		bool
	"""
	return bool(item_row.get("configuration_result"))


def get_configuration_summary(item_row):
	"""
	Get formatted configuration summary for a line item.
	Used in Jinja print formats.

	Args:
		item_row: Item row dict from the transaction

	Returns:
		str or empty string
	"""
	product_configuration = item_row.get("product_configuration")
	if not product_configuration:
		return ""

	summary = frappe.db.get_value(
		"Product Configuration", product_configuration, "configuration_summary"
	)
	return summary or ""
