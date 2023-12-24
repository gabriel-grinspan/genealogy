from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResCountry(models.Model):
    _inherit = 'res.country'

    code = fields.Char(
        string='Country Code',
        size=4,
        required=True,
        help='The ISO country code in two chars.\nAlternitavely four char ISO 3166-3.\nYou can use this field for quick search.')
