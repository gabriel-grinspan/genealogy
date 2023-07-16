from odoo import models, fields, api
from odoo.osv import expression

import requests
# import datetime
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_of_birth = fields.Date('Date of Birth')
    birth_after_sunset = fields.Boolean()
    lunisolar_date_of_birth = fields.Char('Hebrew Date of Birth', readonly=True)
    date_of_death = fields.Date('Date of Death')
    death_after_sunset = fields.Boolean()
    lunisolar_date_of_death = fields.Char('Hebrew Date of Death', readonly=True)
    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    ], string='Sex', default='unknown', required=True)
    alias_ids = fields.One2many('res.partner.alias', 'partner_id', string='Aliases')

    type = fields.Selection(selection_add=[
        ('birthplace', 'Birthplace'),
        ('previous_address', 'Previous Address'),
        ('current_address', 'Current Address'),
    ])

    father_id = fields.Many2one('res.partner', string='Father')
    mother_id = fields.Many2one('res.partner', string='Mother')
    children_ids = fields.Many2many('res.partner', string='Children', compute='_compute_children_ids', readonly=True)
    relationship_ids = fields.Many2many(
        'res.partner.relationship',
        string='Partnerships',
        # compute='_compute_relationship_ids',
        # inverse='_set_relationship_ids',
    )
    spouse_ids = fields.Many2many('res.partner', string='Current Relationship(s)', compute='_compute_spouse_ids')
    address_ids = fields.Many2many('res.partner', string='Addresses')
    resident_ids = fields.Many2many('res.partner', string='Residents', compute='_compute_resident_ids')
    head_of_household = fields.Boolean('Head of Household')
    living_with = fields.Many2many('res.partner', string='Lives With', compute='_compute_living_with')

    def _get_lunisolar_date(self, date, after_sunset):
        if not date:
            return False

        request_url = 'https://www.hebcal.com/converter?cfg=json&g2h=1&strict=1'
        request_url += date.strftime('%Y-%m-%d')
        if after_sunset:
            request_url += '&gs=on'

        response = requests.get(request_url).json()
        return response.get('hebrew')

    @api.onchange('date_of_birth', 'birth_after_sunset')
    def _onchange_date_of_birth(self):
        for partner in self:
            partner.lunisolar_date_of_birth = self._get_lunisolar_date(partner.date_of_birth, partner.birth_after_sunset)

    @api.onchange('date_of_death', 'death_after_sunset')
    def _onchange_date_of_death(self):
        for partner in self:
            partner.lunisolar_date_of_death = self._get_lunisolar_date(partner.date_of_death, partner.death_after_sunset)

    def _compute_children_ids(self):
        for partner in self:
            partner.children_ids = self.search([
                '|',
                ('father_id', '=', partner.id),
                ('mother_id', '=', partner.id),
            ]).ids

    def _compute_relationship_ids(self):
        for partner in self:
            partner.relationship_ids = self.env['res.partner.relationship'].search([
                '|',
                ('male_id', '=', partner.id),
                ('female_id', '=', partner.id),
            ]).ids

    # def _set_relationship_ids(self):
    #     pass

    def _compute_spouse_ids(self):
        for partner in self:
            relationships = self.env['res.partner.relationship'].search([
                '|',
                ('male_id', '=', partner.id),
                ('female_id', '=', partner.id),
                ('end_date', '=', False),
                ('status', 'not in', [
                    'divorced',
                    'deceased',
                ]),
            ])
            partner.spouse_ids = ((relationships.mapped('male_id') | relationships.mapped('female_id')) - partner).ids

    def _compute_resident_ids(self):
        for partner in self:
            partner.resident_ids = partner.search([('address_ids', 'child_of', partner.id)]).ids

    def _compute_living_with(self):
        for partner in self:
            living_with = self.search([
                ('id', 'child_of', partner.resident_ids.ids)
            ])
            partner.living_with = (living_with - partner).ids
