from odoo import models, fields, api
from odoo.osv import expression

class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_of_birth = fields.Date('Date of Birth')
    father_id = fields.Many2one('res.partner', string='Father')
    mother_id = fields.Many2one('res.partner', string='Mother')
    spouse_id = fields.Many2one('res.partner', string='Spouse')
    children_ids = fields.Many2many('res.partner', string='Children', compute='_compute_children_ids')

    def _compute_children_ids(self):
        for partner in self:
            domain = ['|', ('father_id', '=', partner.id), ('mother_id', '=', partner.id)]
            partner.children_ids = self.search(domain).ids
