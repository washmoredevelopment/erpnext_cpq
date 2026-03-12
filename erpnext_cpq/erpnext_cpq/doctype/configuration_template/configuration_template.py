# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ConfigurationTemplate(Document):
	def validate(self):
		self._validate_unique_default()

	def _validate_unique_default(self):
		"""Ensure only one default template per configurator."""
		if not self.is_default:
			return

		existing = frappe.db.exists(
			"Configuration Template",
			{
				"configurator": self.configurator,
				"is_default": 1,
				"name": ("!=", self.name),
			},
		)
		if existing:
			frappe.throw(
				_("There is already a default template ({0}) for this configurator. "
				  "Please unset it first.").format(existing)
			)
