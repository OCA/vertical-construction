# -*- coding: utf-8 -*-

from odoo import models, fields


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    isArchitect = fields.Boolean()
