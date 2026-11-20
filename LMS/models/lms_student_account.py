"""LMS Student Account Model"""

from odoo import fields,models

class LmsStudentAccount(models.Model):
    """LMS Student Account Model"""
    _name = 'lms.student.account'
    _description = 'LMS Student Account'
    _rec_name = 'account_id'

    account_id = fields.Char(unique=True,string='Account ID',required=True)

    _check_account_id = models.Constraint(
        'UNIQUE(account_id)',
        'account id must be unique',
    )