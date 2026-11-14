# Copyright 2018-2024 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Delivery Usability',
    'version': '18.0.1.0.0',
    'category': 'Stock',
    'license': 'AGPL-3',
    'summary': 'Several usability enhancements in Delivery',
    'author': 'Akretion',
    'website': 'https://github.com/akretion/odoo-usability',
    'depends': ['stock_delivery'],
    'data': [
        'views/stock_picking.xml',
    ],
    'installable': True,
}
