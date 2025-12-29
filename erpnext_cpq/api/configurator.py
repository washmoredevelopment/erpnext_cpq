# Copyright (c) 2024, washmoredevelopment and contributors
# For license information, please see license.txt

import json

import frappe


# =============================================================================
# HELPERS
# =============================================================================


def _get_option_choices(configurator, option_name: str) -> list:
	"""
	Get choices for a specific option from the configurator's option_choices table.

	Args:
	    configurator: Product Configurator document
	    option_name: The option name to filter by

	Returns:
	    list: List of Option Choice rows for the given option
	"""
	if not configurator.option_choices:
		return []
	return [c for c in configurator.option_choices if c.option_name == option_name]


# =============================================================================
# RULE MATCHING
# =============================================================================


def rule_matches(rule, selections: dict) -> bool:
	"""
	Check if a single rule's condition is met based on user selections.

	Args:
	    rule: Configurator Item Rule row
	    selections: dict of {option_name: value}

	Returns:
	    bool: True if the rule condition is satisfied
	"""
	condition_type = rule.condition_type

	# Always - item is always included
	if condition_type == "Always":
		return True

	# When Equals - include when option equals specific value
	if condition_type == "When Equals":
		return str(selections.get(rule.option_name, "")) == str(rule.option_value)

	# When Set - include when Check option is checked (value == 1)
	if condition_type == "When Set":
		val = selections.get(rule.option_name)
		return val == 1 or val == "1" or val is True

	# When Not Empty - include when Data option has any value
	if condition_type == "When Not Empty":
		val = selections.get(rule.option_name)
		return val is not None and str(val).strip() != ""

	# When Greater Than - include when numeric option > value
	if condition_type == "When Greater Than":
		return _numeric_comparison(selections, rule, ">")

	# When Less Than - include when numeric option < value
	if condition_type == "When Less Than":
		return _numeric_comparison(selections, rule, "<")

	# When In List - include when option value is in comma-separated list
	if condition_type == "When In List":
		values = [v.strip() for v in (rule.option_value or "").split(",")]
		return str(selections.get(rule.option_name, "")) in values

	return False


def _numeric_comparison(selections: dict, rule, default_operator: str) -> bool:
	"""
	Perform numeric comparison using the comparison field or default operator.

	Args:
	    selections: dict of {option_name: value}
	    rule: Configurator Item Rule row
	    default_operator: Default comparison operator (> or <)

	Returns:
	    bool: Result of the comparison
	"""
	try:
		selection_val = float(selections.get(rule.option_name) or 0)
		rule_val = float(rule.option_value or 0)
	except (ValueError, TypeError):
		return False

	# Use the comparison field if set, otherwise use default
	operator = rule.comparison if rule.comparison else default_operator

	if operator == ">":
		return selection_val > rule_val
	elif operator == ">=":
		return selection_val >= rule_val
	elif operator == "<":
		return selection_val < rule_val
	elif operator == "<=":
		return selection_val <= rule_val
	elif operator == "=":
		return selection_val == rule_val

	return False


# =============================================================================
# QUANTITY CALCULATION
# =============================================================================


def calculate_qty(rule, selections: dict) -> float:
	"""
	Calculate quantity for a matched rule.

	Two modes:
	1. If qty_from_option is set, use that option's value * multiplier
	2. Otherwise, use base_qty

	Args:
	    rule: Configurator Item Rule row
	    selections: dict of {option_name: value}

	Returns:
	    float: Calculated quantity
	"""
	if rule.qty_from_option:
		try:
			base = float(selections.get(rule.qty_from_option) or 0)
		except (ValueError, TypeError):
			base = 0
		multiplier = 1 if rule.qty_multiplier is None else rule.qty_multiplier
		return base * multiplier
	else:
		return rule.base_qty or 0


# =============================================================================
# DESCRIPTION HANDLING
# =============================================================================


