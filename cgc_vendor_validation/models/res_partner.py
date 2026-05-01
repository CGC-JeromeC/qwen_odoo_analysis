# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    validation_document_ids = fields.One2many(
        'vendor.validation.document', 'partner_id', string='Validation Documents'
    )
    validation_progress = fields.Float(
        string='Validation Progress (%)', compute='_compute_validation_progress', store=True
    )
    validation_status = fields.Selection([
        ('not_valid', 'Not Valid'),
        ('in_progress', 'In-Progress'),
        ('validated', 'Validated'),
    ], string='Validation Status', compute='_compute_validation_status',
       search='_search_validation_status', store=False, compute_sudo=True)

    @api.depends('validation_progress')
    def _compute_validation_status(self):
        for partner in self:
            if partner.validation_progress >= 100.0:
                partner.validation_status = 'validated'
            elif partner.validation_progress > 0:
                partner.validation_status = 'in_progress'
            else:
                partner.validation_status = 'not_valid'

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        if self.env.context.get('only_validated_vendors'):
            # Force recompute validation_status for all partners in the search
            self.flush_recordset()
            validated_ids = self.search([('validation_status', '=', 'validated')]).ids
            domain = expression.AND([domain or [], [('id', 'in', validated_ids)]])
        return super()._name_search(name=name, domain=domain, operator=operator, limit=limit, order=order)

    def _search_validation_status(self, operator, value):
        # Flush pending writes to ensure up-to-date data
        self.flush_recordset()
        
        total_reqs = self.env['vendor.requirement.type'].search_count([('active', '=', True)])

        if total_reqs == 0:
            # If no requirements exist, everyone is 'validated'
            if operator == '=' and value == 'validated':
                return []  # match all
            return [('id', '=', -1)]  # match none

        # Get all partners with at least one upload
        self.env.cr.execute("""
            SELECT partner_id, count(DISTINCT requirement_type_id) as uploaded_count
            FROM vendor_validation_document
            WHERE status = 'uploaded'
            GROUP BY partner_id
        """)
        rows = self.env.cr.fetchall()
        uploaded_map = {r[0]: r[1] for r in rows}

        validated_ids = [pid for pid, cnt in uploaded_map.items() if cnt >= total_reqs]
        in_progress_ids = [pid for pid, cnt in uploaded_map.items() if 0 < cnt < total_reqs]
        not_valid_ids = [pid for pid, cnt in uploaded_map.items() if cnt == 0]

        def match(val):
            if val == 'validated':
                return [('id', 'in', validated_ids)] if validated_ids else [('id', '=', -1)]
            elif val == 'in_progress':
                return [('id', 'in', in_progress_ids)] if in_progress_ids else [('id', '=', -1)]
            else:  # not_valid — partners with zero uploads or no documents at all
                # Need to include partners that have no validation_document records at all
                all_partners_with_docs = list(uploaded_map.keys())
                # Partners with docs but 0 uploaded + partners with no docs at all
                return [('id', 'not in', all_partners_with_docs + validated_ids + in_progress_ids)]
        
        if operator == '=':
            return match(value)
        elif operator == '!=':
            # negate: return partners NOT in the matched set
            matched_domain = match(value)
            if matched_domain == []:
                return [('id', '=', -1)]
            if matched_domain == [('id', '=', -1)]:
                return []
            # swap in/not in
            domain_item = matched_domain[0]
            if domain_item[1] == 'in':
                return [('id', 'not in', domain_item[2])]
            elif domain_item[1] == 'not in':
                return [('id', 'in', domain_item[2])]
            return matched_domain
        elif operator == 'in' and isinstance(value, (list, tuple)):
            from odoo.osv import expression
            domains = [match(v) for v in value]
            return expression.OR(domains)
        elif operator == 'not in' and isinstance(value, (list, tuple)):
            from odoo.osv import expression
            domains = [match(v) for v in value]
            # Get all IDs that match any of the values, then exclude them
            combined = expression.OR(domains)
            # This is complex; simpler to just return the negation
            if not domains:
                return []
            # For simplicity, handle common cases
            all_matched_ids = set()
            for d in domains:
                if d and d[0][1] == 'in':
                    all_matched_ids.update(d[0][2])
            if all_matched_ids:
                return [('id', 'not in', list(all_matched_ids))]
            return []
        return []

    # A non-stored field purely used to trigger side-effects when the form view loads
    trigger_auto_load_requirements = fields.Boolean(
        compute='_compute_auto_load_requirements', store=False, compute_sudo=True
    )

    @api.depends('name')
    def _compute_auto_load_requirements(self):
        for partner in self:
            partner.trigger_auto_load_requirements = True
            if isinstance(partner.id, int):
                active_reqs = self.env['vendor.requirement.type'].search([('active', '=', True)])
                existing_req_ids = partner.validation_document_ids.mapped('requirement_type_id.id')
                missing_reqs = active_reqs.filtered(lambda r: r.id not in existing_req_ids)
                if missing_reqs:
                    self.env['vendor.validation.document'].sudo().create([
                        {
                            'partner_id': partner.id,
                            'requirement_type_id': req.id,
                            'status': 'missing'
                        } for req in missing_reqs
                    ])

    @api.depends('validation_document_ids', 'validation_document_ids.status', 'validation_document_ids.requirement_type_id')
    def _compute_validation_progress(self):
        total_requirements_count = self.env['vendor.requirement.type'].search_count([('active', '=', True)])

        for partner in self:
            if total_requirements_count == 0:
                partner.validation_progress = 100.0
                continue

            valid_docs = partner.validation_document_ids.filtered(lambda d: d.status == 'uploaded')
            unique_reqs = valid_docs.mapped('requirement_type_id')
            active_unique_reqs = unique_reqs.filtered(lambda r: r.active)

            progress = (len(active_unique_reqs) / float(total_requirements_count)) * 100.0
            partner.validation_progress = progress
