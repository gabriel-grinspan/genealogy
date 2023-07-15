from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)

class ResPartnerRelationship(models.Model):
    _name = 'res.partner.relationship'

    male_id = fields.Many2one('res.partner', string='Husband')
    female_id = fields.Many2one('res.partner', string='Wife')
    status = fields.Selection(string='Relationship Status', selection=[
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('deceased', 'Deceased Partner'),
        ('live_together', 'Living Together'),
        ('boyfriend_girlfriend', 'Boyfriend/Girlfriend'),
        ('children', 'Have Children Together'),
    ])
    start_date = fields.Date('Start')
    end_date = fields.Date('End')

    def default_get(self, fields):
        res = super(ResPartnerRelationship, self).default_get(fields)
        params = self._context.get('params')
        if params and params.get('model') == 'res.partner':
            partner_id = params.get('id')
            sex = self.env['res.partner'].browse(partner_id).sex
            if sex in ['male', 'other', 'unknown']:
                res.update({'husband_id': partner_id})
            elif sex == 'female':
                res.update({'wife_id': partner_id})
        return res
