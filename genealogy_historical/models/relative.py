# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Relative(models.Model):
    _inherit = 'relative'

    family_number = fields.Integer('Family ID', readonly=True)
    family_code = fields.Char('Family Code', readonly=True, compute='_compute_family_code', store=True)

    @api.depends('family_id', 'family_number')
    def _compute_family_code(self):
        for relative in self:
            relative.family_code = f'{relative.family_id.code}{relative.family_number}'
