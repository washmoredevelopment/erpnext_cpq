# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ConfiguratorOption(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		default_value: DF.Data | None
		depends_on: DF.Data | None
		depends_on_value: DF.Data | None
		field_type: DF.Literal["Select", "Int", "Float", "Check", "Data"]
		help_text: DF.SmallText | None
		label: DF.Data
		max_value: DF.Float
		min_value: DF.Float
		option_name: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		required: DF.Check
	# end: auto-generated types
