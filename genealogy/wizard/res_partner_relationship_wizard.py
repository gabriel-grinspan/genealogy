from odoo import models, fields, api, _
from odoo.addons.genealogy.models.relationship import RELATIONSHIP_STATUSES
from odoo.exceptions import UserError


class RelationshipWizard(models.TransientModel):
    _name = 'res.partner.relationship.wizard'
    _description = 'Relationship Creation Wizard'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    status = fields.Selection(RELATIONSHIP_STATUSES, string='Relationship Status', required=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    def create_relationship(self):
        current_partner_id = self._context.get('active_id')
        if not current_partner_id:
            raise UserError(_('You should not have been able to do this. There should be a related res.partner id attached to the context.'))

        current_partner = self.env['res.partner'].browse(current_partner_id)

        if (
            current_partner.sex == self.partner_id.sex or
            current_partner.sex == 'male' or
            self.partner_id.sex == 'female'
        ):
            male = current_partner_id
            female = self.partner_id.id
        else:
            male = self.partner_id.id
            female = current_partner_id

        self.env['res.partner.relationship'].create({
            'male_id': male,
            'female_id': female,
            'status': self.status,
            'start_date': self.start_date,
            'end_date': self.end_date,
        })
