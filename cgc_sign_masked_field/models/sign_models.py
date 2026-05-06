# -*- coding: utf-8 -*-

from odoo import models


class SignTemplate(models.Model):
    _inherit = 'sign.template'

    def _get_available_field_types(self):
        """Extend available field types to include masked field."""
        res = super()._get_available_field_types()
        res.append(('masked', 'Masked Field'))
        return res


class SignRequestItem(models.Model):
    _inherit = 'sign.request.item'

    def _get_sign_values(self, sign_template_field):
        """Override to handle masked field type."""
        res = super()._get_sign_values(sign_template_field)
        if sign_template_field.field_type == 'masked':
            res['type'] = 'text'  # Store as text but render as password
        return res
