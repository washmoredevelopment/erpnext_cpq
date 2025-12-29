# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ProductConfiguration(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from erpnext_cpq.erpnext_cpq.doctype.configuration_selection.configuration_selection import (  # noqa: E501
			ConfigurationSelection,
		)

		configuration_summary: DF.Text | None
		configurator: DF.Link
		parent_doctype: DF.Data | None
		parent_item_row: DF.Data | None
		parent_name: DF.Data | None
		selections: DF.Table[ConfigurationSelection]
	# end: auto-generated types
