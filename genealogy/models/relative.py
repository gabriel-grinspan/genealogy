from odoo import models, fields, api
import requests
from datetime import datetime


class Relative(models.Model):
    _name = 'relative'
    _inherit = ['avatar.mixin', 'mail.activity.mixin', 'mail.thread.blacklist']
    _description = 'Relative'
    _order = 'date_of_birth, last_name, first_name, id'

    title_id = fields.Many2one('res.partner.title', string='Title')
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    name = fields.Char('Name', compute='_compute_name', store=True)
    alias_ids = fields.One2many('relative.alias', 'relative_id', string='Aliases')

    name_orig_ids = fields.Many2many('relative', 'name_dest_id', 'name_orig_id', string='Named After')
    name_dest_ids = fields.Many2many('relative', 'name_orig_id', 'name_dest_id', string='Named Before')
    # TODO: make computed
    name_orig_description = fields.Char('Named After Description')

    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Sex')

    date_of_birth = fields.Date('Date of Birth')
    date_of_birth_approximate = fields.Boolean('Approximate Date of Birth')
    birth_after_sunset = fields.Boolean()
    lunisolar_date_of_birth = fields.Char(compute='_compute_lunisolar_date_of_birth', string='Hebrew Date of Birth')
    
    date_of_death = fields.Date('Date of Death')
    death_after_sunset = fields.Boolean()
    lunisolar_date_of_death = fields.Char(compute='_compute_lunisolar_date_of_death', string='Hebrew Date of Death')
    date_of_death_approximate = fields.Boolean('Approximate Date of Death')

    home_phone = fields.Char('Home Phone')
    mobile_phone = fields.Char('Mobile Phone')
    phone = fields.Char(compute='_compute_phone', string='Phone')
    email = fields.Char('Email')

    street = fields.Char(related='current_address_id.street', readonly=True)
    street2 = fields.Char(related='current_address_id.street2', readonly=True)
    zip = fields.Char(related='current_address_id.zip', readonly=True)
    city_name_id = fields.Many2one(related='current_address_id.city_name_id', readonly=True)
    state_id = fields.Many2one(related='current_address_id.state_id', readonly=True)
    country_id = fields.Many2one(related='current_address_id.country_id', readonly=True)
    country_code = fields.Char(related='current_address_id.country_code', readonly=True)

    address_ids = fields.Many2many('relative.address', string='Addresses')
    current_address_id = fields.Many2one('relative.address', string='Current Address')

    family_id = fields.Many2one('relative.family', string='Family')
    family_number = fields.Integer('Family ID', readonly=True)
    father_id = fields.Many2one('relative', string='Father')
    mother_id = fields.Many2one('relative', string='Mother')

    sibling_sequence = fields.Integer('nth Sibling', compute='_compute_sibling_sequence')
    sibling_ids = fields.Many2many('relative', string='Siblings', compute='_compute_sibling_ids', readonly=True)
    half_sibling_ids = fields.Many2many('relative', string='Half Siblings', compute='_compute_sibling_ids', readonly=True)

    children_ids = fields.Many2many('relative', string='Children', compute='_compute_children_ids', readonly=True)

    spouse_type = fields.Selection([
        ('male', 'Husband'),
        ('female', 'Wife'),
        ('mixed', 'Mixed'),
    ], compute='_compute_spouse_type')
    
    relationship_ids = fields.Many2many(
        'relative.relationship',
        string='Relationships',
        compute='_compute_relationship_ids',
        inverse='_set_relationship_ids',
    )
    spouse_ids = fields.Many2many('relative', string='Current Relationship(s)', compute='_compute_spouse_ids')

    # Can be used for 'Can contact'
    category_ids = fields.Many2many('res.partner.category', string='Tags')
    note = fields.Html('Note')


    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        for relative in self:
            relative.name = f'{relative.title_id.shortcut or ""} {relative.first_name or ""} {relative.last_name or ""}'.strip()

    # @api.depends('name_orig_ids')
    # def _compute_name_dest_ids(self):
    #     for relative in self:
    #         relative.name_dest_ids = self.search([('name_orig_ids', 'in', relative.id)])

    def _get_lunisolar_date(self, date, after_sunset):
        if not date:
            return False

        request_url = f'https://www.hebcal.com/converter?cfg=json&g2h=1&strict=1&date={date.strftime("%Y-%m-%d")}'
        if after_sunset:
            request_url += '&gs=on'

        response = requests.get(request_url).json()
        return response.get('hebrew')

    @api.depends('date_of_birth', 'birth_after_sunset', 'date_of_birth_approximate')
    def _compute_lunisolar_date_of_birth(self):
        for relative in self:
            relative.lunisolar_date_of_birth = not relative.date_of_birth_approximate and self._get_lunisolar_date(relative.date_of_birth, relative.birth_after_sunset)

    @api.depends('date_of_death', 'death_after_sunset', 'date_of_death_approximate')
    def _compute_lunisolar_date_of_death(self):
        for relative in self:
            relative.lunisolar_date_of_death = not relative.date_of_death_approximate and self._get_lunisolar_date(relative.date_of_death, relative.death_after_sunset)
    
    @api.depends('home_phone', 'mobile_phone')
    def _compute_phone(self):
        for relative in self:
            relative.phone = relative.mobile_phone or relative.home_phone

    @api.depends('sibling_ids', 'date_of_birth')
    def _compute_sibling_sequence(self):
        for relative in self:
            children = (relative.sibling_ids | relative).sorted(lambda r: (
                r.date_of_birth and str(r.date_of_birth) or '',
            ))
            # Need this for creating new records, otherwise need to use _origin
            if len(children) == 1:
                relative.sibling_sequence = 1
                continue

            for i, child in enumerate(children):
                if child.id == relative.id:
                    relative.sibling_sequence = i + 1
                    break

    @api.depends('father_id', 'mother_id')
    def _compute_sibling_ids(self):
        for relative in self:
            # relative._origin
            if not relative.father_id and not relative.mother_id:
                relative.sibling_ids = False
                relative.half_sibling_ids = False
                continue

            elif not relative.father_id and relative.mother_id:
                domain = [
                    ('mother_id', '=', relative.mother_id.id),
                    ('id', '!=', relative._origin.id),
                ]
            elif relative.father_id and not relative.mother_id:
                domain = [
                    ('father_id', '=', relative.father_id.id),
                    ('id', '!=', relative._origin.id),
                ]
            else:
                domain = [
                    '|',
                        ('father_id', '=', relative.father_id.id),
                        ('mother_id', '=', relative.mother_id.id),
                    ('id', '!=', relative._origin.id),
                ]

            siblings = relative.search(domain)

            if len(domain) == 4:
                full_siblings = siblings.filtered(lambda r: r.father_id.id == relative.father_id.id and r.mother_id.id == relative.mother_id.id)
                full_siblings = full_siblings.sorted(lambda r: (
                    r.date_of_birth and str(r.date_of_birth) or '',
                ))
            else:
                full_siblings = relative.browse()
            half_siblings = siblings - full_siblings

            relative.sibling_ids = full_siblings.ids
            relative.half_sibling_ids = half_siblings.ids

    def _compute_children_ids(self):
        for relative in self:
            relative.children_ids = self.search([
                '|',
                    ('father_id', '=', relative.id),
                    ('mother_id', '=', relative.id),
            ], order='date_of_birth').ids

    def _compute_spouse_type(self):
        for relative in self:
            spouse_type = False

            if relative in relative.relationship_ids.male_id:
                spouse_type = 'male'
            if relative in relative.relationship_ids.female_id:
                if spouse_type == 'male':
                    spouse_type = 'mixed'
                else:
                    spouse_type = 'female'

            relative.spouse_type = spouse_type

    def _compute_relationship_ids(self):
        for relative in self:
            relative.relationship_ids = self.env['relative.relationship'].search([
                '|',
                ('male_id', '=', relative.id),
                ('female_id', '=', relative.id),
            ], order='start_date').ids

    def _set_relationship_ids(self):
        for relative in self:
            old_relationship_ids = self.env['relative.relationship'].search([
                '|',
                    ('male_id', '=', relative.id),
                    ('female_id', '=', relative.id),
            ], order='start_date')

            (old_relationship_ids - relative.relationship_ids).unlink()

    def _compute_spouse_ids(self):
        for relative in self:
            relationships = self.env['relative.relationship'].search([
                '|',
                    ('male_id', '=', relative.id),
                    ('female_id', '=', relative.id),
                ('end_date', '=', False),
                ('status', 'not in', [
                    'divorced',
                    'deceased',
                    'children',
                ]),
            ])
            relative.spouse_ids = ((relationships.mapped('male_id') | relationships.mapped('female_id')) - relative).ids

    def action_create_relationship_wizard(self):
        self.ensure_one()
        return {
            'name': 'Create Relationship',
            'type': 'ir.actions.act_window',
            'res_model': 'relative.relationship.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
