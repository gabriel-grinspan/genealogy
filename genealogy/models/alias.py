from odoo import models, fields, api

class RelativeAlias(models.Model):
    _name = 'relative.alias'
    _description = 'Alias'

    name = fields.Char('Alias', required=True)
    alias_type_ids = fields.Many2many('relative.alias.type', string='Type', required=True)
    note = fields.Text('Notes')
    relative_id = fields.Many2one('relative', string='Partner', readonly=True)
    sequence = fields.Integer('Sequence')


class RelativeAliasType(models.Model):
    _name = 'relative.alias.type'
    _description = 'Alias Type'

    name = fields.Char('Reason')
    alias_count = fields.Integer('Alias Count', compute='_compute_alias_count')


    def _compute_alias_count(self):
        for record in self:
            record.alias_count = self.env['relative.alias'].search_count([('alias_type_ids', 'in', self.id)])

    def get_aliases(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Aliases',
            'view_mode': 'tree',
            'res_model': 'relative.alias',
            'domain': [('alias_type_ids', 'in', self.id)],
        }
