from odoo import models, fields, api
from odoo.osv import expression

import requests
# import datetime
import logging

_logger = logging.getLogger(__name__)

class ResPartnerResidence(models.Model):
    _name = 'res.partner.residence'

    resident_id = fields.Many2one('res.partner', string='Resident')
    residence_type = fields.Selection([
        ('birthplace', 'Birthplace'),
        ('previous_address', 'Previous Address'),
        ('current_address', 'Current Address'),
        ('burial_plot', 'Burial Plot'),
    ], string='Address Type')
