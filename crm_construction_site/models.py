# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Lead(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    site = fields.Many2one('res.partner')

    @api.onchange('partner_id')
    def _change_site_when_empty(self):
        if self.partner_id:
            self.site = self.partner_id.id
