# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Affero GNU General Public License for more details.
#
#    You should have received a copy of the Affero GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

{
    "name" : "Sale Insulation",
    "version" : "0.1",
    "author" : "Savoir-faire Linux",
    "website" : "http://www.savoirfairelinux.com",
    "license" : "AGPL-3",
    "category" : "Sales",
    "description" : """
    This module allows you to generate a sale order for insulation products.

    Insulation products are sold in square foot (UOS) and stored in PCE or weight.
    Spray foam is sold in board foot (UOS), calculated from the product R-value,
    the sale order line R-value and the area (in square foot).

    For more information on R-value (thermal resistance):
    http://en.wikipedia.org/wiki/R-value_(insulation)
    """,
    "images" : [],
    "depends" : ["sale", "product_insulation"],
    "test" : [],
    "demo" : [],
    "data" : [
	"sale_insulation_report.xml",
	"sale_insulation_view.xml",
	],
    "installable": True,
    "complexity": "normal",
}
