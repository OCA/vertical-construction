# -*- coding: utf-8 -*-

from openerp import models, fields


class Lead(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    calculator = fields.Many2one('res.users')
    calculator_next_action = fields.Char(default='Calculate')
    calculator_start_date = fields.Date()
    calculation_hours = fields.Float()
