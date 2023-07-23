from odoo import models, fields, api

class ResPartnerAlias(models.Model):
    _name = 'res.partner.alias'

    name = fields.Char('Alias')
    alias_type_ids = fields.Many2many('res.partner.alias.type', string='Type')
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    sequence = fields.Integer('Sequence')


class ResPartnerAliasType(models.Model):
    _name = 'res.partner.alias.type'

    name = fields.Char('Reason')
