{
    "name": "BC3 files importer",
    "author": "Binhex, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/vertical-construction",
    "category": "BC3",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["project", "sale_management"],
    "data": [
        "security/bc3_file_security.xml",
        "security/ir.model.access.csv",
        "wizard/bc3_import_wizard_views.xml",
        "views/bc3_version_views.xml",
        "data/bc3_version_data.xml",
        "views/sale_order_views.xml",
        "data/uom_data.xml",
        "data/product_data.xml",
    ],
    "external_dependencies": {
        "python": ["iteration_utilities", "chardet"],
    },
}
