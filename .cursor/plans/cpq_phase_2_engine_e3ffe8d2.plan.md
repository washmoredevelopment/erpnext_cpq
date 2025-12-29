<!-- Copyright (c) 2025, washmoredevelopment and contributors
For license information, please see license.txt-->

---
name: CPQ Phase 2 Engine
overview: Build the configuration engine API in api/configurator.py - rule evaluation with 7 condition types, quantity calculation with multipliers, pricing integration via ERPNext get_item_details, dialog field generation, and configuration summary builder.
todos:
  - id: p2-rule-matches-always
    content: Implement rule_matches for 'Always' condition type
    status: completed
  - id: p2-rule-matches-equals
    content: Implement rule_matches for 'When Equals' - compare option value
    status: completed
  - id: p2-rule-matches-set
    content: Implement rule_matches for 'When Set' - check if checkbox is 1
    status: completed
  - id: p2-rule-matches-not-empty
    content: Implement rule_matches for 'When Not Empty' - value exists and not blank
    status: completed
  - id: p2-rule-matches-greater
    content: Implement rule_matches for 'When Greater Than' with comparison operator
    status: completed
  - id: p2-rule-matches-less
    content: Implement rule_matches for 'When Less Than' with comparison operator
    status: completed
  - id: p2-rule-matches-in-list
    content: Implement rule_matches for 'When In List' - comma-separated values
    status: completed
  - id: p2-calculate-qty-base
    content: Implement calculate_qty with base_qty mode
    status: completed
  - id: p2-calculate-qty-from-option
    content: Implement calculate_qty with qty_from_option and multiplier mode
    status: completed
  - id: p2-get-description
    content: Implement get_description with 3-tier fallback (override/from_option/None)
    status: completed
  - id: p2-evaluate-rules-iterate
    content: Implement evaluate_rules - iterate rules and check matches
    status: completed
  - id: p2-evaluate-rules-aggregate
    content: Implement evaluate_rules - aggregate same item quantities (additive)
    status: completed
  - id: p2-get-item-prices
    content: Implement get_item_prices using ERPNext get_item_details
    status: completed
  - id: p2-dialog-field-select
    content: Implement dialog field generation for Select type with choices
    status: completed
  - id: p2-dialog-field-int-float
    content: Implement dialog field generation for Int/Float with min/max
    status: completed
  - id: p2-dialog-field-check-data
    content: Implement dialog field generation for Check and Data types
    status: completed
  - id: p2-dialog-field-depends
    content: Implement depends_on handling for conditional field visibility
    status: completed
  - id: p2-build-summary-format
    content: Implement build_configuration_summary with decorative format
    status: completed
  - id: p2-build-summary-display-values
    content: Implement display value lookup for Select choices in summary
    status: completed
  - id: p2-create-config-doc
    content: Implement create_configuration - create Product Configuration doc
    status: completed
  - id: p2-create-config-selections
    content: Implement create_configuration - populate Configuration Selection children
    status: completed
  - id: p2-create-config-display-lookup
    content: Implement create_configuration - lookup display values for Select options
    status: completed
  - id: p2-evaluate-config-load
    content: Implement evaluate_configuration - load config and convert to dict
    status: completed
  - id: p2-evaluate-config-rules
    content: Implement evaluate_configuration - call evaluate_rules
    status: completed
  - id: p2-evaluate-config-prices
    content: Implement evaluate_configuration - fetch prices for all items
    status: completed
  - id: p2-evaluate-config-result
    content: Implement evaluate_configuration - create Configuration Result with items
    status: completed
  - id: p2-evaluate-config-total
    content: Implement evaluate_configuration - calculate and set total
    status: completed
---

# CPQ Phase 2: Configuration Engine

Create [`api/configurator.py`](erpnext_cpq/erpnext_cpq/api/configurator.py) with all backend logic.---

## 1. Rule Matching - `rule_matches(rule, selections)`

Implement all 7 condition types from the plan:| Condition Type | Logic | Required Fields ||----------------|-------|-----------------|| Always | `return True` | None || When Equals | `selections.get(option_name) == option_value` | option_name, option_value || When Set | `selections.get(option_name) == 1` | option_name || When Not Empty | `val is not None and val != ""` | option_name || When Greater Than | `float(val) > float(option_value)` | option_name, option_value || When Less Than | `float(val) < float(option_value)` | option_name, option_value || When In List | `val in option_value.split(",")` | option_name, option_value (comma-separated) |Note: The `comparison` field on the rule (>, >=, <, <=, =) should be used for more granular numeric comparisons if present.---

## 2. Quantity Calculation - `calculate_qty(rule, selections)`

Two modes from the plan:

```python
if rule.qty_from_option:
    base = float(selections.get(rule.qty_from_option, 0))
    multiplier = rule.qty_multiplier or 1
    return base * multiplier
else:
    return rule.base_qty
```

Example: If `qty_from_option = "ram_sticks"` and user selects 4, and `qty_multiplier = 1`, result is qty 4.---

## 3. Description Handling - `get_description(rule, selections)`

Three-tier fallback from the plan:

```python
if rule.description_override:
    return rule.description_override
elif rule.description_from_option:
    return selections.get(rule.description_from_option)
else:
    return None  # Use item's default description
```

---

## 4. Main Evaluation - `evaluate_rules(configurator_name, selections)`

Key behaviors from Part 4:

1. Iterate all `item_rules` from the configurator
2. For each rule that matches, calculate qty
3. **Same item from multiple rules = additive quantities**
4. Return dict of `{item_code: {item_code, qty, description}}`
```python
result_items = {}
for rule in configurator.item_rules:
    if rule_matches(rule, selections):
        qty = calculate_qty(rule, selections)
        if rule.item_code in result_items:
            result_items[rule.item_code]["qty"] += qty  # Additive!
        else:
            result_items[rule.item_code] = {
                "item_code": rule.item_code,
                "qty": qty,
                "description": get_description(rule, selections)
            }
return result_items
```


---

## 5. Pricing - `get_item_prices(items, args)`

Use ERPNext's native pricing:

```python
from erpnext.stock.get_item_details import get_item_details

# For each item in result_items:
item_details = get_item_details({
    "item_code": item_code,
    "price_list": args.price_list,
    "customer": args.customer,
    "company": args.company,
    "qty": qty,
    "doctype": "Quotation",  # or SO/SI
    "conversion_rate": 1,
    ...
})
rate = item_details.get("price_list_rate") or 0
```

---

## 6. Dialog Field Generation - `get_configurator_dialog_fields(configurator_name)`

**Whitelisted API** - Convert Configurator Options to Frappe dialog fields:| Option field_type | Dialog fieldtype | Special handling ||-------------------|------------------|------------------|| Select | Select | Build options from `choices` child table || Int | Int | Set min/max from `min_value`/`max_value` || Float | Float | Set min/max from `min_value`/`max_value` || Check | Check | - || Data | Data | - |Additional field properties to map:

- `fieldname` = option.option_name
- `label` = option.label
- `reqd` = option.required
- `default` = option.default_value
- `description` = option.help_text
- `depends_on` = build from option.depends_on + option.depends_on_value

For Select options, build options list:

```python
options = "\n".join([choice.value for choice in option.choices])
# Or for labeled options:
options = [{"label": c.label, "value": c.value} for c in option.choices]
```

---

## 7. Configuration Summary - `build_configuration_summary(selections, configurator)`

Format from Part 8:

```javascript
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
