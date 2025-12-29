# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def validate_item_configuration(doc, method):
	"""
	Validate Item configuration settings.

	1. Item cannot have both Variants and be Configurable (mutually exclusive)
	2. Configurable items must have a Product Configurator linked
	3. Items with existing Pricing Rules or Promotional Schemes cannot be made configurable
	"""
	# Check: cannot have both variants and be configurable
	if doc.has_variants and doc.is_configurable:
		frappe.throw(
			_(
				"An item cannot have both Variants and be Configurable. "
				"Variants create separate SKUs, while Configuration is dynamic at sale time. "
				"Please choose one approach."
			)
		)

	# Check: configurable items must have a product_configurator linked
	if doc.is_configurable and not doc.product_configurator:
		frappe.throw(_("Please select a Product Configurator for this configurable item."))

	# Check: when enabling is_configurable, ensure no existing pricing rules
	if doc.is_configurable:
		_validate_no_existing_pricing_rules(doc)


def _validate_no_existing_pricing_rules(doc):
	"""
	Check if this item has any existing Pricing Rules or Promotional Schemes.
	If so, block enabling is_configurable until those rules are removed.
	"""
	conflicting_rules = []

	# Check Pricing Rules that target this item
	pricing_rules = frappe.get_all(
		"Pricing Rule Item Code",
		filters={"item_code": doc.item_code},
		fields=["parent"],
		distinct=True,
	)
	for rule in pricing_rules:
		# Verify the parent Pricing Rule is not disabled
		is_disabled = frappe.db.get_value("Pricing Rule", rule.parent, "disable")
		if not is_disabled:
			conflicting_rules.append(f"Pricing Rule: {rule.parent}")

	# Check Promotional Schemes that target this item
	# Promotional Scheme reuses "Pricing Rule Item Code" child table
	promotional_items = frappe.get_all(
		"Pricing Rule Item Code",
		filters={"item_code": doc.item_code, "parenttype": "Promotional Scheme"},
		fields=["parent"],
		distinct=True,
	)
	for scheme in promotional_items:
		# Verify the parent Promotional Scheme is not disabled
		is_disabled = frappe.db.get_value("Promotional Scheme", scheme.parent, "disable")
		if not is_disabled:
			conflicting_rules.append(f"Promotional Scheme: {scheme.parent}")

	if conflicting_rules:
		frappe.throw(
			_(
				"Item {0} has existing pricing rules that must be disabled first: {1}. "
				"Configurable items cannot have pricing rules applied to the parent item. "
				"Pricing rules should be applied to component items instead."
			).format(doc.item_code, ", ".join(conflicting_rules))
		)
