from odoo import models, fields, api
from odoo.osv import expression

import requests
# import datetime
import logging

_logger = logging.getLogger(__name__)

class ResPartnerResidence(models.Model):
    _name = 'res.partner.residence'

    sequence = fields.Integer('Sequence')
    resident_id = fields.Many2one('res.partner', string='Contact', required=True)
    residence_id = fields.Many2one('res.partner', string='Address', required=True)
    residence_type = fields.Selection([
        ('birthplace', 'Birthplace'),
        ('previous', 'Previous Address'),
        ('current', 'Current Address'),
        ('burial_plot', 'Burial Plot'),
    ], string='Address Type', required=True)
    head_of_household = fields.Boolean('Head of Household')
