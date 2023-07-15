from odoo import models, fields, api
from odoo.osv import expression

import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_of_birth = fields.Date('Date of Birth')
    date_of_death = fields.Date('Date of Death')
    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    ], string='Sex', default='unknown')
    alias_ids = fields.Many2many('res.partner.alias', string='Aliases')
    father_id = fields.Many2one('res.partner', string='Father')
    mother_id = fields.Many2one('res.partner', string='Mother')
    children_ids = fields.Many2many('res.partner', string='Children', compute='_compute_children_ids', readonly=True)
    relationship_ids = fields.Many2many('res.partner.relationship', string='Partnerships')
    spouse_ids = fields.Many2many('res.partner', string='Current Spouse(s)', compute='_compute_spouse_ids')


    def _compute_children_ids(self):
        for partner in self:
            partner.children_ids = self.search([
                '|',
                ('father_id', '=', partner.id),
                ('mother_id', '=', partner.id),
            ]).ids

    # @api.onchange('relationship_ids')
    # def _onchange_relationship_ids(self):
    #     self.relationship_ids
            

    # def _compute_relationship_ids(self):
    #     for partner in self:
    #         partner.relationship_ids = self.env['res.partner.relationship'].search([
    #             '|',
    #             ('male_id', '=', partner.id),
    #             ('female_id', '=', partner.id),
    #         ]).ids

    def _compute_spouse_ids(self):
        for partner in self:
            relationships = self.env['res.partner.relationship'].search([
                '|',
                ('male_id', '=', partner.id),
                ('female_id', '=', partner.id),
                ('end_date', '=', False),
            ])
            partner.spouse_ids = ((relationships.mapped('male_id') | relationships.mapped('female_id')) - partner).ids
