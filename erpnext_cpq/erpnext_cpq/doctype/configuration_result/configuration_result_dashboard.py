from frappe import _


def get_data():
	return {
		"fieldname": "configuration_result",
		"internal_links": {
			"Product Configuration": "configuration",
		},
		"transactions": [
			{
				"label": _("Source"),
				"items": ["Product Configuration"],
			},
		],
	}
