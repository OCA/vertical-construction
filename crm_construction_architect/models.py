# -*- coding: utf-8 -*-

from openerp import models, fields


class Lead(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    architect = fields.Many2one('res.partner',
                                domain="[('isArchitect', '=', '1')]")
