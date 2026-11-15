# Copyright 2026 Claude Perrin <klodr@users.noreply.github.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase, new_test_user


class TestProductCategoryTaxMultiCompany(TransactionCase):
    """A user who sees every company (Access Rights) but is a member of some
    of them only must still be able to create a product with a category."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env["res.company"].create(
            {"name": "Test other company", "country_id": cls.env.ref("base.fr").id}
        )
        cls.sale_tax = cls._make_tax(cls.company, "Test sale", "sale")
        cls.purchase_tax = cls._make_tax(cls.company, "Test purchase", "purchase")
        cls.sale_tax_2 = cls._make_tax(cls.company, "Test sale 2", "sale")
        cls.purchase_tax_2 = cls._make_tax(cls.company, "Test purchase 2", "purchase")
        cls.other_sale_tax = cls._make_tax(cls.other_company, "Test other sale", "sale")
        cls.other_purchase_tax = cls._make_tax(
            cls.other_company, "Test other purchase", "purchase"
        )
        categ_model = cls.env["product.category"]
        cls.categ = categ_model.create(
            {
                "name": "Test category",
                "sale_tax_ids": [Command.set(cls.sale_tax.ids)],
                "purchase_tax_ids": [Command.set(cls.purchase_tax.ids)],
            }
        )
        cls.categ_2 = categ_model.create(
            {
                "name": "Test category 2",
                "sale_tax_ids": [Command.set(cls.sale_tax_2.ids)],
                "purchase_tax_ids": [Command.set(cls.purchase_tax_2.ids)],
            }
        )
        cls.categ_both = categ_model.create(
            {
                "name": "Test category, both companies",
                "sale_tax_ids": [Command.set((cls.sale_tax | cls.other_sale_tax).ids)],
                "purchase_tax_ids": [
                    Command.set((cls.purchase_tax | cls.other_purchase_tax).ids)
                ],
            }
        )
        groups = "base.group_user,base.group_system,account.group_account_manager"
        # Member of the current company only; base.group_system implies
        # base.group_erp_manager, whose rule on res.company shows every company.
        cls.user_one_company = new_test_user(
            cls.env,
            login="pcta_one_company",
            groups=groups,
            company_id=cls.company.id,
            company_ids=[Command.set(cls.company.ids)],
        )
        cls.user_both_companies = new_test_user(
            cls.env,
            login="pcta_both_companies",
            groups=groups,
            company_id=cls.company.id,
            company_ids=[Command.set((cls.company | cls.other_company).ids)],
        )

    @classmethod
    def _make_tax(cls, company, name, use):
        group = cls.env["account.tax.group"].create(
            {"name": f"{name} group", "company_id": company.id}
        )
        return cls.env["account.tax"].create(
            {
                "name": name,
                "amount": 10.0,
                "amount_type": "percent",
                "type_tax_use": use,
                "tax_group_id": group.id,
                "company_id": company.id,
            }
        )

    def test_create_by_member_of_one_company(self):
        product = (
            self.env["product.template"]
            .with_user(self.user_one_company)
            .create({"name": "Test product", "categ_id": self.categ.id})
        )
        self.assertEqual(product.sudo().taxes_id, self.sale_tax)
        self.assertEqual(product.sudo().supplier_taxes_id, self.purchase_tax)

    def test_write_category_by_member_of_one_company(self):
        product = self.env["product.template"].create(
            {"name": "Test product", "categ_id": self.categ.id}
        )
        self.env["product.template"].with_user(self.user_one_company).browse(
            product.id
        ).write({"categ_id": self.categ_2.id})
        self.assertEqual(product.taxes_id, self.sale_tax_2)
        self.assertEqual(product.supplier_taxes_id, self.purchase_tax_2)

    def test_created_record_keeps_the_caller_context(self):
        # The companies allowed to write the taxes must not stay on the
        # records returned by create(), for instance when another user then
        # works on them.
        product = self.env["product.template"].create(
            {"name": "Test product", "categ_id": self.categ.id}
        )
        self.assertEqual(
            product.env.context.get("allowed_company_ids"),
            self.env.context.get("allowed_company_ids"),
        )
        product.with_user(self.user_one_company).write({"categ_id": self.categ_2.id})
        self.assertEqual(product.taxes_id, self.sale_tax_2)

    def test_create_keeps_taxes_of_all_companies_of_the_user(self):
        # The current company only is active: the taxes of the other company
        # of the user must still be copied from the category.
        product = (
            self.env["product.template"]
            .with_user(self.user_both_companies)
            .with_context(allowed_company_ids=self.company.ids)
            .create({"name": "Test product", "categ_id": self.categ_both.id})
        )
        self.assertEqual(product.sudo().taxes_id, self.sale_tax | self.other_sale_tax)
        self.assertEqual(
            product.sudo().supplier_taxes_id,
            self.purchase_tax | self.other_purchase_tax,
        )

    def test_write_category_removes_taxes_of_other_company(self):
        # Changing the category with the current company only active must also
        # remove the taxes of the other company of the user: the previous
        # taxes are read with the access rules of the context
        # (Many2many.write_real), so they are only seen when all the companies
        # of the user are allowed.
        both = (self.company | self.other_company).ids
        product = (
            self.env["product.template"]
            .with_context(allowed_company_ids=both)
            .create({"name": "Test product", "categ_id": self.categ_both.id})
        )
        self.env.flush_all()
        self.env.invalidate_all()
        product = (
            self.env["product.template"]
            .with_user(self.user_both_companies)
            .with_context(allowed_company_ids=self.company.ids)
            .browse(product.id)
        )
        product.write({"categ_id": self.categ_2.id})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(product.sudo().taxes_id, self.sale_tax_2)
        self.assertEqual(product.sudo().supplier_taxes_id, self.purchase_tax_2)
