# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Project(models.Model):
    _name = 'project.project'
    _inherit = 'project.project'

    site = fields.Many2one('res.partner')

    @api.multi
    def onchange_partner_id(self, partner_id):
        res = super(Project, self).onchange_partner_id(partner_id)
        if partner_id:
            res['value'].update({'site': partner_id})
        return res
