# -*- coding: utf-8 -*-
from openerp import fields, models, api

class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    user_ids = fields.Many2many('res.users', 'stock_picking_users_rel', 'picking_id', 'user_id', 'Assigned to')
    user_id = fields.Many2one('res.users', 'Assigned to')

    @api.multi
    def on_change_user_ids(self, users):
        if len(users[0][2]) == 0:
            return {'value': {'user_id': False}}

        return {'value': {'user_id': users[0][2][0]}}