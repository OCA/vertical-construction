from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero


class CertificationLine(models.Model):
    _name = "certification.line"
    _description = "Certification Line"
    _order = "sequence, id"

    certification_id = fields.Many2one(
        "order.certification",
        string="Certification",
        required=True,
        ondelete="cascade",
    )
    sale_line_ids = fields.Many2many(
        "sale.order.line",
        "sale_order_line_certif_line_rel",
        "certification_line_id",
        "order_line_id",
        string="Sales Order Lines",
        readonly=True,
        copy=False,
    )
    invoice_lines = fields.Many2many(
        comodel_name="account.move.line",
        relation="certification_line_invoice_rel",
        column1="certification_line_id",
        column2="invoice_line_id",
        copy=False,
    )
    invoice_status = fields.Selection(
        selection=[
            ("invoiced", "Fully Invoiced"),
            ("to invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
        compute="_compute_invoice_status",
        store=True,
    )
    sequence = fields.Integer()
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        ondelete="restrict",
        check_company=True,
    )
    name = fields.Text(
        string="Description",
    )
    quantity = fields.Float(
        digits="Product Unit of Measure",
    )
    qty_to_invoice = fields.Float(
        string="Quantity To Invoice",
        compute="_compute_qty_to_invoice",
        digits="Product Unit of Measure",
        store=True,
    )
    qty_invoiced = fields.Float(
        string="Invoiced Quantity",
        compute="_compute_qty_invoiced",
        digits="Product Unit of Measure",
        store=True,
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        compute="_compute_product_uom_id",
        store=True,
        readonly=False,
        precompute=True,
        ondelete="restrict",
    )
    display_type = fields.Selection(
        selection=[
            ("line_section", "Section"),
            ("line_note", "Note"),
        ],
        default=False,
    )
    company_id = fields.Many2one(
        related="certification_id.company_id",
        store=True,
        readonly=True,
        precompute=True,
        index=True,
    )
    state = fields.Selection(
        related="certification_id.state",
        string="Certification Status",
        copy=False,
        store=True,
        precompute=True,
    )

    @api.depends("product_id")
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id

    @api.depends("quantity", "sale_line_ids.product_uom_qty")
    def _compute_relative_percentage(self):
        for rec in self:
            total_qty = sum(rec.sale_line_ids.mapped("product_uom_qty"))

            if total_qty:
                rec.relative_percentage = (self.quantity / total_qty) * 100
            else:
                rec.relative_percentage = 0.0

    @api.depends("invoice_lines.move_id.state", "invoice_lines.quantity")
    def _compute_qty_invoiced(self):
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if (
                    invoice_line.move_id.state != "cancel"
                    or invoice_line.move_id.payment_state == "invoicing_legacy"
                ):
                    if invoice_line.move_id.move_type == "out_invoice":
                        qty_invoiced += invoice_line.product_uom_id._compute_quantity(
                            invoice_line.quantity, line.product_uom_id
                        )
                    elif invoice_line.move_id.move_type == "out_refund":
                        qty_invoiced -= invoice_line.product_uom_id._compute_quantity(
                            invoice_line.quantity, line.product_uom_id
                        )
            line.qty_invoiced = qty_invoiced

    @api.depends("state", "quantity", "qty_to_invoice", "qty_invoiced")
    def _compute_invoice_status(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for line in self:
            if line.state != "confirmed":
                line.invoice_status = "no"
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = "to invoice"
            elif (
                float_compare(
                    line.qty_invoiced, line.quantity, precision_digits=precision
                )
                >= 0
            ):
                line.invoice_status = "invoiced"
            else:
                line.invoice_status = "no"

    @api.depends("qty_invoiced", "quantity", "state")
    def _compute_qty_to_invoice(self):
        for line in self:
            if line.state == "confirmed" and not line.display_type:
                line.qty_to_invoice = line.quantity - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
