from odoo import models, fields, api, _
from odoo.addons.base.models.res_country import NO_FLAG_COUNTRIES, FLAG_MAPPING
from odoo.exceptions import UserError

class ResCountry(models.Model):
    _inherit = 'res.country'

    code = fields.Char(
        string='Country Code',
        size=4,
        required=True,
        help='The ISO country code in two chars.\nAlternitavely four char ISO 3166-3.\nYou can use this field for quick search.')

    @api.depends('code')
    def _compute_image_url(self):
        for country in self:
            if not country.code or country.code in NO_FLAG_COUNTRIES or len(country.code) != 2:
                country.image_url = False
            else:
                code = FLAG_MAPPING.get(country.code, country.code.lower())
                country.image_url = "/base/static/img/country_flags/%s.png" % code
