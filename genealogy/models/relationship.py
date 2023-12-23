from odoo import models, fields, api

RELATIONSHIP_STATUSES = [
    ('married', 'Married'),
    ('divorced', 'Divorced'),
    ('deceased', 'Deceased Partner'),
    ('live_together', 'Living Together'),
    ('dating', 'Dating'),
    ('children', 'Have Children Together'),
]

class RelativeRelationship(models.Model):
    _name = 'relative.relationship'
    _description = 'Relationship'

    male_id = fields.Many2one('relative', string='Husband')
    female_id = fields.Many2one('relative', string='Wife')
    status = fields.Selection(RELATIONSHIP_STATUSES, string='Relationship Status')
    start_date = fields.Date('Start')
    end_date = fields.Date('End')
