# Copyright 2026 Claude Perrin <klodr@users.noreply.github.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, TransactionCase


class TestProductCategoryTax(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        group = cls.env["account.tax.group"].create({"name": "Test group"})
        tax_model = cls.env["account.tax"]

        def make_tax(name, use):
            return tax_model.create(
                {
                    "name": name,
                    "amount": 10.0,
                    "amount_type": "percent",
                    "type_tax_use": use,
                    "tax_group_id": group.id,
                    "company_id": cls.company.id,
                }
            )

        cls.sale_a = make_tax("Test sale A", "sale")
        cls.sale_b = make_tax("Test sale B", "sale")
        cls.purchase_a = make_tax("Test purchase A", "purchase")
        cls.purchase_b = make_tax("Test purchase B", "purchase")
        categ_model = cls.env["product.category"]
        cls.categ_a = categ_model.create(
            {
                "name": "Test category A",
                "sale_tax_ids": [(6, 0, cls.sale_a.ids)],
                "purchase_tax_ids": [(6, 0, cls.purchase_a.ids)],
            }
        )
        cls.categ_b = categ_model.create(
            {
                "name": "Test category B",
                "sale_tax_ids": [(6, 0, cls.sale_b.ids)],
                "purchase_tax_ids": [(6, 0, cls.purchase_b.ids)],
            }
        )

    def _create_product(self, categ):
        return self.env["product.template"].create(
            {"name": "Test product", "categ_id": categ.id}
        )

    def test_create_takes_taxes_of_category(self):
        product = self._create_product(self.categ_a)
        self.assertEqual(product.taxes_id, self.sale_a)
        self.assertEqual(product.supplier_taxes_id, self.purchase_a)

    def test_change_category_replaces_taxes(self):
        # The taxes of the old category must be replaced, not added to.
        product = self._create_product(self.categ_a)
        product.write({"categ_id": self.categ_b.id})
        self.assertEqual(product.taxes_id, self.sale_b)
        self.assertEqual(product.supplier_taxes_id, self.purchase_b)

    def test_product_variant_follows_category(self):
        product = self._create_product(self.categ_a)
        variant = product.product_variant_id
        self.assertEqual(variant.categ_id, self.categ_a)
        self.assertEqual(variant.taxes_id, self.sale_a)

    def test_onchange_category_sets_taxes(self):
        with Form(self.env["product.template"]) as form:
            form.name = "Test product (form)"
            form.categ_id = self.categ_b
            self.assertEqual(set(form.taxes_id.ids), set(self.sale_b.ids))
            self.assertEqual(set(form.supplier_taxes_id.ids), set(self.purchase_b.ids))

    def test_write_taxes_keeps_category_taxes(self):
        # Unlike the former local port (which raised), the Akretion module
        # rewrites the taxes of the category on any write of the taxes.
        product = self._create_product(self.categ_a)
        product.write({"taxes_id": [(6, 0, self.sale_b.ids)]})
        self.assertEqual(product.taxes_id, self.sale_a)

    def test_write_purchase_taxes_keeps_category_taxes(self):
        product = self._create_product(self.categ_a)
        product.write({"supplier_taxes_id": [(6, 0, self.purchase_b.ids)]})
        self.assertEqual(product.supplier_taxes_id, self.purchase_a)
