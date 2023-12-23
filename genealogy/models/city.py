from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RelativeCity(models.Model):
    _name = 'relative.city'
    _description = 'City'
    
    name_id = fields.Many2one('relative.city.name', string='Current Name', domain="[('id', 'in', name_ids)]", inverse='_set_name_id')
    name_ids = fields.Many2many('relative.city.name', string='Previous Names')
    name = fields.Char('Name', related='name_id.name')
    state_id = fields.Many2one('res.country.state', string='Current State', related='name_id.state_id')
    country_id = fields.Many2one('res.country', string='Current Country', related='name_id.country_id')

    @api.onchange('name_id')
    def _set_name_id(self):
        for city in self:
            if city.name_id and city.name_id.id not in city.name_ids.ids:
                city.name_ids |= city.name_id


class RelativeCityName(models.Model):
    _name = 'relative.city.name'
    _description = 'City Name'

    sequence = fields.Integer('Sequence')
    name = fields.Char('Name')
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country')
    city_ids = fields.One2many('relative.city', 'name_id', string='City')
