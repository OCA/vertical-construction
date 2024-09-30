import logging
import re

from iteration_utilities import duplicates

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Bc3Version(models.Model):
    _name = "bc3.version"
    _description = "BC3 Version"
    _order = "name"
    name = fields.Char(required=True)
    register_ids = fields.One2many(
        "bc3.version.register", "version_id", string="Registers"
    )

    @api.constrains("register_ids")
    def _check_registers(self):
        for record in self:
            if record.register_ids:
                register_name = record.register_ids.mapped("name")
                if len(list(duplicates(register_name))) > 0:
                    raise ValidationError(_("Register name should unique"))


class Bc3VersionRegister(models.Model):
    _name = "bc3.version.register"
    _description = "BC3 Version Register"
    _order = "name"
    name = fields.Selection(
        selection=[
            ("v", "~V"),
            ("k", "~K"),
            ("c", "~C"),
            ("d", "~D"),
            ("t", "~T"),
            ("g", "~G"),
            ("f", "~F"),
        ],
        required=True,
    )
    description = fields.Text("Rule Description")
    rule_ids = fields.One2many(
        "bc3.version.register.rule", "register_id", string="Rule Lines"
    )
    version_id = fields.Many2one("bc3.version", string="Version", ondelete="cascade")
    model_id = fields.Many2one(
        "ir.model",
        "Model",
        required=True,
        ondelete="cascade",
        domain=[
            "|",
            "|",
            ("model", "=", "sale.order"),
            ("model", "=", "sale.order.line"),
            ("model", "=", "product.product"),
        ],
    )
    edit_existent = fields.Boolean("The register may edit existent records")

    @api.onchange("description", "rule_ids")
    def get_regular_expression(self):
        if self.description and self.rule_ids:
            self.description[0].lower()
            register_line = self.description[1:].rstrip().strip().split("|")
            register_line.pop(0)
            len_rule_child = len(self.rule_ids.filtered(lambda x: not x.is_child))
            if len(register_line) > len_rule_child:
                del register_line[-1]
            if not len(register_line) == len(
                self.rule_ids.filtered(lambda x: not x.is_child)
            ):
                raise ValidationError(
                    _("Error in register description or not enough rules")
                )
            i = 0
            for rule in self.rule_ids.filtered(lambda x: not x.is_child):
                rule.generate_regular_expression(register_line[i])
                i += 1


class Bc3VersionRegisterRule(models.Model):
    _name = "bc3.version.register.rule"
    _description = "BC3 Version Register Rule"
    _order = "sequence"

    sequence = fields.Integer()
    model_id = fields.Many2one("ir.model", ondelete="cascade")
    field_id = fields.Many2one(
        "ir.model.fields",
        "Field",
        domain=[
            ("model_id", "=", model_id),
            (
                "ttype",
                "not in",
                [
                    "many2one_reference",
                    "reference",
                    "serialized",
                    "job_serialized",
                    "selection",
                ],
            ),
        ],
        ondelete="cascade",
    )
    register_id = fields.Many2one(
        "bc3.version.register", string="Register", ondelete="cascade"
    )
    is_child = fields.Boolean("Child")
    regular_expression = fields.Char("Regular expression")
    primary_key = fields.Boolean("Primary key")
    field_ids = fields.Many2many(
        "ir.model.fields",
        string="Field",
        domain=[
            (
                "ttype",
                "not in",
                [
                    "many2one_reference",
                    "reference",
                    "serialized",
                    "job_serialized",
                    "selection",
                ],
            ),
        ],
        ondelete="cascade",
    )

    def generate_regular_expression(self, line):
        code = line
        code = code.replace(" ", "").replace("\\", "\\\\?")
        pattern3 = r"[^<>\\\[\]{}?]+"
        replacement2 = r'([à-ü-À-Üa-zA-Z0-9_.+#;,":/\ \-\%\²\³\=\€\ª\º]+)'
        html = re.sub(pattern3, replacement2, code)
        pattern6 = r"\{"
        replacement6 = "("
        pattern7 = r"\}"
        replacement7 = ")*"
        html = re.sub(pattern6, replacement6, html)
        html = re.sub(pattern7, replacement7, html)
        pattern8 = r"\(\\.*\)\*"
        replacement8 = '(\\?[à-ü-À-Üa-zA-Z0-9_+.#;,":/\\ \\-\\%\\²\\³\\=\\€\\ª\\º]+)*'
        html = re.sub(pattern8, replacement8, html)
        html = html.replace("(\\?", "(\\\\?")
        pattern9 = r"\[\([^?]*\)\]"
        replacement9 = '([à-ü-À-Üa-zA-Z0-9_+.#,:";/\\ \\-\\%\\²\\³\\=\\€\\ª\\º]+)*'
        html = re.sub(pattern9, replacement9, html)
        pattern10 = r"\[\\.*\+\)\]"
        replacement10 = '(\\?[à-ü-À-Üa-zA-Z0-9_+.#,:";/\\ \\-\\%\\²\\³\\=\\€\\ª\\º]+)*'
        html = re.sub(pattern10, replacement10, html)
        html = html.replace("(\\?", "(\\\\?")
        pattern11 = r"\(\(.*\+\)\\\\\?\)\*"
        replacement11 = r'([à-ü-À-Üa-zA-Z0-9_+.#,:";/\ \-\%\²\³\=\€\ª\º]+\\\\?)*'
        html = re.sub(pattern11, replacement11, html)
        html = html.replace("<", "").replace(">", "")
        self.regular_expression = html
