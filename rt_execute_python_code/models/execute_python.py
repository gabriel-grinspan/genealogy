import traceback
from odoo import models, fields, _
from odoo.exceptions import UserError

class ExecutePythonCode(models.Model):
    _name = "execute.python.code"
    _description = "Execute Python Code"

    name = fields.Char(string='Script Name', size=1024, required=True, default='Untitled Script')
    code = fields.Text(string='Python Code', required=True, default= \
"""import logging


_logger = logging.getLogger(__name__)
# _logger.info('My name is Bob.')
# _logger.warning('My name is not Bob.')
# _logger.error('Who is Bob?')
# _logger.critical('What is a \'name\'?!?')
# result = self.env['stock.picking'].search([('id','>',0)])
# result = self.env['purchase.order'].browse(1)
""")
    result = fields.Text(string='Result', readonly=True)

    def execute_code(self):
        local_dict = {'self': self, 'user_obj': self.env.user}
        for obj in self:
            try:
                exec(obj.code, local_dict)
                output = local_dict.get('result', None)
                if output is not None:
                    self.result = str(output)
                else:
                    self.result = 'No output'
            except Exception as e:
                raise UserError(_(f'Python code is not able to run! message: {traceback.format_exc()}'))
        return True
