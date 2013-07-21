# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

{
    "name" : "Stock Picking Delivery Order Insulation",
    "version" : "1.0",
    "author" : "Savoir-faire Linux",
    "website" : "http://www.savoirfairelinux.com",
    "license" : "AGPL-3",
    "category" : "Stock",
    "description" : """
This module adds area and thermal resistance of insulation products to the 
delivery orders views and report.
    """,
    "depends" : [
        "product_insulation",
        "stock_picking_delivery_users",
    ],
    "demo" : [],
    "test" : [],
    "images" : [],
    "data" : [
        "report/stock_picking_delivery_order_insulation.xml",
        "stock_picking_delivery_insulation_view.xml",
    ],
    "installable": True,
    "complexity": "easy",
}
