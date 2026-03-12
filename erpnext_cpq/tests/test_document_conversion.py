# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_cpq.api.configurator import create_configuration, evaluate_configuration
from erpnext_cpq.tests.fixtures import (
	cleanup_test_data,
	create_test_configurator,
	create_test_items,
	create_test_price_list,
)


class TestDocumentConversion(FrappeTestCase):
	"""Test that CPQ configuration is preserved across document conversions."""

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

	def test_configuration_fields_exist_on_item_doctypes(self):
		"""Test that custom fields are registered for all transaction item types."""
		for dt in [
			"Quotation Item",
			"Sales Order Item",
			"Sales Invoice Item",
			"Delivery Note Item",
		]:
			meta = frappe.get_meta(dt)
			self.assertTrue(
				meta.has_field("product_configuration"),
				f"{dt} should have product_configuration field",
			)
			self.assertTrue(
				meta.has_field("configuration_result"),
				f"{dt} should have configuration_result field",
			)
