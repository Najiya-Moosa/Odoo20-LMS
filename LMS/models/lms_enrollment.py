# -*- coding: utf-8 -*-
"""LMS Enrollment"""
import re
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

from odoo import api, fields, models
from odoo.orm.commands import Command
from reportlab.pdfbase.pdfdoc import count


class LmsEnrollment(models.Model):
    """model for LMS Enrollment"""
    _name = 'lms.enrollment'
    _description = 'LMS Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'

    reference = fields.Char(string='Reference', required=True, copy=False,
                            readonly=True,
                            default=lambda self: 'New')
    reference_id = fields.Selection(selection='_get_reference_ids',
                                    string='Reference ID', required=True,)
    # name = fields.Char(required=True,string='Name')
    date = fields.Date(string='Date of Enrollment', default=fields.Date.today, )
    due_date = fields.Date(compute='compute_due_date', string='Due Date',store=True)
    is_lead = fields.Boolean(string='Is Lead?')
    course_fee = fields.Monetary(string='Course Fee',readonly=True)
    description = fields.Text(string='Description')
    terms_and_conditions = fields.Html(string='Terms and Conditions')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),

    ], default='draft', tracking=True)
    student_id = fields.Many2one('res.partner', string='Student', required=True,store=True,)
    invoice_id = fields.Many2one('account.move', string='Invoice',readonly=True)
    date_of_birth = fields.Date(string='Date of Birth', readonly=True)

    course_id = fields.Many2one('product.product', string='Course',
                                required=True ,)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id,)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id)
    batch_id = fields.Many2one('lms.batch', string='Batch',)
    scholarship_ids = fields.One2many('lms.scholarship', 'enrollment_id',
                                      string='Scholarships', domain=[
            ('stage_selection', 'in',
             ['fully approved', 'first approved', 'confirmed'])], readonly=True)

    _unique_course = models.Constraint(
        'UNIQUE(student_id,course_id)',
        'This student already enrolled in this course',
        )

    def button_confirm(self):
        """method to confirm the enrollment"""
        self.state = 'confirmed'

    def button_cancel(self):
        """method to cancel enrollment"""
        self.state = 'cancelled'

    def button_done(self):
        """method to cancel enrollment"""
        self.state = 'done'
        template = self.env.ref('LMS.email_template_name')
        template.send_mail(self.id, force_send=True)

    @api.model_create_multi
    def create(self, vals_list):
        """method to create unique sequence number"""
        for record in vals_list:
            if record.get('reference', 'New') == 'New':
                record['reference'] = self.env['ir.sequence'].next_by_code(
                    'lms.enrollment')
        return super().create(vals_list)

    @api.constrains('reference_id')
    def check_reference_id(self):
        """method to validate reference id"""
        for record in self:
            if record.reference_id:
                pattern = r'^(?=(?:.*[a-zA-Z]){3})(?=(?:.*[0-9]){3})(?=(?:.*[^a-zA-Z0-9]){2}).+$'
                if not re.fullmatch(pattern, record.reference_id):
                    raise ValidationError(
                        "reference id must contain 3 alphabets, 3 numbers and 2 special characters")

    @api.onchange('course_id')
    def onchange_course_id(self):
        """method to fetch the course fee from course id"""
        for record in self:
            if record.course_id:
                record.course_fee = record.course_id.list_price

    @api.constrains('batch_id')
    def check_capacity(self):
        """method to validate course capacity"""
        for record in self:
            if record.batch_id.capacity < record.batch_id.student_count:
                raise ValidationError("This batch is full")
    @api.constrains('course_fee')
    def zero_course_fee(self):
        if self.course_fee == 0:
            raise ValidationError("Course fee must be greater than 0")

    @api.depends('date')
    def compute_due_date(self):
        """method to compute due date"""
        for record in self:
            if record.date:
                record.due_date = record.date + relativedelta(days=15)


    @api.onchange('reference_id')
    def onchange_reference_id(self):
        """method to fetch student and date of birth from res.partner"""

        if self.reference_id:
            student = self.env['res.partner'].search(
                [('reference_id', '=', self.reference_id)])
            # if student:
            self.write({'student_id': student})
            self.write({'date_of_birth': student.date_of_birth})
        #     else:
        #         self.student_id = False
        #         self.date_of_birth = False
        #         raise ValidationError('No student found with this Reference ID')
        # else:
        #     self.student_id = False
        #     self.date_of_birth = False

    @api.model
    def _get_reference_ids(self):
        """to show reference ids of students in the reference id field"""
        students = self.env['res.partner'].search(
            [('reference_id', '!=', False)])
        return [(student.reference_id, student.reference_id) for student in students]

    @api.model
    def _cron_generate_due_invoices(self):
        today = fields.Date.today()
        enrollments = self.search([('due_date', '<', today),('state','=','confirmed')])

        for enrollment in enrollments:
            if enrollment.state == 'draft' or enrollment.state == 'cancelled':
                continue
            if enrollment.invoice_id:
                continue
            invoice_lines = [
                Command.create({
                    'product_id': enrollment.course_id.id,
                    'name': 'Course Fee',
                    'quantity': 1,
                    'price_unit': enrollment.course_fee,
                })
            ]
            scholarships = enrollment.scholarship_ids.filtered(
                lambda s: s.stage_selection in ['fully approved'])
            for scholarship in scholarships:
                if scholarship.discount_amount>0:
                    invoice_lines.append(Command.create({
                        'name': scholarship.name,
                        'quantity': 1,
                        'price_unit': -scholarship.discount_amount,
                    }
                    ))
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'partner_id': enrollment.student_id.id,
                'invoice_line_ids': invoice_lines,
                'enrollment_id': enrollment.id,
            })
            enrollment.invoice_id = invoice.id
            invoice.action_post()
