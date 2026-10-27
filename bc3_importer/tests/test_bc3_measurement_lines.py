import base64

from odoo.tests.common import TransactionCase


class TestBC3MeasurementLines(TransactionCase):
    def setUp(self):
        super(TestBC3MeasurementLines, self).setUp()
        self.partner = self.env["res.partner"].create({"name": "BC3 Customer"})
        self.product = self.env["product.product"].create(
            {"name": "BC3 Product", "type": "service"}
        )
        self.sale_order = self.env["sale.order"].create(
            {"partner_id": self.partner.id, "bc3": True}
        )
        self.order_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "name": "Concrete wall",
                "bc3_code": "A03B0010",
            }
        )
        self.wizard = self.env["bc3.import.wizard"].create(
            {
                "bc3_file": base64.b64encode(b"~V|TEST|FIEBDC-3/2020|\n"),
                "bc3_file_name": "test.bc3",
                "partner_id": self.partner.id,
                "sale_id": self.sale_order.id,
            }
        )

    def _measurement(self, code, groups):
        return ["", code, "1\\1\\", "24", groups, ""]

    def test_measurement_without_height(self):
        self.wizard.parse_measurement_lines(
            self._measurement("A01\\A03B0010", "\\Wall\\2\\3\\4\\")
        )
        self.assertEqual(
            self.order_line.name,
            "Concrete wall\n\n"
            "Wall | 2 (units) | 3.0 (length) x 4.0 (width) | Partial: 24.00",
        )

    def test_measurement_with_height(self):
        self.wizard.parse_measurement_lines(
            self._measurement("A01\\A03B0010", "\\Pillar\\1\\0.5\\0.5\\3\\")
        )
        self.assertEqual(
            self.order_line.name,
            "Concrete wall\n\n"
            "Pillar | 1 (units) | 0.5 (length) x 0.5 (width) x 3.0 (height)"
            " | Partial: 0.75",
        )

    def test_measurement_several_groups(self):
        self.wizard.parse_measurement_lines(
            self._measurement(
                "A01\\A03B0010", "\\Wall\\2\\3\\4\\\\Pillar\\1\\0.5\\0.5\\3\\"
            )
        )
        self.assertEqual(
            self.order_line.name,
            "Concrete wall\n\n"
            "Wall | 2 (units) | 3.0 (length) x 4.0 (width) | Partial: 24.00\n"
            "Pillar | 1 (units) | 0.5 (length) x 0.5 (width) x 3.0 (height)"
            " | Partial: 0.75",
        )

    def test_measurement_list_of_registers(self):
        other_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "name": "Slab",
                "bc3_code": "A04",
            }
        )
        self.wizard.parse_measurement_lines(
            [
                self._measurement("A01\\A03B0010", "\\Wall\\2\\3\\4\\"),
                self._measurement("A01\\A04", "\\Floor\\1\\5\\6\\"),
            ]
        )
        self.assertIn("Wall | 2 (units)", self.order_line.name)
        self.assertNotIn("Floor", self.order_line.name)
        self.assertEqual(
            other_line.name,
            "Slab\n\nFloor | 1 (units) | 5.0 (length) x 6.0 (width) | Partial: 30.00",
        )

    def test_measurement_skips_invalid_groups(self):
        self.wizard.parse_measurement_lines(
            self._measurement(
                "A01\\A03B0010",
                "\\1\\\\Short\\1\\2\\\\Text\\a\\2\\3\\\\Wall\\2\\3\\4\\",
            )
        )
        self.assertEqual(
            self.order_line.name,
            "Concrete wall\n\n"
            "Wall | 2 (units) | 3.0 (length) x 4.0 (width) | Partial: 24.00",
        )

    def test_measurement_without_valid_groups(self):
        self.wizard.parse_measurement_lines(
            self._measurement("A01\\A03B0010", "\\Text\\a\\2\\3\\")
        )
        self.assertEqual(self.order_line.name, "Concrete wall")

    def test_measurement_ignored_registers(self):
        self.wizard.parse_measurement_lines(
            [
                # Without parent code
                self._measurement("A03B0010", "\\Wall\\2\\3\\4\\"),
                # Unknown code in the sale order
                self._measurement("A01\\UNKNOWN", "\\Wall\\2\\3\\4\\"),
                # Not enough fields
                ["", "A01\\A03B0010", "1\\1\\", "24"],
            ]
        )
        self.assertEqual(self.order_line.name, "Concrete wall")

    def test_measurement_other_sale_order(self):
        other_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        other_line = self.env["sale.order.line"].create(
            {
                "order_id": other_order.id,
                "product_id": self.product.id,
                "name": "Other wall",
                "bc3_code": "A03B0010",
            }
        )
        self.wizard.parse_measurement_lines(
            self._measurement("A01\\A03B0010", "\\Wall\\2\\3\\4\\")
        )
        self.assertEqual(other_line.name, "Other wall")
        self.assertIn("Wall | 2 (units)", self.order_line.name)

    def test_parse_register_measurement(self):
        self.wizard._parse_register("M|A01\\A03B0010|1\\1\\|24|\\Wall\\2\\3\\4\\|\n")
        self.assertEqual(
            self.order_line.name,
            "Concrete wall\n\n"
            "Wall | 2 (units) | 3.0 (length) x 4.0 (width) | Partial: 24.00",
        )
