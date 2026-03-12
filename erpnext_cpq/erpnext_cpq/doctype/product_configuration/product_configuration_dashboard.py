from frappe import _


def get_data():
	return {
		"fieldname": "configuration",
		"transactions": [
			{
				"label": _("Results"),
				"items": ["Configuration Result"],
			},
		],
	}
