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
        * Hides input characters with asterisks or dots while maintaining data integrity
        * Compatible with existing Odoo Sign workflows
        * Secure handling of masked data
        
        Usage:
        ------
        1. Create or edit a Sign request template
        2. Add a new field and select 'Masked Field' as the field type
        3. Recipients will see masked input when filling out the field
        
        Company: Core Group Company LLC
    """,
    "author": "Core Group Company LLC",
    "website": "https://www.coregroupcompany.com",
    "license": "LGPL-3",
    "depends": ["sign"],
    "data": [
        "views/sign_templates_views.xml",
        "views/sign_request_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cgc_sign_masked_field/static/src/js/sign_masked_field.esm.js",
            "cgc_sign_masked_field/static/src/css/sign_masked_field.css",
        ],
        "web.assets_frontend": [
            "cgc_sign_masked_field/static/src/js/sign_masked_field.esm.js",
            "cgc_sign_masked_field/static/src/css/sign_masked_field.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
