# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_cpq.api.configurator import (
	create_configuration,
	evaluate_configuration,
	get_configuration_selections,
	update_configuration,
)
from erpnext_cpq.tests.fixtures import (
	cleanup_test_data,
	create_test_configurator,
	create_test_items,
	create_test_price_list,
)


class TestConfigurationFlow(FrappeTestCase):
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

	def test_create_configuration(self):
		"""Test creating a Product Configuration."""
		result = create_configuration(
			configurator=self.configurator.name,
			selections={"wash_type": "basic", "num_bays": 2, "add_dryer": 0},
		)

		self.assertTrue(result["name"])
		self.assertIn("Configuration:", result["configuration_summary"])

		# Clean up
		frappe.delete_doc("Product Configuration", result["name"], force=True)

	def test_evaluate_configuration(self):
		"""Test evaluating a configuration to get pricing."""
		config = create_configuration(
			configurator=self.configurator.name,
			selections={"wash_type": "premium", "num_bays": 1, "add_dryer": 0},
		)

		result = evaluate_configuration(
			configuration_name=config["name"],
			price_list=self.price_list,
			company=frappe.defaults.get_defaults().get("company"),
		)

		self.assertTrue(result["name"])
		self.assertGreater(result["total"], 0)

		# Clean up
		frappe.delete_doc("Configuration Result", result["name"], force=True)
		frappe.delete_doc("Product Configuration", config["name"], force=True)

	def test_get_configuration_selections(self):
		"""Test loading existing configuration selections."""
		config = create_configuration(
			configurator=self.configurator.name,
			selections={"wash_type": "basic", "num_bays": 3, "add_dryer": 1},
		)

		selections = get_configuration_selections(config["name"])

		self.assertEqual(selections["wash_type"], "basic")
		self.assertEqual(selections["num_bays"], 3)
		self.assertEqual(selections["add_dryer"], 1)

		# Clean up
		frappe.delete_doc("Product Configuration", config["name"], force=True)

	def test_update_configuration(self):
		"""Test updating an existing configuration."""
		config = create_configuration(
			configurator=self.configurator.name,
			selections={"wash_type": "basic", "num_bays": 1, "add_dryer": 0},
		)

		result = update_configuration(
			configuration_name=config["name"],
			selections={"wash_type": "premium", "num_bays": 2, "add_dryer": 1},
		)

		self.assertTrue(len(result["changes"]) > 0)

		# Verify updated values
		selections = get_configuration_selections(config["name"])
		self.assertEqual(selections["wash_type"], "premium")

		# Clean up
		frappe.delete_doc("Product Configuration", config["name"], force=True)
