# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_cpq.api.configurator import create_configuration, evaluate_configuration
from erpnext_cpq.overrides.packed_items import populate_cpq_packed_items
from erpnext_cpq.tests.fixtures import (
	cleanup_test_data,
	create_test_configurator,
	create_test_items,
	create_test_price_list,
)


class TestPackedItems(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.items = create_test_items()
		cls.configurator = create_test_configurator()
		cls.price_list = create_test_price_list()

	@classmethod
	def tearDownClass(cls):
		cleanup_test_data()
		super().tearDownClass()

	def _create_configured_result(self, selections=None):
		"""Helper to create a configuration and evaluate it."""
		if selections is None:
			selections = {"wash_type": "premium", "num_bays": 2, "add_dryer": 1}

		config = create_configuration(
			configurator=self.configurator.name,
			selections=selections,
		)

		result = evaluate_configuration(
			configuration_name=config["name"],
			price_list=self.price_list,
			company=frappe.defaults.get_defaults().get("company"),
		)

		return config, result

	def test_packed_items_populated(self):
		"""Test that packed_items are populated from Configuration Result."""
		config, result = self._create_configured_result()

		# Create a mock document-like object
		doc = frappe._dict({
			"items": [
				frappe._dict({
					"item_code": "CPQ-TEST-PARENT",
					"name": "test-row-001",
					"qty": 1,
					"stock_qty": 1,
					"conversion_factor": 1,
					"warehouse": "Stores - WPL",
					"configuration_result": result["name"],
				})
			],
			"packed_items": [],
		})

		populate_cpq_packed_items(doc, "validate")

		# Should have packed items for components
		self.assertTrue(len(doc.packed_items) > 0)

		# Check that Component A is present (always included)
		comp_a = [pi for pi in doc.packed_items if pi.item_code == "CPQ-TEST-COMP-A"]
		self.assertTrue(len(comp_a) > 0)

		# Check parent_item is set correctly
		for pi in doc.packed_items:
			self.assertEqual(pi.parent_item, "CPQ-TEST-PARENT")
			self.assertEqual(pi.parent_detail_docname, "test-row-001")

		# Check cache injection
		self.assertTrue(doc._product_bundle_items.get("CPQ-TEST-PARENT"))

		# Clean up
		frappe.delete_doc("Configuration Result", result["name"], force=True)
		frappe.delete_doc("Product Configuration", config["name"], force=True)

	def test_packed_items_qty_multiplied(self):
		"""Test that packed item qty is multiplied by parent item qty."""
		config, result = self._create_configured_result(
			selections={"wash_type": "basic", "num_bays": 3, "add_dryer": 1}
		)

		doc = frappe._dict({
			"items": [
				frappe._dict({
					"item_code": "CPQ-TEST-PARENT",
					"name": "test-row-002",
					"qty": 2,
					"stock_qty": 2,
					"conversion_factor": 1,
					"warehouse": "Stores - WPL",
					"configuration_result": result["name"],
				})
			],
			"packed_items": [],
		})

		populate_cpq_packed_items(doc, "validate")

		# Component C has qty_from_option=num_bays (3), multiplied by parent qty (2) = 6
		comp_c = [pi for pi in doc.packed_items if pi.item_code == "CPQ-TEST-COMP-C"]
		if comp_c:
			self.assertEqual(comp_c[0].qty, 6.0)  # 3 * 2

		# Clean up
		frappe.delete_doc("Configuration Result", result["name"], force=True)
		frappe.delete_doc("Product Configuration", config["name"], force=True)
