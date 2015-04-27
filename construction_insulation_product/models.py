# -*- coding: utf-8 -*-

from openerp import models, fields


class Product(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    insulation = fields.Boolean('Insulation product')
    rvalue = fields.Integer('R-Value', help='Thermal resistance')
    sprayfoam = fields.Boolean('SPF', help="SPray Foam product uses square foot and R-value to compute the board foot. Choose board foot as the UoS")
