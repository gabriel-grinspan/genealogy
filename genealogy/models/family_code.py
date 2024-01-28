from odoo import models, fields, api


class RelativeFamily(models.Model):
    _name = 'relative.family'
    _description = 'Family'
    _rec_name = 'display_name'

    name = fields.Char('Family Name', required=True)
    code = fields.Char('Family Code', size=2, required=True)
    display_name = fields.Char(compute='_compute_display_name')
    relative_ids = fields.One2many(
        comodel_name='relative',
        inverse_name='family_id',
        string='Family Members',
        readonly=True,
    )

    def _compute_display_name(self):
        for family in self:
            family.display_name = f'[{family.code}] {family.name}'


class RelativeTribe(models.Model):
    _name = 'relative.tribe'
    _description = 'Tribe'

    name = fields.Char('Tribe', required=True)
    relative_ids = fields.One2many(
        comodel_name='relative',
        inverse_name='tribe_id',
        string='Family Members',
        readonly=True,
    )
