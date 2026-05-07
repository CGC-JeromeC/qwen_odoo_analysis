{
    "name": "CGC Sign Masked Field",
    "version": "19.0.1.0.0",
    "category": "Sign",
    "summary": "Add masked field functionality to Odoo Sign for sensitive data input",
    "description": """
        CGC Sign Masked Field
        =====================
        
        This module extends the Odoo Sign application by adding support for masked fields.
        Masked fields are useful when collecting sensitive information such as passwords,
        PIN codes, or other confidential data that should not be visible on screen while typing.
        
        Features:
        ---------
        * Adds a new field type 'Masked Field' to Odoo Sign requests
        * Hides input characters with solid dots while the signer types
        * Provides backend helpers for per-signee/admin render modes
        * Supports masked, admin-unmasked, and current-signer-unmasked PDF values
        
        Usage:
        ------
        1. Create or edit a Sign request template
        2. Add a new field and select 'Masked Field' as the field type
        3. Recipients will see masked input when filling out the field
        4. Render the default PDF with masked values and privileged copies with
           per-signee/admin unmasked values
        
        Company: Core Group Company LLC
    """,
    "author": "Core Group Company LLC",
    "website": "https://www.coregroupcompany.com",
    "license": "LGPL-3",
    "depends": ["sign"],
    "data": [
        "security/ir.model.access.csv",
        "data/sign_item_type_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "assets": {
        "web.assets_backend": [
            "cgc_sign_masked_field/static/src/js/sign_masked_field.esm.js",
            "cgc_sign_masked_field/static/src/xml/sign_masked_field.xml",
            "cgc_sign_masked_field/static/src/css/sign_masked_field.css",
        ],
        "web.assets_frontend": [
            "cgc_sign_masked_field/static/src/js/sign_masked_field.esm.js",
            "cgc_sign_masked_field/static/src/xml/sign_masked_field.xml",
            "cgc_sign_masked_field/static/src/css/sign_masked_field.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
