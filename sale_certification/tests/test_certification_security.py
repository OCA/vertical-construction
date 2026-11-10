# Copyright 2026 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.fields import Command
from odoo.tests import new_test_user, tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestCertificationSecurity(SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_internal = new_test_user(
            cls.env, login="cert_internal", groups="base.group_user"
        )
        cls.user_salesman = new_test_user(
            cls.env, login="cert_salesman", groups="sales_team.group_sale_salesman"
        )
        cls.user_manager = new_test_user(
            cls.env, login="cert_manager", groups="sales_team.group_sale_manager"
        )
        cls.sale_order.write({"is_certifiable": True})
        cls.sale_order.action_confirm()
        cls.env["certification.wizard"].create(
            {"sale_order_ids": [Command.set(cls.sale_order.ids)]}
        ).create_certifications()
        cls.certification = cls.sale_order.certification_ids
        cls.menu_root = cls.env.ref("sale_certification.order_certification_menu_root")

    def test_internal_user_has_no_access(self):
        for model in (
            "order.certification",
            "certification.line",
            "certification.wizard",
            "certification.invoice.wizard",
        ):
            with self.assertRaises(AccessError):
                self.env[model].with_user(self.user_internal).check_access_rights(
                    "read"
                )
        menus = self.env["ir.ui.menu"].with_user(self.user_internal)._visible_menu_ids()
        self.assertNotIn(self.menu_root.id, menus)

    def test_salesman_cannot_delete_certifications(self):
        certification = self.certification.with_user(self.user_salesman)
        certification.button_confirm()
        self.assertEqual(certification.state, "confirmed")
        with self.assertRaises(AccessError):
            certification.unlink()
        menus = self.env["ir.ui.menu"].with_user(self.user_salesman)._visible_menu_ids()
        self.assertIn(self.menu_root.id, menus)

    def test_manager_can_delete_certifications(self):
        self.certification.with_user(self.user_manager).unlink()
        self.assertFalse(self.certification.exists())
