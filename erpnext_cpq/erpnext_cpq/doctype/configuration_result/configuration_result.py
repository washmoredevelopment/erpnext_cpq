# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ConfigurationResult(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from erpnext_cpq.erpnext_cpq.doctype.configuration_result_item.configuration_result_item import (  # noqa: E501
			ConfigurationResultItem,
		)

		configuration: DF.Link
		configurator: DF.Link | None
		currency: DF.Link | None
		items: DF.Table[ConfigurationResultItem]
		total: DF.Currency
	# end: auto-generated types
