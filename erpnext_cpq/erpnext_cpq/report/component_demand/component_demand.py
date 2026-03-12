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
			"fieldname": "item_code",
			"label": _("Component Item"),
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
			"fieldname": "total_qty_required",
			"label": _("Qty Required"),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "available_qty",
			"label": _("Available Qty"),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "shortfall",
			"label": _("Shortfall"),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "uom",
			"label": _("UOM"),
			"fieldtype": "Data",
			"width": 80,
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

	if filters.get("company"):
		conditions.append("so.company = %(company)s")
		values["company"] = filters["company"]

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	# Get component demand from open Sales Orders with CPQ configurations
	demand = frappe.db.sql(
		f"""
		SELECT
			cri.item_code,
			cri.item_name,
			cri.uom,
			SUM(cri.qty * soi.qty) AS total_qty_required
		FROM `tabConfiguration Result Item` cri
		INNER JOIN `tabConfiguration Result` cr ON cr.name = cri.parent
		INNER JOIN `tabSales Order Item` soi ON soi.configuration_result = cr.name
		INNER JOIN `tabSales Order` so ON so.name = soi.parent
		WHERE so.docstatus = 1
			AND so.status NOT IN ('Completed', 'Cancelled', 'Closed')
			AND {where_clause}
		GROUP BY cri.item_code, cri.item_name, cri.uom
		ORDER BY total_qty_required DESC
		""",
		values,
		as_dict=True,
	)

	# Get available stock for these items
	warehouse_filter = ""
	if filters.get("warehouse"):
		warehouse_filter = " AND warehouse = %(warehouse)s"
		values["warehouse"] = filters["warehouse"]

	for row in demand:
		available = frappe.db.sql(
			f"""
			SELECT COALESCE(SUM(actual_qty), 0) as qty
			FROM `tabBin`
			WHERE item_code = %(item_code)s {warehouse_filter}
			""",
			{**values, "item_code": row.item_code},
			as_dict=True,
		)
		row["available_qty"] = flt(available[0].qty) if available else 0
		row["shortfall"] = max(0, flt(row["total_qty_required"]) - row["available_qty"])

	return demand
