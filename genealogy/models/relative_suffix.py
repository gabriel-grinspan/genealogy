from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RelativeSuffix(models.Model):
    _name = 'relative.suffix'
    _description = 'Suffix'

    name = fields.Char('Name')
