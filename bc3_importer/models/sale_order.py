from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"
    bc3 = fields.Boolean("BC3 sale order")
    bc3_file_property = fields.Char("File property")
    bc3_version_format = fields.Char("Version / Format")
    bc3_version_date = fields.Date("Version date")
    bc3_program = fields.Char("Program")
    bc3_header = fields.Char("Header")
    bc3_identifying_label = fields.Char("Identifying label")
    bc3_character_set = fields.Char("Character set")
    bc3_comment = fields.Text("Comment")
    bc3_information_type = fields.Char("Information Type")
    bc3_certification_number = fields.Char("Certification number")
    bc3_certification_date = fields.Date("Certification date")
    bc3_base_url = fields.Char("Base url")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    bc3_code = fields.Char("Code")
