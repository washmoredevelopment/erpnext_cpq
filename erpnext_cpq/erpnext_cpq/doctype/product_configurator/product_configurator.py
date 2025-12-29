# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ProductConfigurator(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from erpnext_cpq.erpnext_cpq.doctype.configurator_item_rule.configurator_item_rule import (  # noqa: E501
			ConfiguratorItemRule,
		)
		from erpnext_cpq.erpnext_cpq.doctype.configurator_option.configurator_option import (  # noqa: E501
			ConfiguratorOption,
		)
		from erpnext_cpq.erpnext_cpq.doctype.option_choice.option_choice import (  # noqa: E501
			OptionChoice,
		)

		description: DF.TextEditor | None
		is_active: DF.Check
		item: DF.Link
		item_group: DF.Link | None
		item_name: DF.Data | None
		item_rules: DF.Table[ConfiguratorItemRule]
		naming_series: DF.Literal["CFG-.YYYY.-.#####"]
		option_choices: DF.Table[OptionChoice]
		options: DF.Table[ConfiguratorOption]
		title: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_option_choices()
		self.validate_select_options_have_choices()

	def validate_option_choices(self):
		"""
		Warn about Option Choices that reference non-Select-type options.
		These choices will be ignored during configuration.
		"""
		# Get Select-type option names
		select_options = {
			opt.option_name for opt in self.options if opt.field_type == "Select" and opt.option_name
		}

		# Find orphaned choices
		orphaned_options = set()
		for choice in self.option_choices:
			if choice.option_name and choice.option_name not in select_options:
				orphaned_options.add(choice.option_name)

		if orphaned_options:
			frappe.msgprint(
				_(
					"Warning: Option Choices reference options that are not Select-type: {0}. "
					"These choices will be ignored. Consider removing them or changing the "
					"option's field type to Select."
				).format(", ".join(sorted(orphaned_options))),
				indicator="orange",
				title=_("Orphaned Option Choices"),
			)

	def validate_select_options_have_choices(self):
		"""
		Warn if any Select-type options have no choices defined.
		"""
		# Get option names that have choices
		options_with_choices = {
			choice.option_name for choice in self.option_choices if choice.option_name
		}

		# Find Select options without choices
		missing_choices = []
		for opt in self.options:
			if opt.field_type == "Select" and opt.option_name:
				if opt.option_name not in options_with_choices:
					missing_choices.append(opt.label or opt.option_name)

		if missing_choices:
			frappe.msgprint(
				_(
					"The following Select-type options have no choices defined: {0}. "
					"Users won't be able to select a value for these options."
				).format(", ".join(missing_choices)),
				indicator="orange",
				title=_("Missing Option Choices"),
			)
