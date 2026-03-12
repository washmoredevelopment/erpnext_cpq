# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe


def create_test_items():
	"""Create test items for CPQ testing."""
	items = {}

	# Parent configurable item (non-stock)
	items["parent"] = _get_or_create_item(
		"CPQ-TEST-PARENT",
		item_name="Test Configurable Item",
		is_stock_item=0,
		is_configurable=1,
	)

	# Component items (stock items)
	for i, (code, name) in enumerate([
		("CPQ-TEST-COMP-A", "Test Component A"),
		("CPQ-TEST-COMP-B", "Test Component B"),
		("CPQ-TEST-COMP-C", "Test Component C"),
	]):
		items[f"component_{chr(97 + i)}"] = _get_or_create_item(
			code, item_name=name, is_stock_item=1
		)

	return items


def _get_or_create_item(item_code, item_name=None, is_stock_item=1, is_configurable=0):
	"""Get or create a test Item."""
	if frappe.db.exists("Item", item_code):
		return frappe.get_doc("Item", item_code)

	item = frappe.new_doc("Item")
	item.item_code = item_code
	item.item_name = item_name or item_code
	item.item_group = "All Item Groups"
	item.stock_uom = "Nos"
	item.is_stock_item = is_stock_item
	item.is_configurable = is_configurable
	item.insert(ignore_permissions=True)
	return item


def create_test_configurator(parent_item_code="CPQ-TEST-PARENT"):
	"""Create a test Product Configurator with options and rules."""
	# Check if one already exists for this item
	existing = frappe.db.exists(
		"Product Configurator", {"item": parent_item_code}
	)
	if existing:
		return frappe.get_doc("Product Configurator", existing)

	configurator = frappe.new_doc("Product Configurator")
	configurator.title = "Test Configurator"
	configurator.item = parent_item_code
	configurator.is_active = 1

	# Add options
	configurator.append("options", {
		"option_name": "wash_type",
		"label": "Wash Type",
		"field_type": "Select",
		"required": 1,
	})
	configurator.append("options", {
		"option_name": "num_bays",
		"label": "Number of Bays",
		"field_type": "Int",
		"required": 1,
		"default_value": "1",
		"min_value": 1,
		"max_value": 10,
	})
	configurator.append("options", {
		"option_name": "add_dryer",
		"label": "Add Dryer",
		"field_type": "Check",
	})

	# Add option choices for wash_type
	configurator.append("option_choices", {
		"option_name": "wash_type",
		"value": "basic",
		"label": "Basic Wash",
		"is_default": 1,
	})
	configurator.append("option_choices", {
		"option_name": "wash_type",
		"value": "premium",
		"label": "Premium Wash",
	})

	# Add item rules
	# Always include Component A
	configurator.append("item_rules", {
		"item_code": "CPQ-TEST-COMP-A",
		"base_qty": 1,
		"condition_type": "Always",
	})
	# Include Component B when wash_type is premium
	configurator.append("item_rules", {
		"item_code": "CPQ-TEST-COMP-B",
		"base_qty": 1,
		"condition_type": "When Equals",
		"option_name": "wash_type",
		"option_value": "premium",
	})
	# Include Component C when add_dryer is set, qty from num_bays
	configurator.append("item_rules", {
		"item_code": "CPQ-TEST-COMP-C",
		"base_qty": 1,
		"condition_type": "When Set",
		"option_name": "add_dryer",
		"qty_from_option": "num_bays",
		"qty_multiplier": 1,
	})

	configurator.insert(ignore_permissions=True)

	# Link configurator to item
	frappe.db.set_value("Item", parent_item_code, "product_configurator", configurator.name)

	return configurator


def create_test_price_list():
	"""Create a test price list with prices for test items."""
	price_list_name = "CPQ Test Price List"
	if not frappe.db.exists("Price List", price_list_name):
		pl = frappe.new_doc("Price List")
		pl.price_list_name = price_list_name
		pl.selling = 1
		pl.currency = "USD"
		pl.insert(ignore_permissions=True)

	# Add item prices
	for item_code, rate in [
		("CPQ-TEST-COMP-A", 100),
		("CPQ-TEST-COMP-B", 200),
		("CPQ-TEST-COMP-C", 50),
	]:
		if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list_name}):
			ip = frappe.new_doc("Item Price")
			ip.item_code = item_code
			ip.price_list = price_list_name
			ip.price_list_rate = rate
			ip.currency = "USD"
			ip.insert(ignore_permissions=True)

	return price_list_name


def cleanup_test_data():
	"""Clean up all test data created by fixtures."""
	# Delete in reverse dependency order
	for dt in ["Configuration Result", "Product Configuration", "Configuration Template"]:
		for name in frappe.get_all(dt, filters={"configurator": ("like", "CFG%")}, pluck="name"):
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

	for name in frappe.get_all(
		"Product Configurator", filters={"item": ("like", "CPQ-TEST%")}, pluck="name"
	):
		frappe.delete_doc("Product Configurator", name, force=True, ignore_permissions=True)

	for item_code in ["CPQ-TEST-PARENT", "CPQ-TEST-COMP-A", "CPQ-TEST-COMP-B", "CPQ-TEST-COMP-C"]:
		if frappe.db.exists("Item", item_code):
			# Delete item prices first
			for ip in frappe.get_all("Item Price", filters={"item_code": item_code}, pluck="name"):
				frappe.delete_doc("Item Price", ip, force=True, ignore_permissions=True)
			frappe.delete_doc("Item", item_code, force=True, ignore_permissions=True)

	if frappe.db.exists("Price List", "CPQ Test Price List"):
		frappe.delete_doc("Price List", "CPQ Test Price List", force=True, ignore_permissions=True)
