# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe


def update_configuration_parents(doc, method):
	"""Update Product Configuration parent references after document conversion."""
	for item in doc.get("items", []):
		if item.get("product_configuration"):
			frappe.db.set_value(
				"Product Configuration",
				item.product_configuration,
				{
					"parent_doctype": doc.doctype,
					"parent_name": doc.name,
					"parent_item_row": item.name,
				},
				update_modified=False,
			)


def cleanup_configurations(doc, method):
	"""Delete orphaned CPQ documents when parent transaction is deleted.

	Only deletes configurations whose parent_name still points to
	the document being deleted, to avoid destroying configs that
	have been transferred to a downstream document (e.g. Quotation → SO).
	"""
	for item in doc.get("items", []):
		if item.get("product_configuration"):
			# Verify this configuration still belongs to this document
			parent_name = frappe.db.get_value(
				"Product Configuration", item.product_configuration, "parent_name"
			)
			if parent_name != doc.name:
				continue

			# Delete result first (child of configuration)
			if item.get("configuration_result"):
				frappe.delete_doc(
					"Configuration Result",
					item.configuration_result,
					ignore_permissions=True,
					force=True,
				)
			frappe.delete_doc(
				"Product Configuration",
				item.product_configuration,
				ignore_permissions=True,
				force=True,
			)
