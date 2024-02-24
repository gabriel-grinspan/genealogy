# -*- coding: utf-8 -*-
{
    'name': "Genealogy - Historical Fields",
    'license': 'LGPL-3',

    'summary': "Compatibility with old data",

    'description': """
        - Family codes
    """,

    'author': "Gabriel Grinspan",
    'website': "https://www.ggrinspan.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0.0.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'genealogy',
    ],

    # always loaded
    'data': [
        'views/relative_views.xml',
    ],
}

