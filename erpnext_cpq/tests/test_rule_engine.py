# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_cpq.api.configurator import (
	calculate_qty,
	evaluate_rules,
	rule_matches,
)
from erpnext_cpq.tests.fixtures import (
	cleanup_test_data,
	create_test_configurator,
	create_test_items,
)


class TestRuleEngine(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.items = create_test_items()
		cls.configurator = create_test_configurator()

	@classmethod
	def tearDownClass(cls):
		cleanup_test_data()
		super().tearDownClass()

	def test_always_condition(self):
		"""Test that 'Always' condition always matches."""
		rule = self.configurator.item_rules[0]  # Always rule
		self.assertTrue(rule_matches(rule, {}))
		self.assertTrue(rule_matches(rule, {"wash_type": "basic"}))

	def test_when_equals_condition(self):
		"""Test 'When Equals' condition matching."""
		rule = self.configurator.item_rules[1]  # When Equals premium
		self.assertTrue(rule_matches(rule, {"wash_type": "premium"}))
		self.assertFalse(rule_matches(rule, {"wash_type": "basic"}))
		self.assertFalse(rule_matches(rule, {}))

	def test_when_set_condition(self):
		"""Test 'When Set' condition for Check fields."""
		rule = self.configurator.item_rules[2]  # When Set add_dryer
		self.assertTrue(rule_matches(rule, {"add_dryer": 1}))
		self.assertTrue(rule_matches(rule, {"add_dryer": "1"}))
		self.assertFalse(rule_matches(rule, {"add_dryer": 0}))
		self.assertFalse(rule_matches(rule, {}))

	def test_calculate_qty_base(self):
		"""Test base_qty calculation."""
		rule = self.configurator.item_rules[0]  # base_qty = 1
		self.assertEqual(calculate_qty(rule, {}), 1)

	def test_calculate_qty_from_option(self):
		"""Test qty_from_option calculation."""
		rule = self.configurator.item_rules[2]  # qty_from_option = num_bays
		self.assertEqual(calculate_qty(rule, {"num_bays": 3}), 3)
		self.assertEqual(calculate_qty(rule, {"num_bays": 5}), 5)

	def test_evaluate_rules_basic(self):
		"""Test full rule evaluation with basic selections."""
		selections = {"wash_type": "basic", "num_bays": 2, "add_dryer": 0}
		result = evaluate_rules(self.configurator.name, selections)

		# Should include Component A (always), not B (premium only), not C (dryer off)
		self.assertIn("CPQ-TEST-COMP-A", result)
		self.assertNotIn("CPQ-TEST-COMP-B", result)
		self.assertNotIn("CPQ-TEST-COMP-C", result)

	def test_evaluate_rules_premium_with_dryer(self):
		"""Test full rule evaluation with premium + dryer."""
		selections = {"wash_type": "premium", "num_bays": 3, "add_dryer": 1}
		result = evaluate_rules(self.configurator.name, selections)

		# Should include A (always), B (premium), C (dryer with qty=3)
		self.assertIn("CPQ-TEST-COMP-A", result)
		self.assertIn("CPQ-TEST-COMP-B", result)
		self.assertIn("CPQ-TEST-COMP-C", result)
		self.assertEqual(result["CPQ-TEST-COMP-C"]["qty"], 3)
