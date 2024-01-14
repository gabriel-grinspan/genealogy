from odoo import models, fields, api

class RelativeAddress(models.Model):
    _name = 'relative.address'
    _description = 'Address'
    _rec_name = 'street'

    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city_name_id = fields.Many2one('relative.city.name', string='City', ondelete='restrict', domain="[('country_id', '=?', country_id), ('state_id', '=?', state_id)]")
    state_id = fields.Many2one('res.country.state', string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    country_code = fields.Char(related='country_id.code', string='Country Code')
    latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    longitude = fields.Float(string='Geo Longitude', digits=(10, 7))
    phone = fields.Char()
    note = fields.Html()

    address_type = fields.Selection([
        ('home', 'Home Address'),
        ('birthplace', 'Birthplace'),
        ('marriage', 'Place of Marriage'),
        ('death', 'Place of Death'),
        ('burial_plot', 'Burial Plot'),
    ], default='home', string='Address Type')

    relative_ids = fields.Many2many('relative', string='Residents', compute='_compute_relative_ids')
    past_relative_ids = fields.Many2many('relative', string='Previous Residents', compute='_compute_relative_ids')
    current_relative_ids = fields.One2many('relative', 'current_address_id', string='Current Residents', readonly=True)

    head_of_household_id = fields.Many2one('relative', string='Head of Household', domain="[('id', 'in', current_relative_ids)]")
    head_of_household_id_image_128 = fields.Image(related='head_of_household_id.image_128')

    def _compute_relative_ids(self):
        for address in self:
            relative_ids = self.env['relative'].search([('address_ids', 'in', address.id)])
            address.relative_ids = relative_ids.ids
            address.past_relative_ids = (relative_ids - address.current_relative_ids).ids

    @api.onchange('city_name_id')
    def _onchange_city_names_id(self):
        if self.city_name_id.country_id:
            self.country_id = self.city_name_id.country_id
        
        if self.city_name_id.state_id:
            self.state_id = self.city_name_id.state_id
        
    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id
        
        if not self.state_id:
            return

        if self.city_name_id and not self.city_name_id.state_id:
            self.city_name_id.state_id = self.state_id
        elif self.city_name_id and self.city_name_id.state_id.id != self.state_id.id:
            self.city_name_id = False

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if not self.country_id:
            return

        if self.state_id and not self.state_id.country_id:
            self.state_id.country_id = self.country_id
        elif self.state_id and self.state_id.country_id.id != self.country_id.id:
            self.state_id = False

        if self.city_name_id and not self.city_name_id.country_id:
            self.city_name_id.country_id = self.country_id
        elif self.city_name_id and self.city_name_id.country_id.id != self.country_id.id:
            self.city_name_id = False
