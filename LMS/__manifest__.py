# -*- coding: utf-8 -*-
{
    'name': "Learning Management System",
    'summary': "Learning Management System",
    'description': " centralized system to manage student enrollments, courses, scholarships, academic batches, and course-related billing.",
    'version': "20.0.1.0.0",
    'depends': ['base','sale','mail'],
    'application': True,
    'liscence': "LGPL Version 3",
    'category': 'Learning Management',
    'author': "demo",
    'data': [
        'security/lms_security.xml',
        'security/ir.access.csv',
        'data/lms_sequence_data.xml',
        'data/product_demo.xml',
        'data/ir_cron_data.xml',
        'data/email_template.xml',
        'views/account_move_view.xml',
        'views/lms_enrollment_view.xml',
        'views/lms_crm_lead.xml',
        'views/lms_res_partner_view.xml',
        'views/lms_scholarship_view.xml',
        'views/lms_student_account.xml',
        'views/lms_batch_view.xml',
        'views/lms_menus.xml',
    ]

}