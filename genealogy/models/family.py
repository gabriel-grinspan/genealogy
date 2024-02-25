from odoo import models, fields, api


class RelativeParent(models.Model):
    _name = 'relative.parent'
    _description = 'Non-biological Parent'

    name = fields.Char(compute='_compute_name')
    sequence = fields.Integer('Sequence')
    parent_id = fields.Many2one('relative', string='Parent')
    child_id = fields.Many2one('relative', string='Child')
    reason = fields.Selection([
        ('adopted', 'Adopted Parent'),
        ('god', 'God Parent'),
        ('other', 'Other'),
    ], string='Reason', required=True)
    child_parent_ids = fields.Many2many('relative', compute='_compute_child_parent_ids')


    @api.depends('child_id', 'child_id.parent_line_ids', 'child_id.parent_line_ids.parent_id')
    def _compute_child_parent_ids(self):
        for parent_line in self:
            parent_line.child_parent_ids = parent_line.child_id.mother_id | parent_line.child_id.father_id | parent_line.child_id.parent_line_ids.mapped('parent_id') - parent_line.parent_id

    def _compute_name(self):
        for parent_line in self:
            parent_line.name = parent_line.parent_id.display_name


class RelativeFamily(models.Model):
    _name = 'relative.family'
    _description = 'Family'

    name = fields.Char('Family Name', required=True)
    code = fields.Char('Family Code', size=2, required=True)
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
