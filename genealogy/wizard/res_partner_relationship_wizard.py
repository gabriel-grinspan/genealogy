from odoo import models, fields, api, _
from odoo.addons.genealogy.models.relationship import RELATIONSHIP_STATUSES
from odoo.exceptions import UserError


class RelationshipWizard(models.TransientModel):
    _name = 'res.partner.relationship.wizard'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    status = fields.Selection(RELATIONSHIP_STATUSES, string='Relationship Status', required=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    def create_relationship(self):
        current_partner_id = self._context.get('active_id')
        if not current_partner_id:
            print(self._context)
            raise UserError(_('You should not have been able to do this. There should be a related res.partner id attached to the context.'))

        valid_sexes = {'male', 'female'}

        current_partner = self.env['res.partner'].browse(current_partner_id)
        if not ({current_partner.sex} & valid_sexes or {self.partner_id.sex} & valid_sexes):
            raise UserError(_('You must first specify the sex on one of the partners in this relationship.'))

        if {current_partner.sex} & valid_sexes and not {self.partner_id.sex} & valid_sexes:
            self.partner_id.sex = list(valid_sexes ^ {current_partner.sex})[0]

        if {self.partner_id.sex} & valid_sexes and not {current_partner.sex} & valid_sexes:
            current_partner.sex = list(valid_sexes ^ {self.partner_id.sex})[0]

        self.env['res.partner.relationship'].create({
            'male_id': current_partner_id if current_partner.sex == 'male' else self.partner_id.id,
            'female_id': current_partner_id if current_partner.sex == 'female' else self.partner_id.id,
            'status': self.status,
            'start_date': self.start_date,
            'end_date': self.end_date,
        })
