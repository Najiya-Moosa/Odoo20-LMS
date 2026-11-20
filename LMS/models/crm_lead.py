from odoo import api, fields, models, exceptions

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    order_id = fields.Char(string='Order ID')