from odoo import models, fields, api
import requests


class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_of_birth = fields.Date('Date of Birth')
    birth_after_sunset = fields.Boolean()
    lunisolar_date_of_birth = fields.Char(compute='_compute_lunisolar_date_of_birth', string='Hebrew Date of Birth')
    
    date_of_death = fields.Date('Date of Death')
    death_after_sunset = fields.Boolean()
    lunisolar_date_of_death = fields.Char(compute='_compute_lunisolar_date_of_death', string='Hebrew Date of Death')
    
    def _get_lunisolar_date(self, date, after_sunset):
        if not date:
            return False

        request_url = f'https://www.hebcal.com/converter?cfg=json&g2h=1&strict=1&date={date.strftime("%Y-%m-%d")}'
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
    ], string='Sex')

    can_contact = fields.Boolean('Can contact', default=True)

    alias_ids = fields.One2many('res.partner.alias', 'partner_id', string='Aliases')
    name_orig_ids = fields.Many2many('res.partner', 'name_dest_id', 'name_orig_id', string='Named After')
    name_dest_ids = fields.Many2many('res.partner', 'name_orig_id', 'name_dest_id', string='Named Before', compute='_compute_name_dest_ids')

    @api.depends('name_orig_ids')
    def _compute_name_dest_ids(self):
        for partner in self:
            partner.name_dest_ids = self.search([('name_orig_ids', 'in', partner.id)])

    street = fields.Char(related='current_address_id.street', readonly=True)
    street2 = fields.Char(related='current_address_id.street2', readonly=True)
    zip = fields.Char(related='current_address_id.zip', readonly=True)
    city = fields.Char(related='current_address_id.city', readonly=True)
    state_id = fields.Many2one(related='current_address_id.state_id', readonly=True)
    country_id = fields.Many2one(related='current_address_id.country_id', readonly=True)
    country_code = fields.Char(related='current_address_id.country_code', readonly=True)

    address_ids = fields.Many2many('res.partner.address', string='Addresses')
    current_address_id = fields.Many2one('res.partner.address', string='Current Address')

    father_id = fields.Many2one('res.partner', string='Father')
    mother_id = fields.Many2one('res.partner', string='Mother')
    children_ids = fields.Many2many('res.partner', string='Children', compute='_compute_children_ids', readonly=True)
    
    def _compute_children_ids(self):
        for partner in self:
            partner.children_ids = self.search([
                '|',
                    ('father_id', '=', partner.id),
                    ('mother_id', '=', partner.id),
            ], order='date_of_birth').ids
    
    spouse_type = fields.Selection([
        ('male', 'Husband'),
        ('female', 'Wife'),
        ('mixed', 'Mixed'),
    ], compute='_compute_spouse_type')

    def _compute_spouse_type(self):
        for partner in self:
            spouse_type = False

            if partner in partner.relationship_ids.male_id:
                spouse_type = 'male'
            if partner in partner.relationship_ids.female_id:
                if spouse_type == 'male':
                    spouse_type = 'mixed'
                else:
                    spouse_type = 'female'

            partner.spouse_type = spouse_type

    relationship_ids = fields.Many2many(
        'res.partner.relationship',
        string='Relationships',
        compute='_compute_relationship_ids',
        inverse='_set_relationship_ids',
    )

    def _compute_relationship_ids(self):
        for partner in self:
            partner.relationship_ids = self.env['res.partner.relationship'].search([
                '|',
                ('male_id', '=', partner.id),
                ('female_id', '=', partner.id),
            ], order='start_date').ids

    def _set_relationship_ids(self):
        for partner in self:
            old_relationship_ids = self.env['res.partner.relationship'].search([
                '|',
                ('male_id', '=', partner.id),
                ('female_id', '=', partner.id),
            ], order='start_date')

            (old_relationship_ids - partner.relationship_ids).unlink()

    spouse_ids = fields.Many2many('res.partner', string='Current Relationship(s)', compute='_compute_spouse_ids')

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
                    'children',
                ]),
            ])
            partner.spouse_ids = ((relationships.mapped('male_id') | relationships.mapped('female_id')) - partner).ids

    def action_create_relationship_wizard(self):
        self.ensure_one()
        return {
            'name': 'Create Relationship',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.relationship.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
