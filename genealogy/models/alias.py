from odoo import models, fields, api

class ResPartnerAlias(models.Model):
    _name = 'res.partner.alias'

    name = fields.Char('Alias')
    alias_type = fields.Selection([
        ('nickname', 'Nickname'),
        ('religious', 'Religious Name'),
    ], string='Alias Type')
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