def get_description(rule, selections: dict) -> str | None:
	"""
	Get description for an item based on rule configuration.

	Three-tier fallback:
	1. description_override - explicit override text
	2. description_from_option - pull from another option's value
	3. None - use item's default description

	Args:
	    rule: Configurator Item Rule row
	    selections: dict of {option_name: value}

	Returns:
	    str or None: Description text or None to use item default
	"""
	if rule.description_override:
		return rule.description_override
	elif rule.description_from_option:
		val = selections.get(rule.description_from_option)
		# Return None if value is missing/empty so item default is used
		if val is not None and str(val).strip() != "":
			return str(val)
		return None
	else:
		return None


# =============================================================================
# MAIN EVALUATION ENGINE
# =============================================================================


def evaluate_rules(configurator_name: str, selections: dict) -> dict:
	"""
	Evaluate all rules in a configurator against user selections.

	Key behaviors:
	- Iterates all item_rules from the configurator
	- For each matching rule, calculates qty
	- Same item from multiple rules = additive quantities

	Args:
	    configurator_name: Product Configurator name
	    selections: dict of {option_name: value}

	Returns:
	    dict: {item_code: {"item_code": str, "qty": float, "description": str|None}}
	"""
	configurator = frappe.get_doc("Product Configurator", configurator_name)

	result_items = {}

	for rule in configurator.item_rules:
		if rule_matches(rule, selections):
			qty = calculate_qty(rule, selections)
			item_code = rule.item_code

			if item_code in result_items:
				# Same item from multiple rules: add quantities
				result_items[item_code]["qty"] += qty
				# Check if this rule has a description override and existing doesn't
				if result_items[item_code]["description"] is None:
					result_items[item_code]["description"] = get_description(rule, selections)
			else:
				result_items[item_code] = {
					"item_code": item_code,
					"qty": qty,
					"description": get_description(rule, selections),
				}

	return result_items


# =============================================================================
# PRICING
# =============================================================================


def get_item_prices(items: dict, args: dict) -> dict:
	"""
	Fetch prices for items using ERPNext's get_item_details.

	Args:
	    items: dict from evaluate_rules {item_code: {...}}
	    args: dict with price_list, customer, company, doctype, currency

	Returns:
	    dict: Same structure with rate and amount added to each item
	"""
	from erpnext.stock.get_item_details import get_item_details

	price_list = args.get("price_list")
	customer = args.get("customer")
	company = args.get("company")
	doctype = args.get("doctype", "Quotation")
	currency = args.get("currency")

	# Get currency from price list if not provided
	if not currency and price_list:
		currency = frappe.db.get_value("Price List", price_list, "currency")

	for item_code, item_data in items.items():
		try:
			item_details = get_item_details(
				{
					"item_code": item_code,
					"price_list": price_list,
					"customer": customer,
					"company": company,
					"qty": item_data["qty"],
					"doctype": doctype,
					"conversion_rate": 1,
					"plc_conversion_rate": 1,
				}
			)
			rate = item_details.get("price_list_rate") or 0
		except Exception:
			rate = 0

		item_data["rate"] = rate
		item_data["amount"] = rate * item_data["qty"]

		# Fetch item_name and stock_uom if not already set
		if "item_name" not in item_data or "uom" not in item_data:
			item_doc = frappe.get_cached_value(
				"Item", item_code, ["item_name", "stock_uom", "description"], as_dict=True
			)
			if item_doc:
				item_data["item_name"] = item_doc.item_name
				item_data["uom"] = item_doc.stock_uom
				# Use item's description if rule didn't override
				if item_data.get("description") is None:
					item_data["description"] = item_doc.description

	return items


# =============================================================================
# DIALOG FIELD GENERATION
# =============================================================================


