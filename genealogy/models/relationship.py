from odoo import models, fields, api


class ResPartnerRelationship(models.Model):
    _name = 'res.partner.relationship'

    sequence = fields.Integer('Sequence')
    male_id = fields.Many2one('res.partner', string='Husband')
    female_id = fields.Many2one('res.partner', string='Wife')
    # partner_id = fields.Many2one('res.partner', compute='_compute_partner_id', inverse='_set_partner_id')
    status = fields.Selection([
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('deceased', 'Deceased Partner'),
        ('live_together', 'Living Together'),
        ('dating', 'Dating'),
        ('children', 'Have Children Together'),
    ], string='Relationship Status')
    start_date = fields.Date('Start')
    end_date = fields.Date('End')

    # def _compute_partner_id(self):
    #     for relationship in self:
    #         partner_ids = (relationship.male_id | relationship.female_id).ids
    #         if len(partner_ids) > 1:
    #             partner_ids.remove(relationship._context.get('partner_id'))
    #             relationship.partner_id = partner_ids[0]

    # def _set_partner_id(self):
    #     partner_id = self._context.get('partner_id') or self._context.get('params').get('id')
    #     if self.male_id.id == partner_id:
    #         self.female_id = self.partner_id.id
    #     elif self.female_id.id == partner_id:
    #         self.male_id = self.partner_id.id
