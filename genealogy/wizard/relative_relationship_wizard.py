from odoo import models, fields, api, _
from odoo.addons.genealogy.models.relationship import RELATIONSHIP_STATUSES
from odoo.exceptions import UserError


class RelationshipWizard(models.TransientModel):
    _name = 'relative.relationship.wizard'
    _description = 'Relationship Creation Wizard'

    relative_id = fields.Many2one('relative', string='Partner', required=True)
    status = fields.Selection(RELATIONSHIP_STATUSES, string='Relationship Status', required=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    def create_relationship(self):
        current_relative_id = self._context.get('active_id')
        if not current_relative_id:
            raise UserError(_('You should not have been able to do this. There should be a related relative id attached to the context.'))

        current_partner = self.env['relative'].browse(current_relative_id)

        if (
            current_partner.sex == self.relative_id.sex or
            current_partner.sex == 'male' or
            self.relative_id.sex == 'female'
        ):
            male = current_relative_id
            female = self.relative_id.id
        else:
            male = self.relative_id.id
            female = current_relative_id

        self.env['relative.relationship'].create({
            'male_id': male,
            'female_id': female,
            'status': self.status,
            'start_date': self.start_date,
            'end_date': self.end_date,
        })
