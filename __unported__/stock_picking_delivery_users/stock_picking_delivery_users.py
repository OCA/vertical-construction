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

from osv import fields, osv

class stock_picking_delivery_users(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
        'user_ids': fields.many2many('res.users', 'stock_picking_users_rel', 'picking_id',
                'user_id', 'Assigned to'),
        'user_id': fields.many2one('res.users','Assigned to'),
    }

    def on_change_user_ids(self, cr, uid, ids, users):
        if not users[0][2]:
            return {'value': {'user_id': False}}
        return {'value': {'user_id': users[0][2][0]}}
        

stock_picking_delivery_users()
