import traceback

from odoo import _, fields, models
from odoo.exceptions import UserError


class ExecutePythonCode(models.Model):
    _name = "execute.python.code"
    _description = "Execute Python Code"

    name = fields.Char(string='Script Name', size=1024, required=True, default='Untitled Script')
    active = fields.Boolean('Active', default=True)
    code = fields.Text(string='Python Code', required=True, default= \
"""import logging


_logger = logging.getLogger(__name__)
# _logger.info('My name is Bob.')

# result = self.env['sale.order'].browse(1).read()
# result = self.env['purchase.order'].search([]).read()
# result = self.env['stock.picking'].search([], limit=1).read()

""")
    result = fields.Text(string='Result', readonly=True)

    def execute_code(self):
        self.ensure_one()

        try:
            local_dict = {'self': self}
            exec(self.code, local_dict)
            output = local_dict.get('result', None)
            if output is not None:
                self.result = str(output)
            else:
                self.result = 'No output'
        except Exception as e:
            raise UserError(_(f'{traceback.format_exc()}'))
        return True
