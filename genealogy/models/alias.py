from odoo import models, fields, api

class ResPartnerRelationship(models.Model):
    _name = 'res.partner.alias'

    partner_id = fields.Many2one('res.partner', string='Partner')
    name = fields.Char('Alias')
