from odoo import models, fields, api, _

class RelativeSuffix(models.Model):
    _name = 'relative.suffix'
    _description = 'Suffix'

    name = fields.Char('Name')
