# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ConfigurationSelection(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		display_value: DF.Data | None
		option_label: DF.Data | None
		option_name: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		value: DF.Data
	# end: auto-generated types
