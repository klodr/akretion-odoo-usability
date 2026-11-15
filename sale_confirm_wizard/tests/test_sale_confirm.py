# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import Form, new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleConfirm(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test service', 'type': 'service', 'list_price': 10})
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id, 'product_uom_qty': 1})],
        })

    def _open_wizard(self, order, user=None):
        action = order.sale_confirm_wizard_button()
        self.assertEqual(action['res_model'], 'sale.confirm')
        self.assertEqual(action['target'], 'new')
        wizard_model = self.env['sale.confirm']
        if user:
            wizard_model = wizard_model.with_user(user)
        return Form(wizard_model.with_context(
            active_model='sale.order', active_id=order.id))

    def test_wizard_defaults_and_confirm(self):
        order = self.order
        order.client_order_ref = 'PO-1'
        # the address fields of the wizard are reserved to the users of the
        # group "Customer Addresses"
        user = new_test_user(
            self.env, login='sale_confirm_wizard_user',
            groups='sales_team.group_sale_manager,'
            'account.group_delivery_invoice_address')
        form = self._open_wizard(order, user=user)
        self.assertEqual(form.client_order_ref, 'PO-1')
        self.assertEqual(form.partner_invoice_id, order.partner_invoice_id)
        self.assertEqual(form.partner_shipping_id, order.partner_shipping_id)
        form.client_order_ref = 'PO-2'
        wiz = form.save()
        wiz.confirm()
        self.assertEqual(order.state, 'sale')
        self.assertEqual(order.client_order_ref, 'PO-2')

    def test_blocking_warning(self):
        self.partner.write({
            'sale_warn': 'block', 'sale_warn_msg': 'Do not sell'})
        form = self._open_wizard(self.order)
        self.assertEqual(form.sale_warn, 'block')
        wiz = form.save()
        with self.assertRaises(UserError):
            wiz.confirm()
        self.assertEqual(self.order.state, 'draft')

    def test_confirm_button_replaced(self):
        arch = self.env['sale.order'].get_view(
            self.env.ref('sale.view_order_form').id)['arch']
        self.assertEqual(arch.count('sale_confirm_wizard_button'), 2)
