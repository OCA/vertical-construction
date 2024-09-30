import base64
import os

from odoo.tests.common import TransactionCase

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class TestBC3ImportWizard(TransactionCase):
    def setUp(self):
        super(TestBC3ImportWizard, self).setUp()
        with open(os.path.join(__location__, "bc3_file_test.bc3"), "rb") as file:
            bc3_content = file.read()
        self.bc3_import_wizard = self.env["bc3.import.wizard"].create(
            {
                "bc3_file": base64.b64encode(bc3_content),
                "bc3_file_name": "test.bc3",
                "project_id": self.env.ref("project.project_project_1").id,
                "version_id": self.env.ref("bc3_importer.bc3_version_2020_v2").id,
                "partner_id": self.env.ref("base.res_partner_1").id,
                "create_products": False,
                "sale_id": self.env.ref("sale.sale_order_1").id,
            }
        )

    def test_do_action(self):
        result = self.bc3_import_wizard.do_action()
        self.assertEqual(result["res_model"], "sale.order", "Wrong model")
        self.assertEqual(result["res_id"], self.bc3_import_wizard.sale_id.id)
        self.assertEqual(result["view_mode"], "form")
        self.assertEqual(result["target"], "current")
        self.assertEqual(result["type"], "ir.actions.act_window")
