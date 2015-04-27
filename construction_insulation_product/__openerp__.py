# -*- coding: utf-8 -*-

{
    "name": "Insulation Products",

    "version": "1.1",

    "author": "Savoir-faire Linux,Odoo Community Association (OCA), Mathias Colpaert",

    "website": "http://www.savoirfairelinux.com",

    "license": "AGPL-3",

    "category": "Product",

    "description": """
    This module allows you to define if a product is an insulation product, by 
    adding a checkbox on the product form. Checking the box enables you to enter
    the R-value (thermal resistance) of the product.

    More information about the R-value here:
    http://en.wikipedia.org/wiki/R-value_(insulation)
    """,

    "images": ["images/product_insulation.png"],

    "depends": ["product"],

    "data": ["views.xml"]
}