@frappe.whitelist()
def get_configurator_dialog_fields(configurator_name: str) -> list:
	"""
	Convert Configurator Options to Frappe dialog field definitions.

	Args:
	    configurator_name: Product Configurator name

	Returns:
	    list: List of field dicts suitable for frappe.prompt()
	"""
	configurator = frappe.get_doc("Product Configurator", configurator_name)
	fields = []

	for option in configurator.options:
		field = {
			"fieldname": option.option_name,
			"label": option.label,
			"fieldtype": option.field_type,
			"reqd": option.required,
			"default": option.default_value,
			"description": option.help_text,
		}

		# Handle Select type - build options from option_choices table
		# Show labels in the dropdown for better UX, but store the internal value
		if option.field_type == "Select":
			options = []
			default_value = None
			label_to_value_map = {}
			choices = _get_option_choices(configurator, option.option_name)
			for choice in choices:
				# Use label as the displayed option
				display = choice.label or choice.value or ""
				options.append(display)
				# Store mapping for value lookup
				label_to_value_map[display] = choice.value or ""
				if choice.is_default:
					default_value = display  # Default is also the label
			field["options"] = "\n".join(options)
			if default_value and not field.get("default"):
				field["default"] = default_value
			# Store the mapping in the field for client-side lookup
			field["label_to_value_map"] = label_to_value_map

		# Handle Int/Float - set min/max
		# Note: Frappe Float fields default to 0 when not set, so we treat 0 as "not configured"
		if option.field_type in ("Int", "Float"):
			if option.min_value:
				field["min"] = option.min_value
			if option.max_value:
				field["max"] = option.max_value

		# Handle depends_on for conditional visibility
		# Note: Frappe dialogs populate 'doc' from get_values() before evaluating depends_on
		if option.depends_on:
			if option.depends_on_value:
				# Escape single quotes in value to prevent JS syntax errors
				escaped_value = option.depends_on_value.replace("\\", "\\\\").replace("'", "\\'")
				field["depends_on"] = f"eval:doc.{option.depends_on} == '{escaped_value}'"
			else:
				field["depends_on"] = f"eval:doc.{option.depends_on}"

		fields.append(field)

	return fields


# =============================================================================
# CONFIGURATION SUMMARY
# =============================================================================


def build_configuration_summary(selections: list, configurator) -> str:
	"""
	Build a formatted configuration summary for display and print.

	Args:
	    selections: list of Configuration Selection child rows
	    configurator: Product Configurator doc

	Returns:
	    str: Formatted summary text as a simple bullet list
	"""
	lines = []
	lines.append("Configuration:")

	for selection in selections:
		label = selection.option_label or selection.option_name
		value = selection.display_value or selection.value

		# For Check fields only, show Yes/No instead of 1/0
		field_type = _get_option_field_type(configurator, selection.option_name)
		if field_type == "Check":
			if value == "1" or value == 1 or value is True or value == "True":
				value = "Yes"
			elif value == "0" or value == 0 or value is False or value == "False":
				value = "No"

		lines.append(f"• {label}: {value}")

	return "\n".join(lines)


def _get_display_value(configurator, option_name: str, value) -> str:
	"""
	Look up the display label for a Select option's value.

	Args:
	    configurator: Product Configurator doc
	    option_name: The option's internal name
	    value: The selected value

	Returns:
	    str: Display label if found, otherwise the value itself
	"""
	for option in configurator.options:
		if option.option_name == option_name:
			if option.field_type == "Select":
				choices = _get_option_choices(configurator, option_name)
				for choice in choices:
					if choice.value == str(value):
						return choice.label or choice.value or ""
			break
	return str(value) if value is not None else ""


def _get_option_label(configurator, option_name: str) -> str:
	"""
	Look up the display label for an option.

	Args:
	    configurator: Product Configurator doc
	    option_name: The option's internal name

	Returns:
	    str: Display label if found, otherwise the option_name itself
	"""
	for option in configurator.options:
		if option.option_name == option_name:
			return option.label
	return option_name


def _get_option_field_type(configurator, option_name: str) -> str | None:
	"""
	Look up the field type for an option.

	Args:
	    configurator: Product Configurator doc
	    option_name: The option's internal name

	Returns:
	    str or None: Field type if found, otherwise None
	"""
	for option in configurator.options:
		if option.option_name == option_name:
			return option.field_type
	return None


# =============================================================================
# CREATE CONFIGURATION API
# =============================================================================


