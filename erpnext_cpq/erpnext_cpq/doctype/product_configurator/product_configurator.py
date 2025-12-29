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
		self.validate_duplicate_choice_labels()

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

	def validate_duplicate_choice_labels(self):
		"""
		Warn if any option has multiple choices with the same display label.
		Duplicate labels will be disambiguated at runtime but may confuse users.
		"""
		# Group choices by option_name
		choices_by_option = {}
		for choice in self.option_choices:
			if not choice.option_name:
				continue
			if choice.option_name not in choices_by_option:
				choices_by_option[choice.option_name] = []
			choices_by_option[choice.option_name].append(choice)

		# Check each option for duplicate labels
		options_with_duplicates = []
		for option_name, choices in choices_by_option.items():
			# Get display text for each choice (label or value)
			display_counts = {}
			for choice in choices:
				display = choice.label or choice.value or ""
				display_counts[display] = display_counts.get(display, 0) + 1

			# Find duplicates
			duplicates = [d for d, count in display_counts.items() if count > 1 and d]
			if duplicates:
				# Get the option label for clearer message
				option_label = option_name
				for opt in self.options:
					if opt.option_name == option_name:
						option_label = opt.label or option_name
						break
				options_with_duplicates.append(f"{option_label}: {', '.join(duplicates)}")

		if options_with_duplicates:
			frappe.msgprint(
				_(
					"The following options have duplicate choice labels: {0}. "
					"Duplicates will be disambiguated with their values in parentheses."
				).format("; ".join(options_with_duplicates)),
				indicator="orange",
				title=_("Duplicate Choice Labels"),
			)
