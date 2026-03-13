import frappe


def after_install():
	add_cpq_workspace_links()


def after_migrate():
	add_cpq_workspace_links()


def add_cpq_workspace_links():
	"""Add CPQ links to the Selling workspace."""
	if not frappe.db.exists("Workspace", "Selling"):
		return

	workspace = frappe.get_doc("Workspace", "Selling")

	# Check if CPQ links already exist
	existing_labels = {link.label for link in workspace.links if link.label}
	if "Product Configurator" in existing_labels:
		return

	# Add Card Break for Product Configuration section
	workspace.append(
		"links",
		{
			"type": "Card Break",
			"label": "Product Configuration",
			"icon": "settings",
		},
	)

	# Define CPQ links
	cpq_links = [
		{"type": "Link", "link_type": "DocType", "label": "Product Configurator", "link_to": "Product Configurator"},
		{"type": "Link", "link_type": "DocType", "label": "Configuration Result", "link_to": "Configuration Result"},
		{"type": "Link", "link_type": "DocType", "label": "Configuration Template", "link_to": "Configuration Template"},
		{"type": "Link", "link_type": "Report", "label": "Component Demand", "link_to": "Component Demand", "dependencies": "Configuration Result"},
		{"type": "Link", "link_type": "Report", "label": "Configuration Usage", "link_to": "Configuration Usage", "dependencies": "Product Configuration"},
		{"type": "Link", "link_type": "Report", "label": "Configured Product Sales", "link_to": "Configured Product Sales", "dependencies": "Configuration Result"},
	]

	for link in cpq_links:
		workspace.append("links", link)

	workspace.save(ignore_permissions=True)
	frappe.db.commit()