@frappe.whitelist()
def create_configuration(
	configurator: str,
	selections: dict | str,
	parent_doctype: str = None,
	parent_name: str = None,
	parent_item_row: str = None,
) -> str:
	"""
	Create a Product Configuration from user selections.

	Args:
	    configurator: Product Configurator name
	    selections: dict of {option_name: value} or JSON string
	    parent_doctype: "Quotation", "Sales Order", or "Sales Invoice"
	    parent_name: The document name
	    parent_item_row: The items table row name

	Returns:
	    str: Product Configuration name
	"""
	if isinstance(selections, str):
		selections = json.loads(selections)

	configurator_doc = frappe.get_doc("Product Configurator", configurator)

	# Create Product Configuration
	config = frappe.new_doc("Product Configuration")
	config.configurator = configurator
	config.parent_doctype = parent_doctype
	config.parent_name = parent_name
	config.parent_item_row = parent_item_row

	# Add selections as child rows
	for option_name, value in selections.items():
		option_label = _get_option_label(configurator_doc, option_name)
		display_value = _get_display_value(configurator_doc, option_name, value)

		# Normalize boolean values to "1"/"0" for consistent storage
		if value is True:
			stored_value = "1"
		elif value is False:
			stored_value = "0"
		elif value is not None:
			stored_value = str(value)
		else:
			stored_value = ""

		config.append(
			"selections",
			{
				"option_name": option_name,
				"option_label": option_label,
				"value": stored_value,
				"display_value": display_value,
			},
		)

	# Build and set configuration summary
	config.configuration_summary = build_configuration_summary(config.selections, configurator_doc)

	config.insert()

	return config.name


# =============================================================================
# EVALUATE CONFIGURATION API
# =============================================================================


@frappe.whitelist()
def evaluate_configuration(
	configuration_name: str,
	price_list: str,
	customer: str = None,
	company: str = None,
) -> str:
	"""
	Evaluate a configuration and create a priced Configuration Result.

	Args:
	    configuration_name: Product Configuration name
	    price_list: Price List name
	    customer: Customer name (optional)
	    company: Company name

	Returns:
	    str: Configuration Result name
	"""
	# Load configuration
	config = frappe.get_doc("Product Configuration", configuration_name)
	configurator_doc = frappe.get_doc("Product Configurator", config.configurator)

	# Build a map of option field types for proper conversion
	field_types = {}
	for option in configurator_doc.options:
		field_types[option.option_name] = option.field_type

	# Convert selections table to dict
	selections = {}
	for sel in config.selections:
		val = sel.value
		field_type = field_types.get(sel.option_name)

		# Handle boolean string values (legacy data stored as "True"/"False")
		if val == "True":
			val = 1
		elif val == "False":
			val = 0
		elif field_type == "Check":
			# Checkbox: convert to integer 1 or 0
			val = 1 if val == "1" else 0
		elif field_type in ("Int", "Float"):
			# Numeric fields: convert to number for comparisons
			try:
				if field_type == "Float" or "." in str(val):
					val = float(val)
				else:
					val = int(val)
			except (ValueError, TypeError):
				val = 0
		# For Select, Data, and other types: keep as string for rule matching

		selections[sel.option_name] = val

	# Evaluate rules to get matched items
	result_items = evaluate_rules(config.configurator, selections)

	# Get currency from price list
	currency = frappe.db.get_value("Price List", price_list, "currency")

	# Fetch prices for all items
	pricing_args = {
		"price_list": price_list,
		"customer": customer,
		"company": company,
		"doctype": config.parent_doctype or "Quotation",
		"currency": currency,
	}
	result_items = get_item_prices(result_items, pricing_args)

	# Fetch max_discount for each item for weighted average calculation
	for item_code, item_data in result_items.items():
		max_discount = frappe.db.get_value("Item", item_code, "max_discount") or 0
		item_data["max_discount"] = max_discount

	# Create Configuration Result
	result = frappe.new_doc("Configuration Result")
	result.configuration = configuration_name
	result.configurator = config.configurator
	result.currency = currency

	# Add items as child rows and calculate weighted max discount
	total = 0
	weighted_discount_sum = 0
	total_amount = 0

	for item_code, item_data in result_items.items():
		amount = item_data.get("amount", 0)
		result.append(
			"items",
			{
				"item_code": item_code,
				"item_name": item_data.get("item_name", ""),
				"description": item_data.get("description", ""),
				"qty": item_data.get("qty", 0),
				"uom": item_data.get("uom", ""),
				"rate": item_data.get("rate", 0),
				"amount": amount,
			},
		)
		total += amount

		# Accumulate for weighted average max discount
		max_discount = item_data.get("max_discount", 0)
		weighted_discount_sum += amount * max_discount
		total_amount += amount

	# Set total
	result.total = total

	# Calculate weighted average max discount
	if total_amount > 0:
		result.max_discount = weighted_discount_sum / total_amount
	else:
		result.max_discount = 0

	result.insert()

	return result.name


