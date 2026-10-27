# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoices(self, sale_orders):
        sale_orders = sale_orders.filtered(lambda order: not order.is_certifiable)
        return super()._create_invoices(sale_orders)
