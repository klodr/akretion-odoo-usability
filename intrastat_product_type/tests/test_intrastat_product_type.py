# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestIntrastatProductType(TransactionCase):

    def _create(self, **vals):
        vals.setdefault('name', 'Test product')
        return self.env['product.template'].create(vals)

    def test_default_from_type(self):
        self.assertEqual(self._create(type='consu').intrastat_type, 'product')
        self.assertEqual(
            self._create(type='service').intrastat_type, 'service')

    def test_consumable_declared_as_service(self):
        pt = self._create(type='consu', intrastat_type='service')
        self.assertEqual(pt.intrastat_type, 'service')
        self.assertTrue(
            self.env['product.template']._fields['intrastat_type'].required)
        self.assertFalse(
            self.env['product.template']._fields['intrastat_type'].readonly)

    def test_constraints(self):
        with self.assertRaises(ValidationError):
            self._create(type='service', intrastat_type='product')
        with self.assertRaises(ValidationError):
            self._create(
                type='consu', is_storable=True, intrastat_type='service')

    def test_des_uses_intrastat_type(self):
        decl = self.env['l10n.fr.intrastat.service.declaration']
        for ptype, itype, expected in (
                ('consu', 'service', True),
                ('consu', 'product', False),
                ('service', 'service', True)):
            pt = self._create(type=ptype, intrastat_type=itype)
            line = self.env['account.move.line'].new(
                {'product_id': pt.product_variant_id.id})
            self.assertEqual(decl._is_service(line), expected)
