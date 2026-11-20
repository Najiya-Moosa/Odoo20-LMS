# -*- coding: utf-8 -*-

"""invoice"""
from odoo import api, fields, models

class AccountMove(models.Model):
    """Invoice Model"""
    _inherit = 'account.move'

    enrollment_id = fields.Many2one('lms.enrollment',string='Enrollment ID')





