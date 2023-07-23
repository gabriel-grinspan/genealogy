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
    lunisolar_date_of_birth = fields.Char(compute='_compute_lunisolar_date_of_birth', string='Hebrew Date of Birth', store=True)
    
    date_of_death = fields.Date('Date of Death')
    death_after_sunset = fields.Boolean()
    lunisolar_date_of_death = fields.Char(compute='_compute_lunisolar_date_of_death', string='Hebrew Date of Death', store=True)
    
    def _get_lunisolar_date(self, date, after_sunset):
        if not date:
            return False

        request_url = 'https://www.hebcal.com/converter?cfg=json&g2h=1&strict=1'
        request_url += date.strftime('%Y-%m-%d')
        if after_sunset:
            request_url += '&gs=on'

        response = requests.get(request_url).json()
        return response.get('hebrew')

    @api.depends('date_of_birth', 'birth_after_sunset')
    def _compute_lunisolar_date_of_birth(self):
        for partner in self:
            partner.lunisolar_date_of_birth = self._get_lunisolar_date(partner.date_of_birth, partner.birth_after_sunset)

    @api.depends('date_of_death', 'death_after_sunset')
    def _compute_lunisolar_date_of_death(self):
        for partner in self:
            partner.lunisolar_date_of_death = self._get_lunisolar_date(partner.date_of_death, partner.death_after_sunset)

    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    ], string='Sex', default='unknown', required=True)

    can_contact = fields.Boolean('Can contact', default=True)

    alias_ids = fields.One2many('res.partner.alias', 'partner_id', string='Aliases')
    name_orig_ids = fields.Many2many('res.partner', 'name_dest_id', 'name_orig_id', string='Named After')
    name_dest_ids = fields.Many2many('res.partner', 'name_orig_id', 'name_dest_id', string='Named Before')

    # TODO: fix relationships and test
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
    # END TODO

    residence_ids = fields.One2many('res.partner.residence', 'resident_id', string='Addresses')
    # TODO: use residence ids for mapping because each person can live in multiple places and ones living situation is independent of another's
    address_ids = fields.Many2many('res.partner', 'resident_id', 'address_id', string='Addresses')
    resident_ids = fields.One2many('res.partner', 'address_ids', string='Residents')
    living_with_ids = fields.Many2many('res.partner', string='Living With', compute='_compute_living_with_ids')
    
    @api.depends('address_ids', 'address_ids.resident_ids')
    def _compute_living_with_ids(self):
        for partner in self:
            partner.living_with_ids = (partner.address_ids.resident_ids - partner).ids

    head_of_household_id = fields.Many2one('res.partner', string='Head of Household')
    head_of_household_id_image_128 = fields.Image(related='head_of_household_id.image_128')

    @api.depends('head_of_household_id')
    def _verify_head_of_household_id(self):
        self.filtered(lambda p: p.head_of_household_id not in p.resident_ids).write({
            'head_of_household_id': False,
        })


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

