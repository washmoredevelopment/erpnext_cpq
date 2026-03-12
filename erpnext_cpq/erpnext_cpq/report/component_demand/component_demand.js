// Copyright (c) 2024, washmoredevelopment and contributors
// For license information, please see license.txt

frappe.query_reports['Component Demand'] = {
	filters: [
		{
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype: 'Date',
			default: frappe.datetime.add_months(frappe.datetime.get_today(), 3),
		},
		{
			fieldname: 'warehouse',
			label: __('Warehouse'),
			fieldtype: 'Link',
			options: 'Warehouse',
		},
		{
			fieldname: 'company',
			label: __('Company'),
			fieldtype: 'Link',
			options: 'Company',
			default: frappe.defaults.get_user_default('Company'),
		},
	],
}
