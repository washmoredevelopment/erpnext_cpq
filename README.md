<!-- Copyright (c) 2025, Washmore Development and contributors
For license information, please see license.txt-->

<div align="center">
    <a href="https://github.com/washmoredevelopment/erpnext_cpq">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="./.github/assets/erpnext-cpq-icon_light.png">
        <img alt="TaxJar" src="./.github/assets/erpnext-cpq-icon_dark.png" width="60">
    </picture>
    </a>
  <h2>ERPNext CPQ</h2>
  <p align="center">
      <p><b>Configure, Price, Quote for ERPNext</b></p>
  </p>
  
  <p align="center">
    <a href="https://github.com/WashmoreHoldings/erpnext_cpq/blob/version-15/LICENSE">
      <img alt="license" src="https://img.shields.io/badge/license-AGPLv3-blue">
    </a>
  </p>

</div>


<br>

> **⚠️ Work in Progress**  
> This app is currently under active development. Recent development can be found on the `develop` branch. The `version-15` branch _will_ contain the beta release for ERPNext v15.

<br>

ERPNext CPQ is a Frappe app that extends ERPNext with comprehensive Configure, Price, Quote (CPQ) capabilities. It enables businesses to sell configurable items (products or services) where users can select options (e.g., processor, RAM, storage, etc.) and the system automatically determines component items, quantities, and pricing based on rule-based configurations.

## Core Principle

**Configurable products ARE real ERPNext Items.** The Product Configurator (Super BOM) is metadata attached to an Item that defines:
1. What options a customer can configure
2. What child items are included based on those selections
3. How quantities and descriptions are derived from selections

## Features

### Product Configuration
- **Product Configurator (Super BOM)**: Master record defining configurable product options and rules
- **Flexible Option Types**: Support for Select (dropdown), Int, Float, Check (checkbox), and Data (text) input types
- **Conditional Options**: Dependent options that show/hide based on other selections
- **Rule-Based Item Mapping**: Powerful rule engine that maps customer selections to component items with conditions like "Always", "When Equals", "When Set", "When Greater Than", etc.

### Sales Transaction Integration
- **Seamless Integration**: Works natively with Quotation, Sales Order, and Sales Invoice
- **Dynamic Configuration Dialog**: Automatically generated dialog based on Product Configurator options
- **Automatic Pricing**: Fetches prices from ERPNext price lists and calculates totals
- **Configuration Persistence**: Configuration details are preserved through document conversions (Quote → SO → Invoice)
- **Enhanced Descriptions**: Configuration summary automatically appended to item descriptions for print formats and reports

### Rule Evaluation Engine
- **Multiple Condition Types**: Always, When Equals, When Set, When Not Empty, When Greater/Less Than, When In List
- **Quantity Calculation**: Support for base quantities, quantity from options, and multipliers
- **Additive Rules**: Multiple rules for the same item combine quantities
- **Description Overrides**: Custom descriptions per rule or pulled from option values

### Manufacturing Bridge (Optional)
- **BOM Generation**: Automatically generate ERPNext BOMs from configuration results
- **Make-to-Order Support**: Each configured product can have its own BOM and Work Order
- **Component Tracking**: Stock entries consume exact components from configuration

## Installation

### Prerequisites
- A working Frappe/ERPNext v15 bench environment
- ERPNext v15 installed on your site

### Install from version-15 branch

```bash
# Get the app from the version-15 branch
bench get-app --branch version-15 https://github.com/WashmoreHoldings/erpnext_cpq.git

# Install the app on your site
bench --site <yoursite.name> install-app erpnext_cpq

# Run migrations
bench --site <yoursite.name> migrate
```

### Development Setup

For development work, use the `develop` branch:

```bash
# Get the app from the develop branch
bench get-app --branch develop https://github.com/WashmoreHoldings/erpnext_cpq.git

# Install the app on your site
bench --site <yoursite.name> install-app erpnext_cpq

# Run migrations
bench --site <yoursite.name> migrate
```

## Usage

### Setting Up a Configurable Product

1. **Create or Edit an Item**: Mark the item as configurable by checking "Is Configurable"
2. **Create Product Configurator**: Link a Product Configurator to the item under the Variants tab.
3. **Define Options**: Add configuration options (e.g., Processor, RAM, Storage) with their field types and choices
4. **Create Item Rules**: Define rules that map option selections to component items with quantities.

### Using in Sales Transactions

1. **Add Item to Transaction**: Add a configurable item to a Quotation, Sales Order, or Sales Invoice
2. **Configure**: Click the "Configure" button that appears for configurable items
3. **Make Selections**: Fill out the configuration dialog with customer choices
4. **Save**: The system automatically:
   - Evaluates rules to determine component items
   - Fetches prices from price lists
   - Updates the item rate and description
   - Creates configuration records for tracking

### Document Conversion

Configuration data automatically flows through document conversions:
- Quotation → Sales Order: Configuration and pricing preserved
- Sales Order → Sales Invoice: Configuration and pricing preserved

## Architecture

The app follows a clean separation between master data (Product Configurator, Options, Rules) and runtime data (Product Configuration, Configuration Result). This design ensures:

- **Native ERPNext Integration**: Configurable items work with all standard ERPNext features (Item Groups, Tax Templates, Pricing Rules, Reports, etc.)
- **No Custom Mapping Required**: Document conversions work automatically because custom fields have identical names across transaction doctypes
- **Flexible Rule Engine**: Supports complex business logic through rule-based evaluation

## File Structure

```
erpnext_cpq/
├── erpnext_cpq/
│   ├── hooks.py                    # DocType event hooks
│   ├── modules.txt                   # Module registration
│   ├── api/
│   │   └── configurator.py          # Rule evaluation, pricing, dialog generation
│   ├── overrides/
│   │   └── transaction.py           # Validation hooks
│   ├── erpnext_cpq/doctype/         # All CPQ DocTypes
│   │   ├── product_configurator/    # Master: Super BOM
│   │   ├── configurator_option/     # Child: Configuration options
│   │   ├── option_choice/           # Child: Dropdown choices
│   │   ├── configurator_item_rule/  # Child: Rules mapping to items
│   │   ├── product_configuration/    # Runtime: Customer selections
│   │   ├── configuration_selection/ # Child: Individual selections
│   │   ├── configuration_result/    # Runtime: Priced output
│   │   └── configuration_result_item/ # Child: Priced line items
│   └── fixtures/
│       └── custom_field.json        # Item + transaction item fields
```

## What Works Natively

The following ERPNext features work without modification:
- Item Groups and reporting
- Item Tax Templates
- Pricing Rules
- Terms and Conditions
- Payment Terms
- Contracts
- Print Formats (configuration appears in description)
- Sales Reports
- Stock management (stock/non-stock items)
- Batch/Serial tracking

## Development Status

This app is currently in **Phase 3: Transaction Integration**. 

### Completed
- ✅ App structure and directory organization
- ✅ Product Configurator DocType and child tables
- ✅ Runtime DocTypes (Product Configuration, Configuration Result)

### In Progress
- 🔄 Rule evaluation engine
- 🔄 Configuration dialog generation
- 🔄 Transaction integration

### Planned
- ⏳ Pricing integration
- ⏳ Validation hooks
- ⏳ Manufacturing bridge

## Contributing

This project is growing from an internal business need. As we were unable to find a maintained CPQ/Product Configuration solution for ERPNext, we've opted to open source it. If you're interested in contributing, feel free to open an issue, PR, or get in touch with us.

## License

This app is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See [LICENSE](license.txt) for details.

