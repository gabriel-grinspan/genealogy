from odoo import models, fields, api


class RelativeRelationship(models.Model):
    _name = 'relative.relationship'
    _description = 'Relationship'

    male_id = fields.Many2one('relative', string='Husband')
    female_id = fields.Many2one('relative', string='Wife')
    status_id = fields.Many2one('relative.relationship.status', string='Relationship Status', required=True)

    date_of_marriage = fields.Date('Wedding Date')
    marriage_after_sunset = fields.Boolean()
    date_of_marriage_approximate = fields.Boolean('Approximate Wedding Date')
    lunisolar_date_of_marriage = fields.Char(compute='_compute_lunisolar_date_of_marriage', string='Hebrew Wedding Date')
    marriage_location = fields.Many2one('relative.address', string='Place of Marriage', domain="[('address_type', '=', 'marriage')]")

    divorce_date = fields.Date('Separation Date')


    @api.depends('date_of_marriage', 'marriage_after_sunset', 'date_of_marriage_approximate')
    def _compute_lunisolar_date_of_marriage(self):
        for relationship in self:
            relationship.lunisolar_date_of_marriage = not relationship.date_of_marriage_approximate and self.env['relative']._get_lunisolar_date(relationship.date_of_marriage, relationship.marriage_after_sunset)


class RelativeRelationshipStatus(models.Model):
    _name = 'relative.relationship.status'
    _description = 'Relationship Status'

    name = fields.Char('Status', required=True)
    ended = fields.Boolean('Ended')
