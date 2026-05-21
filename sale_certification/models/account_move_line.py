from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    certification_line_ids = fields.Many2many(
        "certification.line",
        "certification_line_invoice_rel",
        "invoice_line_id",
        "certification_line_id",
        string="Certification Lines",
        readonly=True,
        copy=False,
    )
    retention_invoice_line = fields.Many2one(
        comodel_name="account.move.line",
        help="The retention invoice line related to this line.",
        copy=False,
        ondelete="restrict",
    )

    def find_retention_invoice(self, certification):
        retention_invoice = certification.mapped(
            "order_id.invoice_ids.invoice_line_ids.retention_invoice_line.move_id"
        ).filtered(lambda move: move.state == "draft" and move.retention_invoice)
        if retention_invoice:
            return retention_invoice[0]
        return False

    def create_retention_invoice_line(self, certification):
        self.ensure_one()
        move_id = self.find_retention_invoice(certification)
        if not move_id:
            move_id = self.env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": self.move_id.partner_id.id,
                    "date": fields.Date.context_today(self),
                    "retention_invoice": True,
                }
            )
        retention_vals = {
            "display_type": "product",
            "name": self.name,
            "quantity": 1.0,
            "move_id": move_id.id,
            "price_unit": -1 * self.price_subtotal,
            "balance": -1 * self.price_subtotal,
            "retention_invoice_line": self.id,
            "currency_id": move_id.currency_id.id,
        }
        self.retention_invoice_line = self.env["account.move.line"].create(
            retention_vals
        )
        return move_id
