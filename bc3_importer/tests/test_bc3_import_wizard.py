import base64
import os

from odoo.addons.base.tests.common import BaseCommon

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class TestBC3ImportWizard(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(os.path.join(__location__, "bc3_file_test.bc3"), "rb") as file:
            bc3_content = file.read()
        cls.bc3_import_wizard = cls.env["bc3.import.wizard"].create(
            {
                "bc3_file": base64.b64encode(bc3_content),
                "bc3_file_name": "test.bc3",
                "project_id": cls.env.ref("project.project_project_1").id,
                "version_id": cls.env.ref("bc3_importer.bc3_version_2020_v2").id,
                "partner_id": cls.env.ref("base.res_partner_1").id,
                "create_products": False,
                "sale_id": cls.env.ref("sale.sale_order_1").id,
            }
        )

    def test_do_action(self):
        result = self.bc3_import_wizard.do_action()
        self.assertEqual(result["res_model"], "sale.order", "Wrong model")
        self.assertEqual(result["res_id"], self.bc3_import_wizard.sale_id.id)
        self.assertEqual(result["view_mode"], "form")
        self.assertEqual(result["target"], "current")
        self.assertEqual(result["type"], "ir.actions.act_window")

    def _get_chapter_item_line(self, order, chapter_code, item_code):
        order_lines = order.order_line.sorted("sequence")
        chapter = order_lines.filtered(lambda line: line.bc3_code == chapter_code)
        self.assertEqual(len(chapter), 1)
        chapter_lines = order_lines.filtered(
            lambda line: line.sequence > chapter.sequence
        )
        next_chapter = chapter_lines.filtered(lambda line: line.display_type)[:1]
        if next_chapter:
            chapter_lines = chapter_lines.filtered(
                lambda line: line.sequence < next_chapter.sequence
            )
        item = chapter_lines.filtered(lambda line: line.bc3_code == item_code)
        self.assertEqual(len(item), 1)
        return item

    def test_do_action_measurements(self):
        """The ~M records are printed on the line of their own chapter,
        whatever their position in the file, and an empty dimension is not
        used."""
        with open(
            os.path.join(__location__, "bc3_file_measurements_test.bc3"), "rb"
        ) as file:
            bc3_content = file.read()
        wizard = self.env["bc3.import.wizard"].create(
            {
                "bc3_file": base64.b64encode(bc3_content),
                "bc3_file_name": "measurements.bc3",
                "partner_id": self.partner.id,
            }
        )
        wizard.do_action()
        order = wizard.sale_id
        c01_line = self._get_chapter_item_line(order, "C01", "E04CM040")
        c02_line = self._get_chapter_item_line(order, "C02", "E04CM040")
        self.assertIn(
            "Muro M1 | 1 (units) | 10.0 (length) x 1.0 (width) x 2.0 (height)"
            " | Partial: 20.00",
            c01_line.name,
        )
        self.assertIn(
            "Zapata Z1 | 2 (units) | 3.0 (length) x 0.5 (height) | Partial: 3.00",
            c01_line.name,
        )
        self.assertNotIn("Muro M2", c01_line.name)
        self.assertIn(
            "Muro M2 | 3 (units) | 5.0 (length) x 1.0 (width) x 1.0 (height)"
            " | Partial: 15.00",
            c02_line.name,
        )
        self.assertNotIn("Muro M1", c02_line.name)
        self.assertNotIn("Zapata Z1", c02_line.name)

    def test_format_measurement_row(self):
        wizard = self.bc3_import_wizard
        self.assertEqual(
            wizard._format_measurement_row(["", "Muro", "2", "", "3", ""]),
            "Muro | 2 (units) | 3.0 (width) | Partial: 6.00",
        )
        self.assertEqual(
            wizard._format_measurement_row(["", "Planta baja", "", "", "", ""]),
            "Planta baja",
        )
        self.assertEqual(
            wizard._format_measurement_row(["3", "a*b", "2", "3", "", ""]),
            "a*b | 2 (units) | 3.0 (length)",
        )
        self.assertFalse(
            wizard._format_measurement_row(["1", "Subtotal", "", "", "", ""])
        )
        self.assertFalse(wizard._format_measurement_row(["", "Muro", "x", "", "", ""]))