# =============================================================================
# GET CONFIGURATION SELECTIONS API
# =============================================================================


@frappe.whitelist()
def get_configuration_selections(configuration_name: str) -> dict:
	"""
	Load existing configuration selections for dialog pre-fill.

	Args:
	    configuration_name: Product Configuration name

	Returns:
	    dict: {option_name: value} mapping
	"""
	config = frappe.get_doc("Product Configuration", configuration_name)
	configurator_doc = frappe.get_doc("Product Configurator", config.configurator)

	# Build a map of option field types for proper conversion
	field_types = {}
	for option in configurator_doc.options:
		field_types[option.option_name] = option.field_type

	selections = {}
	for sel in config.selections:
		val = sel.value
		field_type = field_types.get(sel.option_name)

		# Handle boolean string values (legacy data stored as "True"/"False")
		if val == "True":
			val = 1
		elif val == "False":
			val = 0
		elif field_type == "Check":
			# Checkbox: convert to integer 1 or 0
			val = 1 if val == "1" else 0
		elif field_type in ("Int", "Float"):
			# Numeric fields: convert to number
			try:
				if field_type == "Float" or "." in str(val):
					val = float(val)
				else:
					val = int(val)
			except (ValueError, TypeError):
				val = 0
		# For Select, Data, and other types: keep as string

		selections[sel.option_name] = val

	return selections


# =============================================================================
# UPDATE CONFIGURATION API
# =============================================================================


@frappe.whitelist()
def update_configuration(
	configuration_name: str,
	selections: dict | str,
) -> dict:
	"""
	Update an existing Product Configuration with new selections.

	Args:
	    configuration_name: Product Configuration name
	    selections: dict of {option_name: value} or JSON string

	Returns:
	    dict: {"name": config.name, "changes": [{"option": str, "from": str, "to": str}]}
	"""
	if isinstance(selections, str):
		selections = json.loads(selections)

	config = frappe.get_doc("Product Configuration", configuration_name)
	configurator_doc = frappe.get_doc("Product Configurator", config.configurator)

	# Capture old values for change tracking
	old_selections = {}
	for sel in config.selections:
		old_selections[sel.option_name] = {
			"value": sel.value,
			"display_value": sel.display_value,
		}

	# Clear existing selections
	config.selections = []

	# Add new selections
	changes = []
	for option_name, value in selections.items():
		option_label = _get_option_label(configurator_doc, option_name)
		display_value = _get_display_value(configurator_doc, option_name, value)

		# Normalize boolean values
		if value is True:
			stored_value = "1"
		elif value is False:
			stored_value = "0"
		elif value is not None:
			stored_value = str(value)
		else:
			stored_value = ""

		config.append(
			"selections",
			{
				"option_name": option_name,
				"option_label": option_label,
				"value": stored_value,
				"display_value": display_value,
			},
		)

		# Track changes
		old_data = old_selections.get(option_name, {})
		old_value = old_data.get("value", "")
		old_display = old_data.get("display_value", old_value)

		if str(stored_value) != str(old_value):
			changes.append(
				{
					"option": option_label,
					"from": old_display or old_value,
					"to": display_value or stored_value,
				}
			)

	# Check for removed options
	for option_name, old_data in old_selections.items():
		if option_name not in selections:
			option_label = _get_option_label(configurator_doc, option_name)
			changes.append(
				{
					"option": option_label,
					"from": old_data.get("display_value") or old_data.get("value"),
					"to": "(removed)",
				}
			)

	# Rebuild configuration summary
	config.configuration_summary = build_configuration_summary(config.selections, configurator_doc)

	config.save()

	return {
		"name": config.name,
		"changes": changes,
	}
