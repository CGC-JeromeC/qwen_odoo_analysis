# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


MASKED_FIELD_TYPE = "masked"
MASKED_DISPLAY_VALUE = "••••••••"
SIGN_MANAGER_GROUP = "sign.group_sign_manager"


class SignMaskedFieldValue(models.Model):
    """Store raw values for masked Sign fields with explicit reveal rules.

    The value is intentionally not encrypted yet because that is outside the
    current scope. All reads meant for rendering should go through
    ``get_display_value``/``_get_display_value`` so callers can request the
    appropriate per-signee render mode instead of reading ``value`` directly.
    """

    _name = "sign.masked.field.value"
    _description = "Sign Masked Field Value"
    _order = "request_id, request_item_id, id"

    request_id = fields.Many2one(
        "sign.request",
        string="Signature Request",
        required=True,
        index=True,
        ondelete="cascade",
    )
    request_item_id = fields.Many2one(
        "sign.request.item",
        string="Owning Signer",
        index=True,
        ondelete="cascade",
        help="Signer who entered the masked value.",
    )
    template_field_ref = fields.Reference(
        selection=[
            ("sign.item", "Sign Item"),
            ("sign.template.field", "Sign Template Field"),
        ],
        string="Template Field",
        help="Optional reference to the template/sign item that produced this value.",
    )
    field_key = fields.Char(
        string="Field Key",
        index=True,
        help="Stable field identifier used by the Sign frontend/PDF renderer.",
    )
    value = fields.Char(
        string="Raw Value",
        groups=f"{SIGN_MANAGER_GROUP},base.group_system",
        help="Plain-text value; visible in ordinary ORM reads only to Sign/system admins.",
    )
    masked_value = fields.Char(
        string="Masked Value",
        compute="_compute_masked_value",
        help="Constant redaction marker; it intentionally does not preserve value length.",
    )

    @api.depends("value")
    def _compute_masked_value(self):
        for record in self:
            record.masked_value = MASKED_DISPLAY_VALUE if record.value else ""

    def _sign_manager_group_exists(self):
        return bool(self.env["ir.model.data"]._xmlid_to_res_id(SIGN_MANAGER_GROUP, raise_if_not_found=False))

    def _is_sign_manager(self):
        if self._sign_manager_group_exists():
            return self.env.user.has_group(SIGN_MANAGER_GROUP)
        return self.env.user.has_group("base.group_system")

    def _is_owned_by_request_item(self, request_item):
        self.ensure_one()
        return bool(request_item and self.request_item_id and self.request_item_id == request_item)

    def _can_view_unmasked_value(self, request_item=None):
        """Return whether the current user/request item may see the raw value."""
        self.ensure_one()
        return self._is_sign_manager() or self._is_owned_by_request_item(request_item)

    def _get_display_value(self, render_mode="masked", request_item=None):
        """Return the raw or masked value for a PDF/signing render mode.

        Supported modes:
        * ``masked``: always return solid dots.
        * ``unmasked_admin``: reveal only to Sign managers/admin fallback.
        * ``unmasked_current_signer``: reveal only to the owning signer or admin.
        """
        self.ensure_one()
        if not self.value:
            return ""
        if render_mode == "unmasked_admin" and self._is_sign_manager():
            return self.value
        if render_mode == "unmasked_current_signer" and self._can_view_unmasked_value(request_item):
            return self.value
        return self.masked_value

    def get_display_value(self, render_mode="masked", request_item=None):
        self.ensure_one()
        return self._get_display_value(render_mode=render_mode, request_item=request_item)

    def action_reveal_value(self):
        """Allow privileged form/API callers to reveal a value.

        Current signers intentionally do not get a post-signing reveal action
        for Option A; signer-level unmasking is only meant for the active
        signing/render flow that passes the owning request item explicitly.
        """
        self.ensure_one()
        if not self._is_sign_manager():
            raise AccessError(_("Only a Sign administrator can reveal this value after signing."))
        return self.value


class SignTemplate(models.Model):
    _inherit = "sign.template"

    def _get_available_field_types(self):
        """Extend available Sign field types with the masked type when supported."""
        res = list(super()._get_available_field_types())
        if MASKED_FIELD_TYPE not in dict(res):
            res.append((MASKED_FIELD_TYPE, _("Masked Field")))
        return res


