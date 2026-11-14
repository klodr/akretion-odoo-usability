# Copyright 2017-2024 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Confirm Wizard',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'license': 'AGPL-3',
    'summary': 'Open a wizard when you confirm a sale order to update important info',
    'author': 'Akretion',
    'website': 'https://github.com/akretion/odoo-usability',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_confirm_view.xml',
        'views/sale_order.xml',
    ],
    'installable': True,
}
