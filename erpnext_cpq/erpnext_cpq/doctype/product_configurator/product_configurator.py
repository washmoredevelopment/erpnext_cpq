# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

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
