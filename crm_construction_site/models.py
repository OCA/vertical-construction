# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Lead(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    site = fields.Many2one('res.partner')

    @api.multi
    def on_change_partner_id(self, partner_id):
        res = super(Lead, self).on_change_partner_id(partner_id)
        if partner_id:
            res['value'].update({'site': partner_id})
        return res
