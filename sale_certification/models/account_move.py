from odoo import fields, models


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
