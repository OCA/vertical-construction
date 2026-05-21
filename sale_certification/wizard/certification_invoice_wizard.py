from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CertificationInvoiceWizard(models.TransientModel):
    _name = "certification.invoice.wizard"
    _description = "Modal to Invoice a Certification"

    order_certification_ids = fields.Many2many(
        "order.certification", default=lambda self: self.env.context.get("active_ids")
    )
    retention_monies = fields.Boolean(
        string="Apply Retention Monies",
        default=False,
    )
    retention_type = fields.Selection(
        selection=[
            ("percentage", "Percentage"),
            ("value", "Value"),
        ],
        default="percentage",
    )
    retention_percentage = fields.Float(default=0.05)
    retention_value = fields.Float(default=0.0)

    @api.constrains("retention_type")
    def _check_retention_values(self):
        for wizard in self:
            if wizard.retention_type == "percentage" and (
                wizard.retention_percentage < 0 or wizard.retention_percentage > 1
            ):
                raise UserError(_("The percentage must be between 0 and 100."))
            if (
                wizard.retention_type == "value"
                and not wizard.retention_value
                or wizard.retention_value < 0
            ):
                raise UserError(_("You must specify a valid retention value."))

    def create_invoices(self):
        if not self.order_certification_ids:
            raise UserError(_("No certifications selected for invoicing."))
        retention = self.retention_monies and self.retention_type
        retention_value = (
            self.retention_percentage
            if self.retention_type == "percentage"
            else self.retention_value
        )
        return self.order_certification_ids.create_invoice(retention, retention_value)
