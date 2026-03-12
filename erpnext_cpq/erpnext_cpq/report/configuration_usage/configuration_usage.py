# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "option_name",
			"label": _("Option"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "option_label",
			"label": _("Option Label"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "value",
			"label": _("Value"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "display_value",
			"label": _("Display Value"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "count",
			"label": _("Count"),
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"fieldname": "percentage",
			"label": _("Percentage"),
			"fieldtype": "Percent",
			"width": 100,
		},
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("configurator"):
		conditions.append("pc.configurator = %(configurator)s")
		values["configurator"] = filters["configurator"]

	if filters.get("from_date"):
		conditions.append("pc.creation >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("pc.creation <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	# Get total configurations for percentage calculation
	total = frappe.db.sql(
		f"""
		SELECT COUNT(DISTINCT pc.name) as total
		FROM `tabProduct Configuration` pc
		WHERE {where_clause}
		""",
		values,
	)
	total_configs = total[0][0] if total else 0

	if not total_configs:
		return []

	data = frappe.db.sql(
		f"""
		SELECT
			cs.option_name,
			cs.option_label,
			cs.value,
			cs.display_value,
			COUNT(*) AS count
		FROM `tabConfiguration Selection` cs
		INNER JOIN `tabProduct Configuration` pc ON pc.name = cs.parent
		WHERE {where_clause}
		GROUP BY cs.option_name, cs.option_label, cs.value, cs.display_value
		ORDER BY cs.option_name, count DESC
		""",
		values,
		as_dict=True,
	)

	for row in data:
		row["percentage"] = flt(row["count"] / total_configs * 100, 2)

	return data
