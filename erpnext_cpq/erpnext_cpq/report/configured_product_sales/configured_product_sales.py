# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "item_code",
			"label": _("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 200,
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "configurator",
			"label": _("Configurator"),
			"fieldtype": "Link",
			"options": "Product Configurator",
			"width": 180,
		},
		{
			"fieldname": "customer",
			"label": _("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 200,
		},
		{
			"fieldname": "order_count",
			"label": _("Orders"),
			"fieldtype": "Int",
			"width": 80,
		},
		{
			"fieldname": "total_qty",
			"label": _("Total Qty"),
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"fieldname": "total_revenue",
			"label": _("Revenue"),
			"fieldtype": "Currency",
			"width": 150,
		},
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("from_date"):
		conditions.append("so.transaction_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("so.transaction_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	if filters.get("customer"):
		conditions.append("so.customer = %(customer)s")
		values["customer"] = filters["customer"]

	if filters.get("configurator"):
		conditions.append("cr.configurator = %(configurator)s")
		values["configurator"] = filters["configurator"]

	if filters.get("company"):
		conditions.append("so.company = %(company)s")
		values["company"] = filters["company"]

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	data = frappe.db.sql(
		f"""
		SELECT
			soi.item_code,
			soi.item_name,
			cr.configurator,
			so.customer,
			COUNT(DISTINCT so.name) AS order_count,
			SUM(soi.qty) AS total_qty,
			SUM(soi.amount) AS total_revenue
		FROM `tabSales Order Item` soi
		INNER JOIN `tabSales Order` so ON so.name = soi.parent
		INNER JOIN `tabConfiguration Result` cr ON cr.name = soi.configuration_result
		WHERE so.docstatus = 1
			AND soi.configuration_result IS NOT NULL
			AND soi.configuration_result != ''
			AND {where_clause}
		GROUP BY soi.item_code, cr.configurator, so.customer
		ORDER BY total_revenue DESC
		""",
		values,
		as_dict=True,
	)

	return data
