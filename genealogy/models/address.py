from odoo import models, fields, api

class ResPartnerAddress(models.Model):
    _name = 'res.partner.address'
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
    phone = fields.Char(tracking=2)
    comment = fields.Text()

    address_type = fields.Selection([
        ('home', 'Home Address'),
        ('birthplace', 'Birthplace'),
        ('burial_plot', 'Burial Plot'),
    ], string='Address Type')

    partner_ids = fields.Many2many('res.partner', string='Residents', compute='_compute_partner_ids')
    current_partner_ids = fields.One2many('res.partner', 'current_address_id', string='Current Residents')

    def _compute_partner_ids(self):
        for address in self:
            address.partner_ids = self.env['res.partner'].search([('address_ids', 'in', address.id)]).ids

    head_of_household_id = fields.Many2one('res.partner', string='Head of Household')
    head_of_household_id_image_128 = fields.Image(related='head_of_household_id.image_128')

