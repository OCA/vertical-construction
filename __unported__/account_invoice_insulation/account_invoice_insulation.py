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
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import decimal_precision as dp
import netsvc

class account_invoice_line(osv.osv):

    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'
    _columns = {
        'rvalue' : fields.float('R-Value', change_default=True),
        'surface' : fields.float('Surface (sq ft)', change_default=True),
        'product_insulation': fields.boolean('Insulation Product'),
        'product_rvalue' : fields.integer('R-Value'),
        'product_sprayfoam': fields.boolean('Spray Foam Product'),

        }

    _defaults = {
        'product_insulation': False,
        'product_rvalue': 0.0,
        'product_sprayfoam': False,
        'rvalue': 0.0,
        'surface': 0.0,
        }

account_invoice_line()
