# -*- coding: utf-8 -*-
# © 2016 - Eficent http://www.eficent.com/
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Lock partner and log changes',
    'version': '7.0.1.00',
    'author': 'Eficent',
    'category': 'Partner',
    'depends': ['base'],
    'description': """Add group to modify partner""",
    'data': ['security/partner.xml',
             'view/partner_view.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
