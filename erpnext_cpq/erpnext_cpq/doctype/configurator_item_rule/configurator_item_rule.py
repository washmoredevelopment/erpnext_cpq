# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ConfiguratorItemRule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		base_qty: DF.Float
		comparison: DF.Literal["", ">", ">=", "<", "<=", "="]
		condition_type: DF.Literal[
			"Always",
			"When Equals",
			"When Set",
			"When Not Empty",
			"When Greater Than",
			"When Less Than",
			"When In List",
		]
		description_from_option: DF.Data | None
		description_override: DF.SmallText | None
		item_code: DF.Link
		item_name: DF.Data | None
		option_name: DF.Data | None
		option_value: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		qty_from_option: DF.Data | None
		qty_multiplier: DF.Float
	# end: auto-generated types
