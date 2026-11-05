# Copyright 2026 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import new_test_user, tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestCertificationInvoicing(SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_salesman = new_test_user(
            cls.env,
            login="cert_salesman",
            groups="sales_team.group_sale_salesman,account.group_account_invoice",
        )
        cls.user_sales_only = new_test_user(
            cls.env,
            login="cert_sales_only",
            groups="sales_team.group_sale_salesman",
        )
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        cls.eur.rate_ids.unlink()
        cls.env["res.currency.rate"].create(
            {
                "name": "2000-01-01",
                "rate": 2.0,
                "currency_id": cls.eur.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.eur_pricelist = cls.env["product.pricelist"].create(
            {"name": "EUR pricelist", "currency_id": cls.eur.id}
        )

    def _create_order(self, pricelist=None, user=None):
        user = user or self.user_salesman
        values = {
            "partner_id": self.partner.id,
            "user_id": user.id,
            "is_certifiable": True,
            "order_line": [
                Command.create(
                    {
                        "product_id": self.consumable_product.id,
                        "product_uom_qty": 10.0,
                        "price_unit": 100.0,
                    }
                ),
            ],
        }
        if pricelist:
            values["pricelist_id"] = pricelist.id
        order = self.env["sale.order"].create(values)
        order.action_confirm()
        return order.with_user(user)

    def _certify(self, order):
        previous = order.certification_ids
        self.env["certification.wizard"].with_user(order.env.user).create(
            {"sale_order_ids": [Command.set(order.ids)]}
        ).create_certifications()
        certification = order.certification_ids - previous
        certification.button_confirm()
        return certification

    def _certify_quantity(self, order, quantity):
        certification = self._certify(order)
        certification.button_back2draft()
        certification.certification_line_ids.quantity = quantity
        certification.button_confirm()
        return certification

    def _invoice(self, certification, retention_percentage=0.0):
        values = {"order_certification_ids": [Command.set(certification.ids)]}
        if retention_percentage:
            values.update(
                {
                    "retention_monies": True,
                    "retention_type": "percentage",
                    "retention_percentage": retention_percentage,
                }
            )
        self.env["certification.invoice.wizard"].with_user(
            certification.env.user
        ).create(values).create_invoices()
        return certification.invoice_ids

    def test_invoiced_certification_cannot_be_reset_or_cancelled(self):
        order = self._create_order()
        certification = self._certify(order)
        self._invoice(certification).action_post()
        with self.assertRaises(UserError):
            certification.button_back2draft()
        with self.assertRaises(UserError):
            certification.button_cancel()
        self.assertEqual(certification.state, "confirmed")
        self.assertEqual(order.order_line.qty_to_certify, 0.0)

    def test_certification_with_cancelled_invoice_can_be_cancelled(self):
        order = self._create_order()
        certification = self._certify(order)
        self._invoice(certification).button_cancel()
        certification.button_back2draft()
        certification.button_cancel()
        self.assertEqual(certification.state, "cancel")
        self.assertEqual(order.order_line.qty_to_certify, 10.0)

    def test_retention_in_invoice_currency(self):
        order = self._create_order(pricelist=self.eur_pricelist)
        self.assertEqual(order.currency_id, self.eur)
        certification = self._certify(order)
        invoice = self._invoice(certification, retention_percentage=0.1)
        self.assertEqual(invoice.currency_id, self.eur)
        retention_line = invoice.invoice_line_ids.filtered("retention_invoice_line")
        product_lines = invoice.invoice_line_ids - retention_line
        self.assertAlmostEqual(
            retention_line.price_unit,
            -0.1 * sum(product_lines.mapped("price_subtotal")),
        )
        retention_invoice = order._get_retention_invoices()
        self.assertEqual(retention_invoice.currency_id, self.eur)
        self.assertAlmostEqual(
            retention_invoice.amount_untaxed, -retention_line.price_subtotal
        )
        self.assertAlmostEqual(
            retention_invoice.amount_untaxed_signed, retention_line.balance
        )

    def test_retention_without_invoicing_rights(self):
        order = self._create_order(user=self.user_sales_only)
        certification = self._certify(order)
        invoice = self._invoice(certification, retention_percentage=0.1)
        retention_line = invoice.invoice_line_ids.filtered("retention_invoice_line")
        self.assertAlmostEqual(retention_line.price_unit, -100.0)
        self.assertEqual(len(order._get_retention_invoices()), 1)

    def test_cancelled_invoice_drops_its_retention(self):
        order = self._create_order()
        first = self._certify_quantity(order, 4.0)
        first_invoice = self._invoice(first, retention_percentage=0.1)
        second = self._certify_quantity(order, 6.0)
        self._invoice(second, retention_percentage=0.1)
        retention_invoice = order._get_retention_invoices()
        self.assertAlmostEqual(retention_invoice.amount_untaxed, 100.0)
        first_invoice.button_cancel()
        self.assertAlmostEqual(retention_invoice.amount_untaxed, 60.0)
        second.invoice_ids.button_cancel()
        self.assertEqual(retention_invoice.state, "cancel")
        self.assertFalse(order._get_retention_invoices())

    def test_posted_retention_blocks_invoice_cancellation(self):
        order = self._create_order()
        certification = self._certify(order)
        invoice = self._invoice(certification, retention_percentage=0.1)
        invoice.action_post()
        retention_invoice = order._get_retention_invoices()
        retention_invoice.action_post()
        with self.assertRaises(UserError):
            invoice.button_cancel()
        self.assertEqual(invoice.state, "posted")
        retention_invoice.button_draft()
        invoice.button_cancel()
        self.assertEqual(invoice.state, "cancel")
        self.assertEqual(retention_invoice.state, "cancel")
