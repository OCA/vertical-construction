# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestSaleCertification(SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResCompany = cls.env["res.company"]
        cls.sale_order.write(
            {
                "order_line": [
                    Command.create(
                        {
                            "display_type": "line_section",
                            "name": "Section 1",
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.consumable_product.id,
                            "product_uom_qty": 12.5,
                        }
                    ),
                ],
                "is_certifiable": True,
            }
        )
        cls.sale_order.action_confirm()

    def test_certification_generation(self):
        with self.assertRaises(UserError):
            self.env["certification.wizard"].create(
                {
                    "sale_order_ids": [(6, 0, [self.sale_order.id])],
                    "certification_type": "percentage",
                    "percentage": -1,
                }
            )
        with self.assertRaises(UserError):
            self.env["certification.wizard"].create(
                {
                    "sale_order_ids": [(6, 0, [self.sale_order.id])],
                    "certification_type": "percentage",
                    "percentage": 2,
                }
            )
        with self.assertRaises(UserError):
            self.env["certification.wizard"].create(
                {
                    "sale_order_ids": [(6, 0, [self.sale_order.id])],
                    "certification_type": "chapters",
                }
            )
        # Chapter certification
        self.env["certification.wizard"].create(
            {
                "sale_order_ids": [(6, 0, [self.sale_order.id])],
                "certification_type": "chapters",
                "chapter_ids": [
                    Command.link(
                        self.sale_order.order_line.filtered(
                            lambda line: line.display_type == "line_section"
                        ).id
                    )
                ],
            }
        ).create_certifications()
        self.assertEqual(self.sale_order.certification_count, 1)
        self.assertEqual(len(self.sale_order.certification_ids), 1)

        # Invoicing
        certification = self.sale_order.certification_ids[0]
        certification.button_confirm()
        self.env["certification.invoice.wizard"].create(
            {
                "order_certification_ids": [(6, 0, [certification.id])],
                "retention_monies": True,
                "retention_type": "percentage",
                "retention_percentage": 0.1,
            }
        ).create_invoices()
        self.assertEqual(len(self.sale_order.invoice_ids), 1)
        self.assertEqual(self.sale_order.retention_invoice_count, 1)

        # Percentage certification
        self.assertEqual(self.sale_order.certified_percentage, 41.67)
        self.env["certification.wizard"].create(
            {
                "sale_order_ids": [(6, 0, [self.sale_order.id])],
                "certification_type": "percentage",
                "percentage": 0.5,
            }
        ).create_certifications()
        self.assertEqual(len(self.sale_order.certification_ids), 2)

        # Invoicing
        certification = self.sale_order.certification_ids[1]
        certification.button_confirm()
        self.env["certification.invoice.wizard"].create(
            {
                "order_certification_ids": [(6, 0, [certification.id])],
                "retention_monies": False,
            }
        ).create_invoices()
        self.assertEqual(len(self.sale_order.invoice_ids), 2)
        self.assertEqual(self.sale_order.retention_invoice_count, 1)
        self.sale_order._get_retention_invoices().action_post()

        # Regular certification
        self.env["certification.wizard"].create(
            {
                "sale_order_ids": [(6, 0, [self.sale_order.id])],
                "certification_type": "regular",
            }
        ).create_certifications()
        self.assertEqual(len(self.sale_order.certification_ids), 3)

        # Invoicing
        certification = self.sale_order.certification_ids[2]
        certification.button_confirm()
        self.env["certification.invoice.wizard"].create(
            {
                "order_certification_ids": [(6, 0, [certification.id])],
                "retention_monies": True,
                "retention_type": "value",
                "retention_value": 10,
            }
        ).create_invoices()
        self.assertEqual(len(self.sale_order.invoice_ids), 3)
        self.assertEqual(len(self.sale_order._get_retention_invoices()), 2)
