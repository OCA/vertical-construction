# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    certification_count = fields.Integer(
        compute="_compute_origin_certification_count",
    )
    retention_invoice = fields.Boolean(
        help="Indicates if this invoice is a retention invoice.",
    )

    def _compute_origin_certification_count(self):
        for move in self:
            move.certification_count = len(
                move.line_ids.certification_line_ids.certification_id
            )

    def button_cancel(self):
        source_lines = self.filtered(
            lambda move: not move.retention_invoice
        ).invoice_line_ids.filtered("retention_invoice_line")
        retention_lines = source_lines.retention_invoice_line
        retention_invoices = retention_lines.move_id
        posted = retention_invoices.filtered(lambda move: move.state == "posted")
        if posted:
            raise UserError(
                _(
                    "Reset these retention invoices to draft first: %(names)s",
                    names=", ".join(posted.mapped("name")),
                )
            )
        res = super().button_cancel()
        source_lines.retention_invoice_line = False
        retention_lines.unlink()
        empty_retention_invoices = retention_invoices.filtered(
            lambda move: move.state == "draft" and not move.invoice_line_ids
        )
        if empty_retention_invoices:
            empty_retention_invoices.button_cancel()
        return res

    def action_view_source_certifications(self):
        self.ensure_one()
        certification_lines = self.line_ids.certification_line_ids
        source_certifications = certification_lines.certification_id
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "sale_certification.order_certification_action"
        )
        if len(source_certifications) > 1:
            result["domain"] = [("id", "in", source_certifications.ids)]
        elif len(source_certifications) == 1:
            result["views"] = [
                (
                    self.env.ref(
                        "sale_certification.view_order_certifications_form", False
                    ).id,
                    "form",
                )
            ]
            result["res_id"] = source_certifications.id
        else:
            result = {"type": "ir.actions.act_window_close"}
        return result
