# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_cpq.tests.fixtures import (
	cleanup_test_data,
	create_test_configurator,
	create_test_items,
)


class TestProductConfigurator(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.items = create_test_items()
		cls.configurator = create_test_configurator()

	@classmethod
	def tearDownClass(cls):
		cleanup_test_data()
		super().tearDownClass()

	def test_configurator_creation(self):
		"""Test that a configurator is created with correct structure."""
		self.assertTrue(self.configurator.name)
		self.assertEqual(self.configurator.item, "CPQ-TEST-PARENT")
		self.assertEqual(len(self.configurator.options), 3)
		self.assertEqual(len(self.configurator.item_rules), 3)

	def test_configurator_options(self):
		"""Test option types are correct."""
		options = {o.option_name: o for o in self.configurator.options}

		self.assertEqual(options["wash_type"].field_type, "Select")
		self.assertEqual(options["num_bays"].field_type, "Int")
		self.assertEqual(options["add_dryer"].field_type, "Check")

	def test_configurator_choices(self):
		"""Test option choices are created."""
		choices = [c for c in self.configurator.option_choices if c.option_name == "wash_type"]
		self.assertEqual(len(choices), 2)

		values = [c.value for c in choices]
		self.assertIn("basic", values)
		self.assertIn("premium", values)
