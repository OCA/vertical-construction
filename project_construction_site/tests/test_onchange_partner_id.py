from openerp.tests import common


class TestOnchangePartnerId(common.TransactionCase):

    def test_onchange_partner_id(self):
        project_record = self.env['project.project'].create({
            "name": "Sample Project",
        })

        partner_record = self.env['res.partner'].create({
            "name": "Sample Partner"
        })

        project_record.onchange_partner_id(partner_record.id)

        self.assertEqual(project_record.partner_id, project_record.site)
