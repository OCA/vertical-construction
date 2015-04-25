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


from report import report_sxw

class delivery_order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(delivery_order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'delivery_men': self.delivery_men,
            'get_line_number': self.get_line_number,
            'get_address': self.get_address,
        })
        self.line_number = 1
        
    def delivery_men(self, men):
        """
        Return the list of delivery men pre-formatted for the report.
        """
        return "\n".join(man.name for man in men)
    
    def get_line_number(self):
        result = self.line_number
        self.line_number += 1
        return result
    
    def get_address(self, partner_id):
        result = u""
        if partner_id:
            result += partner_id.title + u" " if partner_id.title else u""
            result += partner_id.name or u""
            result += u"\n"
            if len(partner_id.address) > 0:
                address = partner_id.address[0]
                result += (address.street or u"") + "\n"
                result += (address.street2 or u"") + "\n"
                result += address.city + u" " if address.city else u""
                result += u"(" + address.state_id.name.upper() + u")" \
                        if address.state_id and address.state_id.name else u""
                result += u"\n"
                result += address.zip if address.zip else u""
        return result

report_sxw.report_sxw('report.stock.picking.delivery.order.insulation',
                      'stock.picking',
                      'addons/stock_picking_delivery_insulation/report/stock_picking_delivery_order_insulation.rml',
                      parser=delivery_order,
                      header="external")
