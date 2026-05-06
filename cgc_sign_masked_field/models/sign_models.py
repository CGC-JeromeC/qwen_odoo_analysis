# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SignTemplateField(models.Model):
    _inherit = 'sign.template.field'

    field_type = fields.Selection(selection_add=[
        ('masked', 'Masked Field'),
    ], string='Field Type')


class SignRequestItem(models.Model):
    _inherit = 'sign.request.item'

    def _get_sign_values(self, sign_template_field):
        """Override to handle masked field type."""
        res = super()._get_sign_values(sign_template_field)
        if sign_template_field.field_type == 'masked':
            res['type'] = 'text'  # Store as text but render as password
        return res
