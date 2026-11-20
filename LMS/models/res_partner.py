# -*- coding: utf-8 -*-
"""res partner"""
import re
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    """res.partner"""
    _inherit = 'res.partner'

    reference_id = fields.Char(string='Reference ID',required=True)
    student_account_id = fields.Char(string='Student Account ID',required=True)
    date_of_birth = fields.Date(string='Date of Birth',required=True)
    is_student = fields.Boolean(string='Is Student')


    @api.constrains('reference_id')
    def check_reference_id(self):
        """check if reference id is valid"""
        for record in self:
            if record.reference_id:
                pattern = r'^(?=(?:.*[a-zA-Z]){3})(?=(?:.*[0-9]){3})(?=(?:.*[^a-zA-Z0-9]){2}).+$'
                if not re.fullmatch(pattern, record.reference_id):
                    raise ValidationError("reference id must contain 3 alphabets,"
                                          " 3 numbers and 2 special characters")
