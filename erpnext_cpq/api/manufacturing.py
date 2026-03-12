# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def create_bom_from_configuration(configuration_result_name):
	"""
	Create a BOM from a Configuration Result.

	Args:
		configuration_result_name: Configuration Result name

	Returns:
		dict with bom name
	"""
	result = frappe.get_doc("Configuration Result", configuration_result_name)
	result.check_permission("write")

	# Get the parent item from the configurator
	configurator = frappe.get_doc("Product Configurator", result.configurator)
	parent_item = configurator.item

	# Check if BOM already exists for this configuration
	if result.get("bom"):
		existing_bom = frappe.db.exists("BOM", result.bom)
		if existing_bom:
			frappe.throw(
				_("BOM {0} already exists for this configuration. "
				  "Delete it first to create a new one.").format(result.bom)
			)

	# Get parent item details
	parent_item_doc = frappe.get_cached_value(
		"Item", parent_item, ["item_name", "stock_uom"], as_dict=True
	)

	# Create BOM
	bom = frappe.new_doc("BOM")
	bom.item = parent_item
	bom.item_name = parent_item_doc.item_name if parent_item_doc else ""
	bom.quantity = 1
	bom.is_active = 1
	bom.is_default = 0
	bom.with_operations = 0

	# Add component items
	for item in result.items:
		item_data = frappe.get_cached_value(
			"Item", item.item_code,
			["item_name", "stock_uom", "description"],
			as_dict=True,
		)
		if not item_data:
			continue

		bom.append("items", {
			"item_code": item.item_code,
			"item_name": item_data.item_name,
			"description": item.description or item_data.description,
			"qty": item.qty,
			"uom": item_data.stock_uom,
			"stock_uom": item_data.stock_uom,
			"rate": item.rate or 0,
		})

	bom.insert()
	bom.submit()

	# Link BOM back to Configuration Result
	frappe.db.set_value("Configuration Result", configuration_result_name, "bom", bom.name)

	return {"bom": bom.name}


@frappe.whitelist()
def link_bom_to_transaction_item(doctype, docname, item_row_name, bom_name):
	"""
	Set bom_no on a Sales Order Item for manufacturing.

	Args:
		doctype: Parent doctype (e.g., "Sales Order")
		docname: Parent document name
		item_row_name: Child table row name
		bom_name: BOM name to link
	"""
	# Validate doctype is an allowed selling transaction
	allowed_doctypes = ("Sales Order", "Quotation", "Sales Invoice", "Delivery Note")
	if doctype not in allowed_doctypes:
		frappe.throw(_("Invalid doctype: {0}").format(doctype))

	# Check permission on the parent document
	doc = frappe.get_doc(doctype, docname)
	doc.check_permission("write")

	# Validate BOM exists
	if not frappe.db.exists("BOM", bom_name):
		frappe.throw(_("BOM {0} does not exist.").format(bom_name))

	# Set bom_no on the item row
	frappe.db.set_value(
		f"{doctype} Item",
		item_row_name,
		"bom_no",
		bom_name,
	)

	return {"success": True}
