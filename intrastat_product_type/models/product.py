# Copyright 2016-2024 Akretion France (https://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# @author Alexis de Lattre <alexis.delattre@akretion.com>

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # The field itself (stored, computed from 'type', precomputed) is
    # defined by intrastat_base. This module only makes it editable
    # (and required, as it was in 14.0), so that a consumable product can
    # be declared as a service for the intrastat declarations.
    intrastat_type = fields.Selection(
        readonly=False,
        required=True,
        help="Type of product used for the intrastat declarations. "
        "It allows you to configure a service product as 'Goods' "
        "to have it in pickings but configure it with "
        "Intrastat Type = 'Service' to consider it as a "
        "service for intrastat declarations.",
    )

    @api.constrains('type', 'is_storable', 'intrastat_type')
    def _check_intrastat_type(self):
        for pt in self:
            if pt.type == 'service' and pt.intrastat_type != 'service':
                raise ValidationError(_(
                    "On the service product '%s', Intrastat Type must be "
                    "'Service'.", pt.display_name))
            if (
                    pt.type == 'consu'
                    and pt.is_storable
                    and pt.intrastat_type != 'product'):
                raise ValidationError(_(
                    "On the storable product '%s', Intrastat Type must be "
                    "'Product'.", pt.display_name))
