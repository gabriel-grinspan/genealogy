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
	'depends': [
		'base',
		'web',
		'mail',
	],

	# always loaded
	'data': [
		'data/res_groups.xml',
		'security/ir.model.access.csv',
		'views/relative_address_views.xml',
		'views/relative_alias_views.xml',
		'views/relative_city_views.xml',
		'views/relative_data_views.xml',
		'views/relative_family_views.xml',
		'views/relative_parent_views.xml',
		'views/relative_relationship_views.xml',
		'views/relative_views.xml',
		'views/res_country_views.xml',
		'views/genealogy_menu_items.xml',
		'wizard/relative_pedigree_wizard_views.xml',
		'wizard/relative_relationship_wizard_views.xml',
	],

	'assets': {
		'web.assets_backend': [
			'genealogy/static/src/js/list_renderer_no_link.js',
			'genealogy/static/src/views/fields/boolean_emoji_field.js',
			'genealogy/static/src/views/fields/boolean_emoji_field.xml',
			'genealogy/static/src/views/fields/char_iframe_field.js',
			'genealogy/static/src/views/fields/char_iframe_field.xml',
			'genealogy/static/src/views/kanban/kanban_record.js',
		],
	},
	'application': True,
}
