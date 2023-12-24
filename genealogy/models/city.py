from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RelativeCity(models.Model):
    _name = 'relative.city'
    _description = 'City'
    
    name_id = fields.Many2one('relative.city.name', string='Current Name', domain="[('id', 'in', name_ids)]", inverse='_set_name_id')
    name_ids = fields.Many2many('relative.city.name', string='Previous Names', inverse='_set_name_ids')
    name = fields.Char('Name', related='name_id.name')
    state_id = fields.Many2one('res.country.state', string='Current State', related='name_id.state_id')
    country_id = fields.Many2one('res.country', string='Current Country', related='name_id.country_id')
    note = fields.Html('Notes')

    @api.onchange('name_id')
    def _set_name_id(self):
        for city in self:
            if city.name_id and city.name_id.id not in city.name_ids.ids:
                city.name_ids |= city.name_id

    @api.onchange('name_ids')
    def _set_name_ids(self):
        for city in self:
            overlap_cities = city.search([('name_ids', 'in', city.name_ids.ids)]) - city
            for overlap_city in overlap_cities:
                overlap_city.name_ids -= city.name_ids


class RelativeCityName(models.Model):
    _name = 'relative.city.name'
    _description = 'City Name'

    sequence = fields.Integer('Sequence')
    name = fields.Char('Name')
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country')
    city_id = fields.Many2one('relative.city', string='Current Name', compute='_compute_city_id')

    def _compute_city_id(self):
        for city in self:
            if not city.id:
                city.city_id = False
                continue

            city.city_id = city.env['relative.city'].search([('name_ids', 'in', city.ids)])

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id and self.state_id.country_id and self.state_id.country_id.id != self.country_id.id:
            self.country_id = self.state_id.country_id.id

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.state_id and self.country_id.id != self.state_id.country_id.id:
            self.state_id = False
