# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDeliveryUsability(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier1 = cls.env['delivery.carrier'].create({
            'name': 'Carrier one',
            'delivery_type': 'fixed',
            'product_id': cls.env['product.product'].create({
                'name': 'Shipping one', 'type': 'service'}).id,
        })
        cls.carrier2 = cls.carrier1.copy({'name': 'Carrier two'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test product', 'type': 'consu'})
        cls.picking = cls.env['stock.picking'].create({
            'picking_type_id': cls.env.ref('stock.picking_type_out').id,
            'location_id': cls.env.ref('stock.stock_location_stock').id,
            'location_dest_id': cls.env.ref('stock.stock_location_customers').id,
            'carrier_id': cls.carrier1.id,
            'move_ids': [(0, 0, {
                'name': 'move',
                'product_id': cls.product.id,
                'product_uom_qty': 1,
                'product_uom': cls.product.uom_id.id,
                'location_id': cls.env.ref('stock.stock_location_stock').id,
                'location_dest_id': cls.env.ref('stock.stock_location_customers').id,
            })],
        })

    def test_fields_tracked(self):
        for fname in ('carrier_id', 'carrier_tracking_ref'):
            self.assertTrue(
                self.env['stock.picking']._fields[fname].tracking,
                "%s must be tracked" % fname)

    def test_carrier_not_readonly_in_picking_form(self):
        # Form() cannot open this picking in 18.0: the view of stock_delivery
        # makes partner_id required with "carrier_id.integration_level", a
        # path that the Python evaluation of Form does not support. The view
        # is checked on its arch instead.
        arch = self.env['stock.picking'].get_view(
            self.env.ref('stock.view_picking_form').id, 'form')['arch']
        carrier_fields = etree.fromstring(arch).xpath("//field[@name='carrier_id']")
        self.assertTrue(carrier_fields)
        for field in carrier_fields:
            self.assertEqual(field.get('readonly'), '0')

    def _flush_tracking(self):
        # Tracking is computed on commit, and a record created in the same
        # transaction is not tracked until then: force it, as the mail tests
        # do (MailCase.flush_tracking).
        self.env.flush_all()
        self.cr.precommit.run()

    def test_change_carrier_on_done_picking(self):
        picking = self.picking
        picking.action_confirm()
        picking.move_ids.quantity = 1
        picking.move_ids.picked = True
        picking._action_done()
        self.assertEqual(picking.state, 'done')
        self._flush_tracking()
        n_msg = len(picking.message_ids)
        picking.write({
            'carrier_id': self.carrier2.id,
            'carrier_tracking_ref': 'TRACK-1',
        })
        self._flush_tracking()
        picking.invalidate_recordset(['message_ids'])
        self.assertEqual(picking.carrier_id, self.carrier2)
        self.assertEqual(picking.carrier_tracking_ref, 'TRACK-1')
        self.assertGreater(len(picking.message_ids), n_msg)
