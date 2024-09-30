from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestBC3Version(TransactionCase):
    def setUp(self):
        super(TestBC3Version, self).setUp()
        self.bc3_version = self.env["bc3.version"].create({"name": "Test Version"})
        self.bc3_version_register = self.env["bc3.version.register"].create(
            {
                "name": "v",
                "description": "v|rule1|rule2|rule3",
                "version_id": self.bc3_version.id,
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )
        self.bc3_version_register_rule_1 = self.env["bc3.version.register.rule"].create(
            {
                "sequence": 1,
                "model_id": self.env.ref("base.model_res_partner").id,
                "field_id": self.env.ref("base.field_res_partner__name").id,
                "register_id": self.bc3_version_register.id,
                "is_child": False,
            }
        )
        self.bc3_version_register_rule_2 = self.env["bc3.version.register.rule"].create(
            {
                "sequence": 2,
                "model_id": self.env.ref("base.model_res_partner").id,
                "field_id": self.env.ref("base.field_res_partner__email").id,
                "register_id": self.bc3_version_register.id,
                "is_child": False,
            }
        )
        self.bc3_version_register_rule_3 = self.env["bc3.version.register.rule"].create(
            {
                "sequence": 3,
                "model_id": self.env.ref("base.model_res_partner").id,
                "field_id": self.env.ref("base.field_res_partner__phone").id,
                "register_id": self.bc3_version_register.id,
                "is_child": False,
            }
        )

    def test_get_regular_expression_success(self):
        self.bc3_version_register.get_regular_expression()
        self.assertTrue(self.bc3_version_register_rule_1.regular_expression)
        self.assertTrue(self.bc3_version_register_rule_2.regular_expression)
        self.assertTrue(self.bc3_version_register_rule_3.regular_expression)

    def test_get_regular_expression_error_in_description(self):
        self.bc3_version_register.description = "v|rule1"
        with self.assertRaises(ValidationError):
            self.bc3_version_register.get_regular_expression()

    def test_get_regular_expression_not_enough_rules(self):
        self.bc3_version_register_rule_2.unlink()
        self.bc3_version_register_rule_3.unlink()
        with self.assertRaises(ValidationError):
            self.bc3_version_register.get_regular_expression()
