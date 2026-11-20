# -*- coding: utf-8 -*-
"""LMS Batch"""
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.orm.commands import Command


class LMSBatch(models.Model):
    """LMS Batch"""
    _name = 'lms.batch'
    _description = 'LMS Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(required=True,string='Name')
    capacity = fields.Integer(tracking=True,string='Capacity')
    student_count = fields.Integer(compute='_compute_student_count',
                                   string='Number of Students',tracking=True)
    invoice_count = fields.Integer(compute='_compute_invoice_count',)
    total_course_fee = fields.Monetary(compute='_compute_total_course_fee',
                                       string='Total Course Fee')
    to_invoice = fields.Integer(compute='_compute_to_invoice',)
    start_date = fields.Date(default=fields.Date.today(),string='Start Date')
    end_date = fields.Date(string='End Date')
    active = fields.Boolean(default=True,string='Active')
    course_id = fields.Many2one('product.product',
                                required=True,string='Course')
    enrollment_ids = fields.Many2many('lms.enrollment',
                                      string='Enrollment',)
    scholarship_ids = fields.One2many('lms.scholarship',
                                      string='Scholarship' ,compute="_compute_scholarship")

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id, string='Company')
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  string='Currency')

    @api.depends('enrollment_ids')
    def _compute_student_count(self):
        for batch in self:
            batch.student_count = len(batch.enrollment_ids)

    @api.depends('enrollment_ids')
    def _compute_invoice_count(self):
        self.invoice_count = len(self.enrollment_ids.invoice_id)

    @api.depends('enrollment_ids')
    def _compute_to_invoice(self):
        self.to_invoice = len(self.enrollment_ids) - len(self.enrollment_ids.invoice_id)

    @api.depends('course_id')
    def _compute_total_course_fee(self):
        for record in self:
            record.total_course_fee= record.student_count * record.course_id.list_price

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError('The start date must be anterior to the end date.')

    @api.depends('enrollment_ids')
    def _compute_scholarship(self):
        """fetch scholarship info from enrollment"""
        for record in self:
            approved_scholarship  = (record.enrollment_ids.scholarship_ids.filtered
                                     (lambda s: s.stage_selection in ['fully approved']))
            record.scholarship_ids = [Command.set(approved_scholarship.ids)]

    @api.onchange('enrollment_ids')
    def _check_capacity(self):
        for record in self:
            if len(record.enrollment_ids.mapped('student_id')) > record.capacity:
                raise ValidationError('Enrollment exceeds student capacity.')


    def stat_button(self):
        """Return student list to the smart button of those who are enrolled"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'students',
            'res_model': 'res.partner',
            'view_mode': 'list',
            'domain'  :[('id','in',self.enrollment_ids.mapped('student_id').ids)]
        }


    def create_invoice(self):
        """create invoice"""
        for record in self:
            count = 0

            for enrollment in record.enrollment_ids:
                if enrollment.state == 'draft' or enrollment.state == 'cancelled':
                    continue
                if enrollment.invoice_id:
                    continue
                scholarships = enrollment.scholarship_ids.filtered(lambda s: s.stage_selection in ['fully approved'])
                invoice_lines= [
                        Command.create( {
                            'product_id': enrollment.course_id.id,
                            'name': 'Course Fee',
                            'quantity': 1,
                            'price_unit': enrollment.course_fee,
                            # 'price_subtotal': self.enrollment_ids.course_fee,
                        })
                    ]
                for scholarship in scholarships:
                        invoice_lines.append(Command.create({
                            'name' : scholarship.name,
                            'quantity': 1,
                            'price_unit':-scholarship.discount_amount,
                        }
                        ))
                invoice = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.today(),
                    'partner_id':enrollment.student_id.id,
                    'invoice_line_ids': invoice_lines,
                    'enrollment_id': enrollment.id,
                })
                enrollment.invoice_id = invoice.id
                invoice.action_post()



    def stat_button_invoice(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('enrollment_id', 'in', self.enrollment_ids.ids)]
        }
