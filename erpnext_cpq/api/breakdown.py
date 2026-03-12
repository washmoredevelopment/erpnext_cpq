# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_configuration_breakdown(configuration_result_name):
	"""
	Get formatted breakdown of a Configuration Result for display.

	Args:
		configuration_result_name: Configuration Result name

	Returns:
		dict with items list and totals
	"""
	result = frappe.get_doc("Configuration Result", configuration_result_name)

	items = []
	for item in result.items:
		items.append({
			"item_code": item.item_code,
			"item_name": item.item_name,
			"description": item.description,
			"qty": item.qty,
			"uom": item.uom,
			"rate": item.rate,
			"amount": item.amount,
		})

	# Get configuration summary
	config = frappe.get_doc("Product Configuration", result.configuration)

	return {
		"items": items,
		"total": result.total,
		"currency": result.currency,
		"max_discount": result.max_discount,
		"configuration_summary": config.configuration_summary,
	}
