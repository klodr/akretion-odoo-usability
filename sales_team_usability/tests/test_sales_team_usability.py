# Copyright 2026 Claude Perrin <klodr@users.noreply.github.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


# post_install: at_install tests run while the loading code still forces
# translate=True on the fields the database holds as translated (odoo/models.py),
# so on a database where sales_team is already installed the field is not yet
# seen as untranslated.
@tagged("post_install", "-at_install")
class TestSalesTeamUsability(TransactionCase):
    def test_tag_name_is_not_translatable(self):
        self.assertFalse(self.env["crm.tag"]._fields["name"].translate)

    def test_tag_name_is_the_same_in_every_language(self):
        self.env["res.lang"]._activate_lang("fr_FR")
        tag = self.env["crm.tag"].create({"name": "Test tag"})
        tag.with_context(lang="fr_FR").write({"name": "Test tag (fr)"})
        self.assertEqual(tag.with_context(lang="en_US").name, "Test tag (fr)")
        self.assertEqual(tag.with_context(lang="fr_FR").name, "Test tag (fr)")
