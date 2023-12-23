from odoo import models, fields, api

class RelativeAddress(models.Model):
    _name = 'relative.address'
    _description = 'Address'
    _rec_name = 'street'

    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
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
        ('death', 'Place of Death'),
        ('burial_plot', 'Burial Plot'),
    ], string='Address Type')

    relative_ids = fields.Many2many('relative', string='Residents', compute='_compute_relative_ids')
    past_relative_ids = fields.Many2many('relative', string='Previous Residents', compute='_compute_relative_ids')
    current_relative_ids = fields.One2many('relative', 'current_address_id', string='Current Residents', readonly=True)

    def _compute_relative_ids(self):
        for address in self:
            relative_ids = self.env['relative'].search([('address_ids', 'in', address.id)])
            address.relative_ids = relative_ids.ids
            address.past_relative_ids = (relative_ids - address.current_relative_ids).ids

    head_of_household_id = fields.Many2one('relative', string='Head of Household')
    head_of_household_id_image_128 = fields.Image(related='head_of_household_id.image_128')

