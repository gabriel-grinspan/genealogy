from odoo import models, fields, api

class ResPartnerFamily(models.Model):
    _name = 'res.partner.family'
    _description = 'Family'
    _rec_name = 'display_name'

    name = fields.Char('Family Name', required=True)
    code = fields.Char('Family Code', size=2, required=True)
    display_name = fields.Char(compute='_compute_display_name')
    partner_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='family_id',
        string='Family Members',
        readonly=True,
    )

    def _compute_display_name(self):
        for family in self:
            family.display_name = f'[{family.code}] {family.name}'
