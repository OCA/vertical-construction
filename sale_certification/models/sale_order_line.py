from odoo import api, fields, models
from odoo.fields import Command
from odoo.tools import float_compare, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_certified = fields.Boolean(
        string="Is Certified?",
        compute="_compute_is_certified",
        store=True,
    )
    section_id = fields.Many2one(
        "sale.order.line",
        string="Section",
        domain=[("display_type", "=", "line_section")],
        compute="_compute_section",
        store=True,
        help="Section or Chapter to which this line belongs.",
    )
    certified_lines = fields.Many2many(
        comodel_name="certification.line",
        relation="sale_order_line_certif_line_rel",
        column1="order_line_id",
        column2="certification_line_id",
        copy=False,
    )
    qty_certified = fields.Float(
        string="Certified Quantity",
        compute="_compute_qty_certified",
        digits="Product Unit of Measure",
        store=True,
    )
    qty_to_certify = fields.Float(
        string="Quantity To Certify",
        compute="_compute_qty_to_certify",
        digits="Product Unit of Measure",
        store=True,
    )
    certifiable_quantity = fields.Float(compute="_compute_certifiable_quantity")
    certified_status = fields.Selection(
        selection=[
            ("certified", "Fully Certified"),
            ("to certify", "To Certify"),
            ("no", "Nothing to Certify"),
        ],
        string="Certify Status",
        compute="_compute_certified_status",
        store=True,
    )

    @api.depends("qty_certified", "qty_delivered", "product_uom_qty", "state")
    def _compute_qty_to_certify(self):
        for line in self:
            if line.state == "sale" and not line.display_type:
                if line.product_id.invoice_policy == "order":
                    line.qty_to_certify = line.product_uom_qty - line.qty_certified
                else:
                    line.qty_to_certify = line.qty_delivered - line.qty_certified
            else:
                line.qty_to_certify = 0

    @api.depends(
        "state", "product_uom_qty", "qty_delivered", "qty_to_certify", "qty_certified"
    )
    def _compute_certified_status(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for line in self:
            if line.state != "sale":
                line.certified_status = "no"
            elif not float_is_zero(line.qty_to_certify, precision_digits=precision):
                line.certified_status = "to certify"
            elif (
                float_compare(
                    line.qty_invoiced, line.product_uom_qty, precision_digits=precision
                )
                >= 0
            ):
                line.certified_status = "certified"
            else:
                line.certified_status = "no"

    @api.depends("certified_lines.certification_id.state", "certified_lines.quantity")
    def _compute_qty_certified(self):
        for line in self:
            qty_certified = 0.0

            for certified_line in line.certified_lines:
                if certified_line.certification_id.state != "cancel":
                    qty_certified += certified_line.product_uom_id._compute_quantity(
                        certified_line.quantity, line.product_uom
                    )

            line.qty_certified = qty_certified

    @api.depends(
        "order_id.order_line",
        "order_id.order_line.sequence",
        "order_id.order_line.display_type",
    )
    def _compute_section(self):
        for line in self:
            if not line.order_id:
                line.section_id = False
                continue

            last_section = None

            for line2 in line.order_id.order_line.sorted(key=lambda r: r.sequence):
                if line2.display_type == "line_section":
                    last_section = line2
                if line2.id == line.id:
                    break

            line.section_id = last_section.id if last_section else False

    @api.depends(
        "product_uom_qty", "qty_delivered", "qty_certified", "product_id.invoice_policy"
    )
    def _compute_certifiable_quantity(self):
        for line in self:
            if line.product_id.invoice_policy == "delivery":
                line.certifiable_quantity = max(
                    line.qty_delivered - line.qty_certified, 0
                )
            else:
                line.certifiable_quantity = max(
                    line.product_uom_qty - line.qty_certified, 0
                )

    def _compute_is_certified(self):
        CertificationLine = self.env["certification.line"]
        for line in self:
            line.is_certified = bool(
                CertificationLine.search([("sale_line_ids", "in", [line.id])], limit=1)
            )

    def _prepare_certification_line(self, mode, options, sequence):
        """Prepare the values to create the new certification line
           for a sales order line.

        :param optional_values: any parameter that should be added to
                                the returned certification line
        :rtype: dict
        """
        self.ensure_one()
        if mode in ["percentage", "chapters"]:
            quantity = self.qty_to_certify * options.get("percentage", 1)
        else:
            quantity = self.qty_to_certify
        res = {
            "display_type": self.display_type or False,
            "sequence": sequence or self.sequence,
            "name": self.name,
            "product_id": self.product_id.id,
            "product_uom_id": self.product_uom.id,
            "quantity": quantity,
            "sale_line_ids": [Command.link(self.id)],
        }
        return res

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        certification = self._context.get("certification", False)
        if certification:
            certification_line_ids = certification.certification_line_ids.filtered(
                lambda line, self=self: self.id in line.sale_line_ids.ids
            )
            res["quantity"] = sum(certification_line_ids.mapped("qty_to_invoice"))
            res["certification_line_ids"] = [
                Command.link(certification_line_id.id)
                for certification_line_id in certification_line_ids
            ]

        return res
