# -*- coding: utf-8 -*-
# © 2016 - Eficent http://www.eficent.com/
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields


class ResPartner(orm.Model):
    """Add third field in address"""
    _name = 'res.partner'
    _inherit = ['res.partner']

    _columns = {
        'name': fields.boolean('Lock Partner',
                               help='Users cannot modify this partner'),
    }

    _track = {
        'lock': {
        },
    }

    _defaults = {'lock': False}
