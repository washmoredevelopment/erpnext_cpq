// Copyright (c) 2024, washmoredevelopment and contributors
// For license information, please see license.txt

frappe.query_reports['Configuration Usage'] = {
	filters: [
		{
			fieldname: 'configurator',
			label: __('Product Configurator'),
			fieldtype: 'Link',
			options: 'Product Configurator',
		},
		{
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -6),
		},
		{
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype: 'Date',
			default: frappe.datetime.get_today(),
		},
	],
}
