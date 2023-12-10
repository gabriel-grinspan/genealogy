from odoo import models, fields, api

class ResPartnerAlias(models.Model):
    _name = 'res.partner.alias'
    _description = 'Alias'

    name = fields.Char('Alias')
    alias_type_ids = fields.Many2many('res.partner.alias.type', string='Type')
    note = fields.Text('Notes')
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    sequence = fields.Integer('Sequence')


class ResPartnerAliasType(models.Model):
    _name = 'res.partner.alias.type'
    _description = 'Alias Type'

    name = fields.Char('Reason')
    alias_count = fields.Integer('Alias Count', compute='_compute_alias_count')


    def _compute_alias_count(self):
        for record in self:
            record.alias_count = self.env['res.partner.alias'].search_count([('alias_type_ids', 'in', self.id)])

    def get_aliases(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Aliases',
            'view_mode': 'tree',
            'res_model': 'res.partner.alias',
            'domain': [('alias_type_ids', 'in', self.id)],
        }
