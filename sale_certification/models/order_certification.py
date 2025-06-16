from odoo import api, fields, models

INVOICE_STATUS = [
    ("invoiced", "Fully Invoiced"),
    ("to invoice", "To Invoice"),
    ("no", "Nothing to Invoice"),
]


class OrderCertification(models.Model):
    _name = "order.certification"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Base model to define a certification"
    _order = "id desc"

    order_id = fields.Many2one(
        "sale.order", string="Sale Order", required=True, ondelete="cascade"
    )
    name = fields.Char(
        string="Certification",
        required=True,
        copy=False,
        default=lambda self: self.env["ir.sequence"].next_by_code("order.certification")
        or "New",
    )
    certification_line_ids = fields.One2many(
        "certification.line", "certification_id", string="Lines"
    )
    chapter_cert_ids = fields.Many2many("sale.order.line", string="Certified Chapters")
    certification_date = fields.Datetime(string="Date", default=fields.Datetime.now)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    invoice_status = fields.Selection(
        selection=INVOICE_STATUS,
        compute="_compute_invoice_status",
        store=True,
    )
    invoice_count = fields.Integer(compute="_compute_get_invoiced")
    invoice_ids = fields.Many2many(
        comodel_name="account.move",
        string="Invoices",
        compute="_compute_get_invoiced",
        copy=False,
    )

    @api.depends("certification_line_ids.invoice_lines")
    def _compute_get_invoiced(self):
        for cert in self:
            invoice_lines = cert.certification_line_ids.invoice_lines
            invoices = invoice_lines.move_id.filtered(
                lambda r: r.move_type in ("out_invoice", "out_refund")
            )
            cert.invoice_ids = invoices
            cert.invoice_count = len(invoices)

    def button_confirm(self):
        self.state = "confirmed"
        self.certification_date = fields.Datetime.now(self)

    def button_cancel(self):
        self.state = "cancel"

    def button_back2draft(self):
        self.state = "draft"

    @api.depends("state", "certification_line_ids.invoice_status")
    def _compute_invoice_status(self):
        confirmed_certifications = self.filtered(lambda cert: cert.state == "confirmed")
        (self - confirmed_certifications).invoice_status = "no"
        if not confirmed_certifications:
            return
        lines_domain = [("display_type", "=", False)]
        line_invoice_status_all = [
            (certification.id, invoice_status)
            for certification, invoice_status in self.env[
                "certification.line"
            ]._read_group(
                lines_domain
                + [("certification_id", "in", confirmed_certifications.ids)],
                ["certification_id", "invoice_status"],
            )
        ]
        for certification in confirmed_certifications:
            line_invoice_status = [
                d[1] for d in line_invoice_status_all if d[0] == certification.id
            ]
            if certification.state != "confirmed":
                certification.invoice_status = "no"
            elif any(
                invoice_status == "to invoice" for invoice_status in line_invoice_status
            ):
                certification.invoice_status = "to invoice"
            elif line_invoice_status and all(
                invoice_status == "invoiced" for invoice_status in line_invoice_status
            ):
                certification.invoice_status = "invoiced"
            else:
                certification.invoice_status = "no"

    def create_invoice(self, retention=False, retention_value=0.0):
        invoices = self.env["account.move"]
        for certification in self.filtered(
            lambda cert: cert.state == "confirmed"
            and cert.invoice_status == "to invoice"
        ):
            for order in certification.certification_line_ids.mapped(
                "sale_line_ids.order_id"
            ):
                invoices |= order.with_context(
                    certification=certification,
                    retention=retention,
                    retention_value=retention_value,
                )._create_invoices()
        return self.env["sale.order"].action_view_invoice(invoices=invoices)

    def action_view_invoice(self, invoices=False):
        if not invoices:
            invoices = self.mapped("invoice_ids")
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = invoices.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        action["context"] = {
            "default_move_type": "out_invoice",
        }
        return action
