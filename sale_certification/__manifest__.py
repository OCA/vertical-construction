{
    "name": "Sale Certification",
    "summary": (
        "This module allows to certificate sales orders " "in a construction context"
    ),
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Binhex,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/vertical-construction",
    "category": "Sales",
    "depends": [
        "sale",
    ],
    "maintainers": ["Christian-RB"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rules.xml",
        "wizard/certification_invoice_wizard_view.xml",
        "wizard/certification_wizard_view.xml",
        "views/view_order_certifications.xml",
        "views/view_order_form_certify.xml",
        "views/order_certifications_menu.xml",
        "views/account_views.xml",
        "report/certification_reports.xml",
        "report/certification_templates.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "sale_certification/static/src/css/report_certification.css",
        ],
        "web.report_assets_pdf": [
            "sale_certification/static/src/css/report_certification.css",
        ],
    },
}