class SignRequest(models.Model):
    _inherit = "sign.request"

    masked_field_value_ids = fields.One2many(
        "sign.masked.field.value",
        "request_id",
        string="Masked Field Values",
        copy=False,
    )

    def _get_masked_field_render_mode(self, request_item=None, force_admin=False):
        """Select the render mode for masked fields.

        The default completed/shared PDF should call this without a signer and
        gets ``masked``. Sign admins can force ``unmasked_admin``. A signing or
        review flow for a specific signer should pass that request item and gets
        ``unmasked_current_signer``.
        """
        self.ensure_one()
        value_model = self.env["sign.masked.field.value"]
        if force_admin and value_model._is_sign_manager():
            return "unmasked_admin"
        if request_item:
            return "unmasked_current_signer"
        return "masked"

    def _get_masked_field_pdf_values(self, render_mode="masked", request_item=None):
        """Return field-key/value pairs for a PDF renderer.

        Odoo Sign PDF hooks differ between versions/customizations, so this
        method is deliberately small and reusable: call it from the concrete PDF
        generation hook and merge the returned values into the values painted on
        the PDF.
        """
        self.ensure_one()
        return {
            value.field_key: value.get_display_value(render_mode=render_mode, request_item=request_item)
            for value in self.masked_field_value_ids
            if value.field_key
        }

    def _get_masked_pdf_values(self):
        self.ensure_one()
        return self._get_masked_field_pdf_values(render_mode="masked")

    def _get_unmasked_admin_pdf_values(self):
        self.ensure_one()
        return self._get_masked_field_pdf_values(render_mode="unmasked_admin")

    def _get_unmasked_current_signer_pdf_values(self, request_item):
        self.ensure_one()
        return self._get_masked_field_pdf_values(
            render_mode="unmasked_current_signer",
            request_item=request_item,
        )


class SignRequestItem(models.Model):
    _inherit = "sign.request.item"

    masked_field_value_ids = fields.One2many(
        "sign.masked.field.value",
        "request_item_id",
        string="Masked Field Values",
        copy=False,
    )

    def _get_sign_request(self):
        self.ensure_one()
        for field_name in ("sign_request_id", "request_id"):
            if field_name in self._fields and self[field_name]:
                return self[field_name]
        return self.env["sign.request"]

    def upsert_masked_field_value(self, field_key, value, template_field_ref=False):
        """Create/update the protected raw value for a masked Sign field.

        This helper is intended to be called by the concrete Odoo Sign
        submission hook after a signer submits field values. It stores exactly
        one raw value per signer/request/field key and leaves PDF rendering to
        the per-signee render-mode helpers on ``sign.request``.
        """
        self.ensure_one()
        request = self._get_sign_request()
        domain = [
            ("request_id", "=", request.id),
            ("request_item_id", "=", self.id),
            ("field_key", "=", field_key),
        ]
        value_model = self.env["sign.masked.field.value"].sudo()
        masked_value = value_model.search(domain, limit=1)
        vals = {
            "request_id": request.id,
            "request_item_id": self.id,
            "field_key": field_key,
            "value": value,
        }
        if template_field_ref:
            vals["template_field_ref"] = template_field_ref
        if masked_value:
            masked_value.write(vals)
        else:
            masked_value = value_model.create(vals)
        return masked_value

    def _get_sign_values(self, sign_template_field):
        """Handle masked fields as text for Sign value collection.

        The raw value should be mirrored into ``sign.masked.field.value`` by the
        concrete Odoo Sign submission hook so that PDFs and later reads can use
        per-signee render modes.
        """
        res = super()._get_sign_values(sign_template_field)
        field_type = getattr(sign_template_field, "field_type", False) or getattr(sign_template_field, "type", False)
        if field_type == MASKED_FIELD_TYPE:
            res["type"] = "text"
            res["masked"] = True
        return res

    def _can_view_masked_field_value(self, masked_value):
        self.ensure_one()
        return masked_value._can_view_unmasked_value(request_item=self)
