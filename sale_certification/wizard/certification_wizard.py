from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CertificationWizard(models.TransientModel):
    _name = "certification.wizard"
    _description = "Modal to Certify an Order"

    sale_order_ids = fields.Many2many(
        "sale.order", default=lambda self: self.env.context.get("active_ids")
    )
    certification_type = fields.Selection(
        [
            ("regular", "Regular"),
            ("percentage", "Percentage"),
            ("chapters", "Chapters"),
        ],
        default="regular",
        required=True,
    )
    percentage = fields.Float(default=1)
    chapter_ids = fields.Many2many(
        "sale.order.line",
        string="Certifiable Chapters",
        domain="""
            [('order_id', 'in', sale_order_ids),
            ('display_type', '=', 'line_section')]
        """,
    )

    @api.constrains("certification_type")
    def _check_certification_values(self):
        for wizard in self:
            if wizard.certification_type == "percentage" and (
                wizard.percentage <= 0 or wizard.percentage > 1
            ):
                raise UserError(_("The percentage must be between 0 and 100."))
            if wizard.certification_type == "chapters" and not wizard.chapter_ids:
                raise UserError(_("You must select at least one chapter to certify."))

    def create_certifications(self):
        if hasattr(self, f"_create_certifications_options_{self.certification_type}"):
            options = getattr(
                self, f"_create_certifications_options_{self.certification_type}"
            )()
        else:
            options = {}
        certifications = self.sale_order_ids.create_certifications(
            mode=self.certification_type, options=options
        )
        return self.sale_order_ids.action_view_certifications(
            certifications=certifications
        )

    def _create_certifications_regular(self):
        return self.sale_order_ids._create_certifications()

    def _create_certifications_options_percentage(self):
        return {"percentage": self.percentage}

    def _create_certifications_options_chapters(self):
        return {"chapter_ids": self.chapter_ids.ids, "percentage": self.percentage}
