# -*- coding: utf-8 -*-
"""lms scholarship"""
from odoo import fields,models,api
from odoo.exceptions import UserError

class LmsScholarship(models.Model):
    """LMS Scholarship Model"""
    _name = 'lms.scholarship'
    _description = 'LMS Scholarship'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Name',required=True)
    stage_selection = fields.Selection([
        ('pending','Pending'),
        ('confirmed','Confirmed'),
        ('first approved','First Approved'),
        ('fully approved','Fully Approved'),
        ('rejected','Rejected'),
    ],default='pending',string='Stage',tracking=True)
    discount_amount = fields.Monetary(string='Discount Amount',required=True)
    enrollment_id = fields.Many2one('lms.enrollment',string='Enrollment ID',required=True)
    student_id = fields.Many2one(related='enrollment_id.student_id',string='Student')
    company_id = fields.Many2one('res.company',string='Company',
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    due_date = fields.Date(related='enrollment_id.due_date',string='Due Date')

    def button_approve(self):
        """Button to First Approve LMS Scholarship"""
        self.stage_selection='first approved'

    def button_reject(self):
        """Button to Reject LMS Scholarship"""
        self.stage_selection='rejected'

    def button_confirm(self):
        """Button to Confirm LMS Scholarship"""
        self.stage_selection='confirmed'

    def button_full_approve(self):
        """Button to Fully Approve LMS Scholarship"""
        self.stage_selection='fully approved'

    @api.constrains('discount_amount')
    def discount_amount_constraint(self):
        """validate discount amount"""
        if self.discount_amount<=0:
            raise UserError('Discount amount must be above zero')
        if self.discount_amount>self.enrollment_id.course_fee:
            raise UserError('Discount amount cannot be more than the course fee')

