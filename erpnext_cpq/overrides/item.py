# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def validate_item_configuration(doc, method):
	"""
	Validate that an Item cannot have both Variants and be Configurable.
	These are mutually exclusive features.
	"""
	if doc.has_variants and doc.is_configurable:
		frappe.throw(
			_(
				"An item cannot have both Variants and be Configurable. "
				"Variants create separate SKUs, while Configuration is dynamic at sale time. "
				"Please choose one approach."
			)
		)

	# Also validate: if is_configurable, must have a product_configurator linked
	if doc.is_configurable and not doc.product_configurator:
		frappe.throw(_("Please select a Product Configurator for this configurable item."))
