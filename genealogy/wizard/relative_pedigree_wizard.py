from odoo import models, fields


class PedigreeWizard(models.TransientModel):
    _name = 'relative.pedigree.wizard'
    _description = 'Pedigree View'

    def _get_url_context(self):
        return self._context.get('url')

    url = fields.Char('URL', default=_get_url_context)
