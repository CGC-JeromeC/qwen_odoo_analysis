# -*- coding: utf-8 -*-

from odoo import _, SUPERUSER_ID, api


MASKED_FIELD_TYPE_XMLID = "cgc_sign_masked_field.sign_item_type_masked"
MASKED_FIELD_TYPE_NAME = "Masked Field"


def _env_from_hook_args(*args):
    """Return an Environment for both modern and legacy hook signatures."""
    if len(args) == 1 and hasattr(args[0], "registry"):
        return args[0]
    cr = args[0]
    return api.Environment(cr, SUPERUSER_ID, {})


def _selection_contains(field, value):
    selection = field.selection
    if callable(selection):
        return True
    return value in dict(selection or [])


def _prepare_masked_item_type_values(item_type_model):
    """Build values using only fields that exist on this Odoo Sign version.

    Odoo Sign's signature field-type model is record based. The exact field
    names have moved across versions/custom builds, so keep this provisioning
    defensive instead of relying on one brittle XML data shape.
    """
    fields = item_type_model._fields
    vals = {}

    if "name" in fields:
        vals["name"] = MASKED_FIELD_TYPE_NAME
    if "item_type" in fields and _selection_contains(fields["item_type"], "text"):
        vals["item_type"] = "text"
    elif "type" in fields and _selection_contains(fields["type"], "text"):
        vals["type"] = "text"
    if "is_masked_field" in fields:
        vals["is_masked_field"] = True
    if "tip" in fields:
        vals["tip"] = _("Enter the sensitive value.")
    if "placeholder" in fields:
        vals["placeholder"] = _("Enter masked value")
    if "default_width" in fields:
        vals["default_width"] = 0.150
    if "default_height" in fields:
        vals["default_height"] = 0.015
    if "auto_field" in fields:
        vals["auto_field"] = False

    return vals


def _ensure_masked_item_type(env):
    """Create/update the actual Sign field-type record used by the dropdown."""
    if "sign.item.type" not in env.registry.models:
        return False

    item_type_model = env["sign.item.type"].sudo()
    xmlid_model = env["ir.model.data"].sudo()
    existing_id = xmlid_model._xmlid_to_res_id(MASKED_FIELD_TYPE_XMLID, raise_if_not_found=False)
    vals = _prepare_masked_item_type_values(item_type_model)
    if not vals:
        return False

    item_type = item_type_model.browse(existing_id).exists() if existing_id else item_type_model
    if not item_type:
        domain = [("name", "=", MASKED_FIELD_TYPE_NAME)] if "name" in item_type_model._fields else []
        item_type = item_type_model.search(domain, limit=1) if domain else item_type_model

    if item_type:
        item_type.write(vals)
    else:
        item_type = item_type_model.create(vals)

    if item_type and not existing_id:
        xmlid_model.create({
            "module": "cgc_sign_masked_field",
            "name": "sign_item_type_masked",
            "model": "sign.item.type",
            "res_id": item_type.id,
            "noupdate": True,
        })
    return item_type


def post_init_hook(*args):
    env = _env_from_hook_args(*args)
    _ensure_masked_item_type(env)
