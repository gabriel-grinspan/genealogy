from odoo import models, fields, api, _


class RelativeDeath(models.Model):
    _name = 'relative.death'
    _description = 'Cause Of Death'

    name = fields.Char('Name')


class RelativeOccupation(models.Model):
    _name = 'relative.occupation'
    _description = 'Occupation'

    name = fields.Char('Name')


class RelativeSuffix(models.Model):
    _name = 'relative.suffix'
    _description = 'Suffix'

    name = fields.Char('Name')
