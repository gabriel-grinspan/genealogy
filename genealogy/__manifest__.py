# -*- coding: utf-8 -*-
{
    'name': "Genealogy",
    'license': 'LGPL-3',

    'summary': "Genealogy App",

    'description': "Track the family tree",

    'author': "Gabriel Grinspan",
    'website': "https://www.ggrinspan.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'wizard/res_partner_relationship_wizard_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'genealogy/static/src/js/list_renderer_no_link.js',
        ],
    },
    'application': True,
}
