import base64
import io
import os
import re
import tempfile
from datetime import datetime

import chardet

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

BC3_PRODUCTS = {}
created_product = False
parse_later = []
lines = {}
erase_lines = []


class BC3ImportWizard(models.TransientModel):
    _name = "bc3.import.wizard"
    _description = "Import BC3 file"

    @api.model
    def _default_version(self):
        return self.env.ref("bc3_importer.bc3_version_2020_v2") or self.env[
            "bc3.version"
        ].search([], limit=1)

    bc3_file = fields.Binary(string="BC3 file", required=True)
    bc3_file_name = fields.Char(string="BC3 file name")
    project_id = fields.Many2one("project.project", string="Project")
    version_id = fields.Many2one(
        "bc3.version", string="Version", ondelete="cascade", default=_default_version
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer/Vendor",
        store=True,
        readonly=False,
        ondelete="restrict",
        domain="['|', ('parent_id','=', False), ('is_company','=', True)]",
        check_company=True,
    )
    create_products = fields.Boolean("Create non-existent products")
    product_id = fields.Many2one(
        "product.product",
        string="Default product",
        ondelete="cascade",
        help="Select a product which will be used in the BC3 file.",
    )
    sale_id = fields.Many2one("sale.order", "Sale Order")
    sequence = fields.Integer()

    def do_action(self):
        self.ensure_one()
        self.get_uom_products()
        self.sequence = 0
        self.sale_id = (
            self.env["sale.order"]
            .create({"partner_id": self.partner_id.id, "bc3": True})
            .id
        )
        # decode the base64 encoded data
        data = base64.decodebytes(self.bc3_file)
        # create a temporary file, and save the bc3
        fobj = tempfile.NamedTemporaryFile(delete=False)
        fname = fobj.name
        fobj.write(data)
        fobj.close()
        try:
            rawdata = open(fname, "rb").read()
            encoding = chardet.detect(rawdata)["encoding"]
            file_content = list(
                filter(
                    None,
                    io.open(fname, "rt", encoding=encoding, errors="replace")
                    .read()
                    .split("~"),
                )
            )
            for f in file_content:
                self._parse_register(f)
            # do stuff here
        finally:
            # delete the file when done
            os.unlink(fname)
            seq = 0
            line_ids = []
            sorted_chapters = dict(sorted(lines.items()))
            for key in sorted_chapters:
                s = (
                    self.env["sale.order.line"]
                    .sudo()
                    .search(
                        [("bc3_code", "=", key), ("order_id", "=", self.sale_id.id)],
                        limit=1,
                    )
                )
                if s and (
                    (s.price_unit == 1 and s.product_uom_qty == 1)
                    or (s.price_unit == 0 and s.product_uom_qty == 1)
                    or ("%" in s.bc3_code)
                    or (s.price_unit == 1)
                ):
                    s.sudo().unlink()
                    self.env["sale.order.line"].sudo().search(
                        [("id", "in", sorted_chapters[key])]
                    ).unlink()
                elif s:
                    if s.id not in line_ids:
                        line_ids.append(s.id)
                        s.write({"sequence": seq})
                        seq += 1
                    for line in (
                        self.env["sale.order.line"]
                        .sudo()
                        .search(
                            [
                                ("order_id", "=", self.sale_id.id),
                                ("id", "in", sorted_chapters[key]),
                            ]
                        )
                        .sorted("name")
                    ):
                        if line:
                            if (
                                (line.price_unit == 1 and line.product_uom_qty == 1)
                                or (line.price_unit == 0 and line.product_uom_qty == 1)
                                or ("%" in line.bc3_code)
                                or (line.price_unit == 1)
                                or not line.price_subtotal
                            ):
                                line.sudo().unlink()
                            elif line.id not in line_ids:
                                line_ids.append(line.id)
                                line.sudo().write({"sequence": seq})
                                seq += 1
                elif not s and key == "0":
                    for line in (
                        self.env["sale.order.line"]
                        .sudo()
                        .search(
                            [
                                ("order_id", "=", self.sale_id.id),
                                ("id", "in", sorted_chapters[key]),
                            ]
                        )
                        .sorted("name")
                    ):
                        if line:
                            if (
                                (line.price_unit == 1 and line.product_uom_qty == 1)
                                or (line.price_unit == 0 and line.product_uom_qty == 1)
                                or ("%" in line.bc3_code)
                                or (line.price_unit == 1)
                            ):
                                line.sudo().unlink()
                            else:
                                line_ids.append(line.id)
                                line.sudo().write({"sequence": seq})
                                seq += 1
            for s in self.env["sale.order.line"].search(
                [("order_id", "=", self.sale_id.id)], order="sequence asc"
            ):
                if (
                    (s.price_unit == 1 and s.product_uom_qty == 1)
                    or (s.price_unit == 0 and s.product_uom_qty == 1)
                    or (s.bc3_code and "%" in s.bc3_code)
                    or (s.price_unit == 1)
                ) and not s.display_type:
                    s.sudo().unlink()
                elif s.id not in line_ids and not s.display_type == "line_note":
                    s.sudo().unlink()
                elif s.bc3_code not in lines and s.display_type == "line_section":
                    s.sudo().unlink()
                elif s.display_type == "line_section":
                    next_sequence = (
                        self.env["sale.order.line"]
                        .sudo()
                        .search(
                            [
                                ("order_id", "=", self.sale_id.id),
                                ("display_type", "=", "line_section"),
                                ("sequence", ">", s.sequence),
                            ],
                            limit=1,
                        )
                    )
                    if next_sequence and next_sequence.sequence == s.sequence + 1:
                        s.sudo().unlink()
            for c in erase_lines:
                line = (
                    self.env["sale.order.line"]
                    .sudo()
                    .search([("bc3_code", "=", c), ("order_id", "=", self.sale_id.id)])
                )
                if line and not (c in lines):
                    line.sudo().unlink()
        return {
            "name": _("Show Sale Order"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sale.order",
            "views": [(self.env.ref("sale.view_order_form").id, "form")],
            "view_id": self.env.ref("sale.view_order_form").id,
            "target": "current",
            "res_id": self.sale_id.id,
        }

    def parse_line(self, line):
        split_line = line.rstrip().strip().split("|")
        return split_line

    @api.model
    def _parse_register_sale_order(
        self, parsed_line, rules, current_register, red=False
    ):
        if len(parsed_line) == len(rules):
            i = 0
            for rule in rules:
                if len(parsed_line[i]) == 1:
                    self.sale_id[rule.field_id.name] = self._parse_data(
                        parsed_line[i][0], rule.field_id.ttype
                    )
                elif len(parsed_line[i]) > 1:
                    if self.sale_id[rule.field_id.name]:
                        self.sale_id[rule.field_id.name] += self._parse_child_data(
                            parsed_line[i], rule.field_id.ttype
                        )
                    else:
                        self.sale_id[rule.field_id.name] = self._parse_child_data(
                            parsed_line[i], rule.field_id.ttype
                        )
                i += 1
        return True

    # and "\\" not in line[i]
    @api.model
    def _parse_register_product_product(self, line, rules, current_register, red=False):
        return True

    @api.model
    def _search_create_product(self, code):
        product = self.env["product.template"].search(
            [("default_code", "ilike", code[0])], limit=1
        )
        if product:
            return product
        else:
            if self.create_products:
                code_temp = ""
                if len(code) > 1:
                    for c in code:
                        code_temp += c + "-"
                else:
                    code_temp = code
                product = self.env["product.template"].create(
                    {
                        "name": _("Dynamic Product ") + code_temp,
                        "default_code": code_temp,
                    }
                )
            else:
                # Por defecto se ponen unidades
                product = self.env.ref("bc3_importer.product_product_product_units")
            return product

    @api.model
    def _search_create_uom(self, name):
        uom = False
        if name == "m3" or name == "M3" or name == "m³":
            uom = self.env.ref("uom.product_uom_cubic_meter").id or False
        elif name == "m²" or name == "M2" or name == "m2":
            uom = self.env.ref("bc3_importer.product_uom_square_meter").id or False
        elif name == "ud":
            uom = self.env.ref("uom.product_uom_unit").id or False
        else:
            uom = (
                self.env["uom.uom"]
                .search(
                    [
                        "|",
                        "|",
                        ("name", "in", name),
                        ("name", "in", name.upper()),
                        ("name", "in", name.lower()),
                    ],
                    limit=1,
                )
                .id
                or False
            )
        return uom

    def _parse_repeats_line(self, existent_line, temp_line, sale_order_line):
        create_line = False
        if (
            existent_line
            and not existent_line.id == sale_order_line.id
            and not existent_line.display_type
            and not sale_order_line.display_type
        ):
            if not self.line_in_any_dict(sale_order_line.id):
                erase_lines.append(temp_line["bc3_code"])
            return
        if existent_line and not existent_line.id == sale_order_line.id and lines:
            if not self.line_in_dict(
                existent_line.bc3_code, sale_order_line.id
            ) and not (sale_order_line.id in self.sale_id.order_line.ids):
                create_line = True
            elif self.line_in_any_dict(sale_order_line.id):
                create_line = True
        if create_line:
            sale_order_line = sale_order_line.copy(
                {
                    "order_id": self.sale_id.id,
                    "price_unit": sale_order_line.price_unit,
                }
            )
            if (
                sale_order_line
                and "price_unit" in temp_line
                and float(temp_line["price_unit"]) == 1.0
            ):
                temp_line["price_unit"] = sale_order_line.price_unit
            sale_order_line.sudo().write(temp_line)
        else:
            if (
                "product_uom_qty" in temp_line
                and float(temp_line["product_uom_qty"]) == 1.0
                and sale_order_line.product_uom_qty
                and not sale_order_line.display_type
            ):
                temp_line["product_uom_qty"] = sale_order_line.product_uom_qty
            elif not sale_order_line.product_uom_qty == 1:
                temp_line["product_uom_qty"] = (
                    float(temp_line["product_uom_qty"])
                    + sale_order_line.product_uom_qty
                )
            if (
                "price_unit" in temp_line
                and float(temp_line["price_unit"]) == 1.0
                and not sale_order_line.display_type
            ):
                temp_line["price_unit"] = sale_order_line.price_unit
            if "name" in temp_line and sale_order_line.name:
                temp_line["name"] = sale_order_line.name + "-" + temp_line["name"]
            if sale_order_line.display_type:
                temp_line["product_uom_qty"] = 0
                temp_line["price_unit"] = 0
            sale_order_line.sudo().write(temp_line)
        if (
            existent_line
            and not existent_line.id == sale_order_line.id
            and existent_line.display_type
            and existent_line.display_type == "line_section"
        ):
            if existent_line.bc3_code in lines:
                lines[existent_line.bc3_code].append(sale_order_line.id)
            else:
                lines[existent_line.bc3_code] = [sale_order_line.id]

    def _parse_repeats_line_product(self, temp_line, seq, existent_line):
        product = self.env.ref("bc3_importer.product_product_product_units")
        if "bc3_code" in temp_line:
            temp_line["name"] = temp_line["bc3_code"] or product.default_code or "Line"
        else:
            temp_line["name"] = product.default_code or "Line"
        temp_line["product_id"] = product.id
        temp_line["product_uom"] = product.uom_id.id
        temp_line["order_id"] = self.sale_id.id
        temp_line["sequence"] = seq
        if "price_unit" in temp_line and float(temp_line["price_unit"]) == 1.0:
            s = self.env["sale.order.line"].search(
                [
                    ("order_id", "=", self.sale_id.id),
                    ("bc3_code", "=", temp_line["bc3_code"]),
                    ("price_unit", ">", 1),
                ],
                limit=1,
            )
            if s:
                temp_line["price_unit"] = s.price_unit
        sale_order_line = self.env["sale.order.line"].create(temp_line)
        if (
            existent_line
            and not existent_line.id == sale_order_line.id
            and existent_line.display_type
            and existent_line.display_type == "line_section"
        ):
            if existent_line.bc3_code in lines:
                lines[existent_line.bc3_code].append(sale_order_line.id)
            else:
                lines[existent_line.bc3_code] = [sale_order_line.id]

    def _parse_repeats(
        self, rules, i, dependent_rules, parsed_line, line, parent_seq, existent_line
    ):
        if rules[i] in dependent_rules:
            z = 0
            while z < len(parsed_line[i]):
                j = i
                counter = 0
                temp_line = {}
                if parent_seq:
                    seq = parent_seq + 1
                    # self.lines_reorder(seq)
                else:
                    seq = self.sequence
                    self.sequence += 1
                while counter < len(dependent_rules[rules[i]]):
                    if len(parsed_line[j]) == 0:
                        temp_line[
                            dependent_rules[rules[i]][counter]["field_id"]["name"]
                        ] = False
                    else:
                        temp_line[
                            dependent_rules[rules[i]][counter]["field_id"]["name"]
                        ] = parsed_line[j][z]
                    j += 1
                    counter += 1
                z += 1
                temp_line["sequence"] = seq
                sale_order_line = False
                if "bc3_code" in temp_line:
                    sale_order_line = self.env["sale.order.line"].search(
                        [
                            ("order_id", "=", self.sale_id.id),
                            ("bc3_code", "=", temp_line["bc3_code"]),
                        ]
                    )
                    if len(sale_order_line) > 1:
                        if existent_line:
                            chapter = existent_line.bc3_code
                            for s in sale_order_line:
                                if chapter in lines and s.id in lines[chapter]:
                                    sale_order_line = s
                                else:
                                    sale_order_line = False
                if sale_order_line:
                    self._parse_repeats_line(existent_line, temp_line, sale_order_line)
                else:
                    self._parse_repeats_line_product(temp_line, seq, existent_line)

            if line:
                line = {}

    def _update_line(self, line, seq):
        s = False
        if "bc3_code" in line:
            line["bc3_code"] = line["bc3_code"].replace("#", "")
            s = self.env["sale.order.line"].search(
                [
                    ("order_id", "=", self.sale_id.id),
                    ("bc3_code", "=", line["bc3_code"].replace("#", "")),
                ]
            )
        if s:
            for sale_order_line in s:
                if sale_order_line.bc3_code in erase_lines:
                    erase_lines.remove(sale_order_line.bc3_code)
                if (
                    "product_uom_qty" in line
                    and sale_order_line.product_uom_qty
                    and not sale_order_line.display_type
                ):
                    line["product_uom_qty"] = float(line["product_uom_qty"]) + float(
                        sale_order_line.product_uom_qty
                    )
                if (
                    "price_unit" in line
                    and sale_order_line.price_unit
                    and sale_order_line.price_unit > 1
                    and line["price_unit"] == 1
                    and not sale_order_line.display_type
                ):
                    line["price_unit"] = sale_order_line.price_unit
                if "name" in line and sale_order_line.name:
                    if sale_order_line.name not in line["name"]:
                        line["name"] = sale_order_line.name + "- " + line["name"]
                if sale_order_line.display_type:
                    line["product_uom_qty"] = 0
                    line["price_unit"] = 0
                sale_order_line.sudo().write(line)

        else:
            product = self.env.ref("bc3_importer.product_product_product_units")

            if "bc3_code" in line:
                if "name" in line:
                    line["name"] = (
                        line["bc3_code"] or product.default_code or "Line"
                    ) + line["name"]
                else:
                    line["name"] = line["bc3_code"] or product.default_code or "Line"
            else:
                if "name" in line:
                    line["name"] = (product.default_code or "Line") + line["name"]
                else:
                    line["name"] = product.default_code or "Line"
            line["product_id"] = product.id
            line["product_uom"] = product.uom_id.id
            line["order_id"] = self.sale_id.id
            line["sequence"] = seq
            sale_order_line = self.env["sale.order.line"].create(line)

    def _parse_register_edit_sale_order_line(
        self, parsed_line, rules, dependent_rules, rule_ids, current_register, red=False
    ):
        if len(parsed_line) == len(rules):
            primary_key_id = parsed_line[0][0]
            existent_line = self.search_line(primary_key_id.replace("#", ""))
            parent_seq = False
            # Está dentro de un capítulo
            if existent_line:
                parent_seq = existent_line.sequence

            elif "#" in primary_key_id and not existent_line:
                existent_line = (
                    self.env["sale.order.line"]
                    .sudo()
                    .create(
                        {
                            "name": primary_key_id.replace("#", ""),
                            "display_type": "line_section",
                            "bc3_code": primary_key_id.replace("#", ""),
                            "order_id": self.sale_id.id,
                        }
                    )
                )

            i = 0
            seq = False
            line = {}
            while i < len(rules):
                # Repetidos
                if rules[i]["id"] in rule_ids:
                    self._parse_repeats(
                        rules,
                        i,
                        dependent_rules,
                        parsed_line,
                        line,
                        parent_seq,
                        existent_line,
                    )
                # Únicos
                else:
                    if rules[i]["field_id"]["name"]:
                        if len(parsed_line[i]) > 0:
                            line[rules[i]["field_id"]["name"]] = parsed_line[i][0]
                    if parent_seq:
                        seq = parent_seq + 1
                        # self.lines_reorder(seq)
                    else:
                        seq = self.sequence
                        self.sequence += 1
                    line["sequence"] = seq
                i += 1
            # Solo cuando actualiza un dato -> lo hago para todos

            if line:
                self._update_line(line, seq)

        return

    @api.model
    def search_seq_line(self, seq):
        sale_order_line = self.env["sale.order.line"].search(
            [("order_id", "=", self.sale_id.id), ("bc3_code", "=", seq)], limit=1
        )
        return sale_order_line.sequence or False

    @api.model
    def search_line(self, code):
        code = code.replace("#", "")
        a = self.env["sale.order.line"].search(
            [("order_id", "=", self.sale_id.id), ("bc3_code", "=", code)], limit=1
        )
        if not a:
            a = self.env["sale.order.line"].search(
                [
                    ("order_id", "=", self.sale_id.id),
                    ("bc3_code", "=", code.split(".")[0]),
                ],
                limit=1,
            )
        return a

    @api.model
    def search_lines(self, code):
        code = code.replace("#", "")
        a = self.env["sale.order.line"].search(
            [("order_id", "=", self.sale_id.id), ("bc3_code", "=", code)]
        )
        return a

    @api.model
    def lines_reorder(self, seq):
        sale_order_line = self.env["sale.order.line"].search(
            [("order_id", "=", self.sale_id.id), ("sequence", "=", seq)], limit=1
        )
        if sale_order_line:
            for s in self.env["sale.order.line"].search(
                [("order_id", "=", self.sale_id.id), ("sequence", ">=", seq)]
            ):
                s.write({"sequence": s.sequence + 1})
        return

    def _parse_register_sale_order_line_sl(
        self, rule, parsed_line, line, i, product_name, product
    ):
        if (not rule.field_id.relation) or (
            rule.field_id.relation and rule.field_id.relation == "product.template"
        ):
            if (
                not rule.field_id.name == "product_template_id"
                and not rule.field_id.name == "categ_id"
            ):
                if len(parsed_line[i]) == 1 and parsed_line[i]:
                    line[rule.field_id.name] = self._parse_data(
                        parsed_line[i][0], rule.field_id.ttype
                    )
                elif len(parsed_line[i]) > 1:
                    if rule.field_id.name in line:
                        line[rule.field_id.name] += self._parse_child_data(
                            parsed_line[i], rule.field_id.ttype
                        )
                    else:
                        line[rule.field_id.name] = self._parse_child_data(
                            parsed_line[i], rule.field_id.ttype
                        )
            elif rule.field_id.name == "product_template_id":
                if len(parsed_line[i]) == 1 and parsed_line[i]:
                    product_name = self._parse_data(
                        parsed_line[i][0], rule.field_id.ttype
                    )
        elif rule.field_id.relation and rule.field_id.relation == "uom.uom":
            if len(parsed_line[i]) == 1 and parsed_line[i]:
                uom_id = int(self._search_create_uom(parsed_line[i][0]))
                line[rule.field_id.name] = uom_id
                if product and product.uom_id and not product.uom_id.id == uom_id:
                    if created_product:
                        product.uom_id = uom_id
                    else:
                        if uom_id in BC3_PRODUCTS:
                            product = BC3_PRODUCTS[uom_id]
                        else:
                            product = self.env.ref(
                                "bc3_importer.product_product_product_units"
                            )
                    line["product_id"] = product.id
                    line["product_uom"] = product.uom_id.id
        return product_name

    def _parse_line_t(self, line_t, line):
        for t in line_t:
            if t.display_type:
                line["price_unit"] = 0.0
                line["product_id"] = False
                line["product_uom_qty"] = 0.0

            if "display_type" in line and not t.display_type:
                if not t.product_uom_qty > 1:
                    a = t.read(["sequence", "bc3_code"])[0]
                    a["order_id"] = self.sale_id.id
                    a.update(line)
                    t.unlink()
                    sale_order_line = self.env["sale.order.line"].create(a)
                    if (
                        sale_order_line.display_type
                        and sale_order_line.display_type == "line_note"
                    ):
                        if "0" in lines:
                            lines["0"].append(sale_order_line.id)
                        else:
                            lines["0"] = [sale_order_line.id]
                else:
                    line["display_type"] = False
                    t.write(line)

            else:
                t.write(line)
                if t.display_type and line_t.display_type == "line_note":
                    if "0" in lines:
                        lines["0"].append(line_t.id)
                    else:
                        lines["0"] = [line_t.id]

    @api.model
    def _parse_register_sale_order_line(
        self, parsed_line, rules, current_register, red=False
    ):
        product_name = ""
        if len(parsed_line) == len(rules):
            # Se busca el codigo del producto
            if not len(parsed_line[0]) > 0:
                return
            if len(parsed_line[0]) > 0 and "%" in parsed_line[0][0]:
                return
            line_t = self.search_lines(parsed_line[0][0])
            product = self._search_create_product(parsed_line[0])
            if not line_t:
                line = {
                    "name": product.default_code or parsed_line[0],
                    "product_id": product.id,
                    "product_uom_qty": 1,
                    "qty_delivered": 1,
                    "product_uom": product.uom_id.id,
                    "order_id": self.sale_id.id,
                    "sequence": self.sequence,
                }
                self.sequence += 1
            else:
                line = {}
            i = len(rules) - 1
            for rule in rules.sorted(key="sequence", reverse=True):
                # Sale order line
                if rule.model_id.model == "sale.order.line":
                    product_name = self._parse_register_sale_order_line_sl(
                        rule, parsed_line, line, i, product_name, product
                    )

                elif rule.model_id.model == "product.template":
                    if len(parsed_line[i]) == 1:
                        line_type = int(self._parse_data(parsed_line[i][0], "char"))
                        if line_type == 0 and "##" in parsed_line[0][0]:
                            line["display_type"] = "line_note"
                        elif line_type == 0 and "#" in parsed_line[0][0]:
                            line["display_type"] = "line_section"
                i -= 1
            line["name"] = "[" + line["bc3_code"] + "] " + product_name
            if self.create_products:
                product.name = product_name
            if not line_t:
                if "display_type" in line:
                    line["price_unit"] = 0.0
                    line["product_id"] = False
                    line["product_uom_qty"] = 0.0
                sale_order_line = self.env["sale.order.line"].create(line)
                if (
                    sale_order_line.display_type
                    and sale_order_line.display_type == "line_note"
                ):
                    if "0" in lines:
                        lines["0"].append(sale_order_line.id)
                    else:
                        lines["0"] = [sale_order_line.id]
            else:
                self._parse_line_t(line_t, line)
        return True

    @api.model
    def _parse_data(self, data, field_type):
        data = data.replace("\\", "").replace("#", "")
        if field_type in ["char", "text"]:
            return data
        if field_type == "date":
            # if odd -> 0
            if not len(data) % 2 == 0:
                data += "0"
            # AA
            if len(data) == 2:
                return datetime.strptime(data, "%y").date()
            # MMAA
            elif len(data) == 4:
                return datetime.strptime(data, "%m%y").date()
            # DDMMAA
            elif len(data) == 6:
                return datetime.strptime(data, "%d%m%y").date()
            # DDMMAAAA
            elif len(data) == 8:
                return datetime.strptime(data, "%d%m%Y").date()
            return data
        return data

    @api.model
    def _parse_child_data(self, data, field_type):
        if field_type == "char" or field_type == "text":
            result = ""
            for d in data:
                d = d.replace("\\", "").replace("\\\\", "")
                result += d + ";"
            return result
        elif field_type == "float":
            if len(data) > 0:
                return float(data[-1].replace("\\", ""))
            else:
                return float(data.replace("\\", ""))
        return data

    def _parse_register_data(
        self, register_rules, register_line, current_register, model, render_func
    ):
        i = 0
        regular_expression = []
        parser_result = []
        for r in register_rules.filtered(lambda x: not x.is_child):
            regular_expression.append(r.regular_expression)
        if len(regular_expression) == len(register_line):
            i = 0
            while i < len(regular_expression):
                parser_result.append(
                    self._get_results(
                        regular_expression[i], register_line[i].replace("\n", "")
                    )
                )
                i += 1
        else:
            raise ValidationError(_("Parsing error, missing data"))
        if len(parser_result) > 0:
            final_result = []
            for i in parser_result:
                if len(i) > 1:
                    for j in i:
                        final_result.append(j)
                elif not len(i) == 0:
                    final_result.append(i[0])
                else:
                    final_result.append([])
            if register_rules[0].register_id.edit_existent:
                repeat_value_rule = {}
                rule_ids = []
                temp_r = []
                for r in register_rules:
                    if r.field_ids:
                        for a in register_rules.filtered(
                            lambda rule: rule.field_id in r.field_ids
                        ):
                            temp_r.append(a)
                        temp_r.insert(0, r)
                        repeat_value_rule[r] = temp_r
                        rule_ids.append(r.id)
                        rule_ids += register_rules.filtered(
                            lambda rule: rule.field_id in r.field_ids
                        ).ids

                render_func = getattr(self, "_parse_register_edit_" + model, None)
                if not render_func:
                    raise UserError(_("Error parsing the file"))
                render_func(
                    final_result,
                    register_rules,
                    repeat_value_rule,
                    rule_ids,
                    current_register,
                )
                return
            else:
                render_func(final_result, register_rules, current_register)

    def _parse_register(self, line):
        register_type = line[0].lower()
        current_register = register_type
        register_line = (
            line[1:]
            .rstrip()
            .replace("�", "")
            .replace("(", ",")
            .replace(")", ",")
            .replace("[", ",")
            .replace("]", ",")
            .strip()
            .split("|")
        )
        register_rules = (
            self.env["bc3.version.register"]
            .search(
                [
                    ("name", "ilike", register_type),
                    ("version_id", "=", self.version_id.id),
                ],
                limit=1,
            )
            .rule_ids
        )

        if (
            register_rules
            and register_rules[0]
            and register_rules[0].register_id.model_id
        ):
            model = register_rules[0].register_id.model_id.model.replace(".", "_")
            register_line.pop(0)
            if len(register_line) < len(
                register_rules.filtered(lambda x: not x.is_child)
            ):
                for _i in range(
                    abs(
                        len(register_rules.filtered(lambda x: not x.is_child))
                        - len(register_line)
                    )
                ):
                    register_line.append("")
            elif len(register_line) > len(
                register_rules.filtered(lambda x: not x.is_child)
            ):
                for _i in range(
                    abs(
                        len(register_rules.filtered(lambda x: not x.is_child))
                        - len(register_line)
                    )
                ):
                    register_line.pop()
            render_func = getattr(self, "_parse_register_" + model, None)
            if not render_func:
                raise UserError(_("Error parsing the file"))

            self._parse_register_data(
                register_rules, register_line, current_register, model, render_func
            )

    # Parseo
    def get_groups_matches(self, group_id, check_list, text, group_pattern):
        # Hay que revisar las substring:
        for a in check_list:
            t = text[a[0] : a[1]]
            matches = re.finditer(group_pattern[group_id]["expression"], t)
            last_index = (0, 0)
            for match in matches:
                if match.lastindex:
                    for index in range(1, match.lastindex + 1):
                        group_pattern[str(group_id)]["groups"].insert(
                            0, match.group(index)
                        )
                    if not last_index[0] == match.span(index)[0]:
                        group_pattern[str(group_id)]["check"].append(
                            (last_index[0], match.span(index)[0])
                        )
            group_pattern[str(group_id)]["check"].remove(a)
        if len(group_pattern[group_id]["check"]) > 0:
            self.get_groups_matches(
                group_id, group_pattern[group_id]["check"], t, group_pattern
            )
        else:
            return True

    def _parse_matches(self, matches, group_pattern):
        for match in matches:
            # Recorro los grupos
            # Empiezo en 1 porque el primer grupo es todo el match, no me interesa
            last_index = (0, 0)
            if match.lastindex:
                if match.lastindex > 1:
                    for index in range(1, match.lastindex + 1):
                        if str(index) in group_pattern and match.group(index):
                            group_pattern[str(index)]["groups"].append(
                                match.group(index)
                            )
                            # Es el primer grupo
                            if index == 1:
                                last_index = match.span(index)
                            else:
                                if not last_index[1] == match.span(index)[0]:
                                    group_pattern[str(index)]["check"].append(
                                        (last_index[1], match.span(index)[0])
                                    )
                                last_index = match.span(index)
                else:
                    for index in range(1, match.lastindex + 1):
                        if str(index) in group_pattern and match.group(index):
                            group_pattern[str(index)]["groups"].append(
                                match.group(index)
                            )
                            if not last_index[1] == match.span(index)[0]:
                                group_pattern[str(index)]["check"].append(
                                    (last_index[1], match.span(index)[0])
                                )
                                last_index = match.span(index)
        return group_pattern

    def _get_results(self, pattern, text):
        text = text.rstrip()
        result = []
        if pattern:
            pattern_2 = pattern.split("(")
            group_pattern = {}
            counter = 1
            for p in pattern_2:
                if p:
                    group_pattern[str(counter)] = {
                        "expression": "(" + p,
                        "groups": [],
                        "check": [],
                    }
                    counter += 1
            matches = re.finditer(pattern, text)
            group_pattern = self._parse_matches(matches, group_pattern)

            # Reviso los checks
            for i in group_pattern:
                if len(group_pattern[i]["check"]) > 0:
                    self.get_groups_matches(
                        i, group_pattern[i]["check"], text, group_pattern
                    )
            for i in group_pattern:
                result.append(group_pattern[i]["groups"])
        return result

    @api.model
    def get_uom_products(self):
        BC3_PRODUCTS[
            self.env.ref("bc3_importer.product_product_product_units").uom_id.id
        ] = self.env.ref("bc3_importer.product_product_product_units")
        BC3_PRODUCTS[
            self.env.ref("bc3_importer.product_product_product_meter").uom_id.id
        ] = self.env.ref("bc3_importer.product_product_product_meter")
        BC3_PRODUCTS[
            self.env.ref("bc3_importer.product_product_product_square_meter").uom_id.id
        ] = self.env.ref("bc3_importer.product_product_product_square_meter")
        BC3_PRODUCTS[
            self.env.ref("bc3_importer.product_product_product_cubic_meter").uom_id.id
        ] = self.env.ref("bc3_importer.product_product_product_cubic_meter")
        BC3_PRODUCTS[
            self.env.ref("bc3_importer.product_product_product_g").uom_id.id
        ] = self.env.ref("bc3_importer.product_product_product_g")
        BC3_PRODUCTS[
            self.env.ref("bc3_importer.product_product_product_l").uom_id.id
        ] = self.env.ref("bc3_importer.product_product_product_l")

    @api.model
    def line_in_dict(self, code, line_id):
        if code in lines and line_id in lines[code]:
            return True
        return False

    @api.model
    def line_in_any_dict(self, line_id):
        a = self.env["sale.order.line"].search(
            [("order_id", "=", self.sale_id.id), ("id", "=", int(line_id))]
        )
        if a:
            if a in lines:
                return True
            else:
                for d in lines:
                    if line_id in lines[d]:
                        return True
        return False
