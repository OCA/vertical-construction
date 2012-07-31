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


import time

from report import report_sxw

class quotation(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(quotation, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_line_number': self.get_line_number,
        })
        self.line_number = 1

    def get_line_number(self):
        result = self.line_number
        self.line_number += 1
        return result

report_sxw.report_sxw('report.sale.order.quotation',
                      'sale.order',
                      'addons/sale_insulation/report/sale_order_quotation.rml',
                      parser=quotation,
                      header="external")
