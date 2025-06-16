from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import float_is_zero


class SaleOrder(models.Model):
    _inherit = "sale.order"

    certification_ids = fields.One2many(
        "order.certification", "order_id", string="Certifications"
    )
    is_certifiable = fields.Boolean(
        string="Certifiable?",
        default=False,
        help="Check if the order is in a state that allows to create certifications",
    )
    certification_count = fields.Integer(
        compute="_compute_certification_count",
    )
    certified_percentage = fields.Float(
        string="Certified Quantities",
        compute="_compute_certified_percentage",
        digits=(16, 2),
    )
    retention_invoice_count = fields.Integer(
        string="Invoice Count", compute="_compute_retention_invoices_count"
    )

    def _compute_certification_count(self):
        for order in self:
            order.certification_count = len(
                order.certification_ids.filtered(lambda cert: cert.state != "cancel")
            )

    def _compute_certified_percentage(self):
        for order in self:
            total_qty = sum(order.order_line.mapped("product_uom_qty"))
            certified_qty = sum(order.order_line.mapped("qty_certified"))
            if total_qty:
                order.certified_percentage = max(
                    (certified_qty / total_qty) * 100.0, 0.0
                )
            else:
                order.certified_percentage = 0.0

    def open_certify_wizard(self):
        self.ensure_one()
        return {
            "name": "Certify Order",
            "type": "ir.actions.act_window",
            "res_model": "certification.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_order_id": self.id},
        }

    def action_view_certifications(self, certifications=False):
        if not certifications:
            certifications = self.mapped("certification_ids")

        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale_certification.order_certification_action"
        )
        if len(certifications) > 1:
            action["domain"] = [("id", "in", certifications.ids)]
        elif len(certifications) == 1:
            form_view = [
                (
                    self.env.ref(
                        "sale_certification.view_order_certifications_form"
                    ).id,
                    "form",
                )
            ]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = certifications.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        return action

    def create_certifications(self, mode="regular", options=None):
        certification_vals_list = []
        certification_item_sequence = 1
        for order in self:
            order = order.with_company(order.company_id)

            certification_vals = order._prepare_certification(mode, options)
            certificable_lines = order._get_certificable_lines(mode, options)

            if not any(not line.display_type for line in certificable_lines):
                continue

            certification_line_vals = []
            for line in certificable_lines:
                certification_line_vals.append(
                    Command.create(
                        line._prepare_certification_line(
                            mode, options, certification_item_sequence
                        )
                    ),
                )
                certification_item_sequence += 1

            certification_vals["certification_line_ids"] += certification_line_vals
            certification_vals_list.append(certification_vals)
        if not certification_vals_list:
            raise UserError(
                _(
                    "Cannot create a certification."
                    " No items are available to certify.\n\n"
                )
            )

        return self._create_certifications(certification_vals_list)

    def _create_certifications(self, certification_vals_list):
        return self.env["order.certification"].sudo().create(certification_vals_list)

    def _prepare_certification(self, mode, options):
        self.ensure_one()

        values = {
            "order_id": self.id,
            "company_id": self.company_id.id,
            "certification_line_ids": [],
        }
        return values

    def _get_certificable_lines(self, mode, options):
        """Return the certificable lines for order `self`."""
        certificable_line_ids = []
        pending_section = None
        current_section = None
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )

        for line in self.order_line:
            if line.display_type == "line_section":
                pending_section = current_section = line
                continue
            if line.display_type != "line_note" and float_is_zero(
                line.qty_to_certify, precision_digits=precision
            ):
                continue
            if line.qty_to_certify > 0 or line.display_type == "line_note":
                if mode == "chapters" and (
                    not current_section
                    or current_section.id not in options.get("chapter_ids", [])
                ):
                    continue
                if pending_section:
                    certificable_line_ids.append(pending_section.id)
                    pending_section = None
                certificable_line_ids.append(line.id)

        return self.env["sale.order.line"].browse(certificable_line_ids)

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        certification = self._context.get("certification", False)
        retention = self._context.get("retention", False)
        retention_value = self._context.get("retention_value", 0.0)
        if certification and retention and retention_value:
            for move in moves:
                retention_line_vals = {
                    "name": _("Retention for Certification %s") % certification.name,
                    "quantity": 1.0,
                    "move_id": move.id,
                    "display_type": "product",
                }
                if retention == "percentage":
                    retention_line_vals["name"] += f" ({retention_value * 100:.2f}%)"
                    retention_line_vals["price_unit"] = (
                        -1 * move.amount_untaxed_signed * retention_value
                    )
                elif retention == "value":
                    retention_line_vals["price_unit"] = -1 * retention_value
                retention_move_line = self.env["account.move.line"].create(
                    retention_line_vals
                )
                moves |= retention_move_line.create_retention_invoice_line(
                    certification
                )
        return moves

    def _get_invoiceable_lines(self, final=False):
        certification = self._context.get("certification", False)
        if certification:
            sale_order_lines = certification.certification_line_ids.filtered(
                lambda cert_line: cert_line.invoice_status == "to invoice"
            ).mapped("sale_line_ids")
        else:
            sale_order_lines = super()._get_invoiceable_lines(final)
        return sale_order_lines.with_context(certification=certification)

    def _get_retention_invoices(self):
        return self.mapped(
            "invoice_ids.invoice_line_ids.retention_invoice_line.move_id"
        ).filtered(lambda move: move.state != "cancel" and move.retention_invoice)

    def _compute_retention_invoices_count(self):
        for order in self:
            retention_invoices = order._get_retention_invoices()
            order.retention_invoice_count = len(retention_invoices)

    def action_view_retention_invoices(self):
        retention_invoices = self._get_retention_invoices()
        if not retention_invoices:
            raise UserError(_("No retention invoices found for this order."))
        return self.action_view_invoice(retention_invoices)
