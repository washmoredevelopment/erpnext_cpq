from frappe import _


def get_data():
	return {
		"fieldname": "configurator",
		"non_standard_fieldnames": {
			"Configuration Template": "configurator",
		},
		"transactions": [
			{
				"label": _("Configurations"),
				"items": ["Product Configuration", "Configuration Result"],
			},
			{
				"label": _("Templates"),
				"items": ["Configuration Template"],
			},
		],
	}
