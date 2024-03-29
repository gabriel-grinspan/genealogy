from odoo import models, fields, api, _
from odoo.tools import html_escape
import requests
import re
from datetime import datetime
from markupsafe import Markup
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class Relative(models.Model):
    _name = 'relative'
    _inherit = ['avatar.mixin', 'mail.activity.mixin', 'mail.thread.blacklist']
    _description = 'Relative'
    _order = 'date_of_birth, last_name, first_name, id'

    title_id = fields.Many2one('res.partner.title', string='Title')
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    name = fields.Char('Name', compute='_compute_name', store=True)
    suffix_id = fields.Many2one('relative.suffix', string='Suffix')
    alias_ids = fields.One2many('relative.alias', 'relative_id', string='Aliases')

    name_orig_ids = fields.Many2many('relative', 'name_dest_id', 'name_orig_id', string='Named After')
    name_dest_ids = fields.Many2many('relative', 'name_orig_id', 'name_dest_id', string='Named Before')
    # TODO: make computed
    name_orig_description = fields.Char('Named After Description')

    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Sex')

    date_of_birth = fields.Date('Date of Birth')
    date_of_birth_approximate = fields.Boolean('Approximate Date of Birth')
    birth_after_sunset = fields.Boolean()
    lunisolar_date_of_birth = fields.Char(compute='_compute_lunisolar_date_of_birth', string='Hebrew Date of Birth')
    
    date_of_death = fields.Date('Date of Death')
    death_after_sunset = fields.Boolean()
    lunisolar_date_of_death = fields.Char(compute='_compute_lunisolar_date_of_death', string='Hebrew Date of Death')
    date_of_death_approximate = fields.Boolean('Approximate Date of Death')
    death_id = fields.Many2many('relative.death', string='Cause of Death')

    age = fields.Char('Age', compute='_compute_age')

    home_phone = fields.Char('Home Phone')
    mobile_phone = fields.Char('Mobile Phone')
    phone = fields.Char(compute='_compute_phone', string='Phone')
    email = fields.Char('Email')

    street = fields.Char(related='current_address_id.street', readonly=True)
    street2 = fields.Char(related='current_address_id.street2', readonly=True)
    zip = fields.Char(related='current_address_id.zip', readonly=True)
    city_name_id = fields.Many2one(related='current_address_id.city_name_id', readonly=True)
    state_id = fields.Many2one(related='current_address_id.state_id', readonly=True)
    country_id = fields.Many2one(related='current_address_id.country_id', readonly=True)
    country_code = fields.Char(related='current_address_id.country_code', readonly=True)

    relative_address_line_ids = fields.One2many('relative.address.line', 'relative_id', string='Addresses')
    address_ids = fields.Many2many('relative.address', string='Addresses', compute='_compute_address_ids', store=True)
    current_address_id = fields.Many2one('relative.address', string='Current Address', compute='_compute_address_ids', store=True)
    head_of_household = fields.Boolean('Head of Household', compute='_compute_address_ids', store=True)
    occupation_ids = fields.Many2many('relative.occupation', string='Occupations')

    tribe_id = fields.Many2one('relative.tribe', string='Tribe')
    family_id = fields.Many2one('relative.family', string='Family')

    father_id = fields.Many2one('relative', string='Father')
    mother_id = fields.Many2one('relative', string='Mother')
    parent_line_ids = fields.One2many('relative.parent', 'child_id', string='Non-biological Parents')
    step_parent_ids = fields.Many2many('relative', string='Step Parents', compute='_compute_step_parent_ids')
    adopted_parent_ids = fields.Many2many('relative', compute='_compute_adopted_parent_ids')

    sibling_sequence = fields.Integer('nth Sibling', compute='_compute_sibling_sequence')
    sibling_ids = fields.Many2many('relative', string='Siblings', compute='_compute_sibling_ids', readonly=True)
    half_sibling_ids = fields.Many2many('relative', string='Half Siblings', compute='_compute_sibling_ids', readonly=True)
    adopted_sibling_ids = fields.Many2many('relative', string='Adopted Siblings', compute='_compute_adopted_sibling_ids', readonly=True)
    step_sibling_ids = fields.Many2many('relative', string='Step Siblings', compute='_compute_step_sibling_ids', readonly=True)

    child_ids = fields.Many2many('relative', string='Children', compute='_compute_child_ids', readonly=True)
    adopted_child_ids = fields.Many2many('relative', string='Non-biological Children', compute='_compute_child_ids', readonly=True)
    step_child_ids = fields.Many2many('relative', string='Step Children', compute='_compute_child_ids', readonly=True)

    spouse_type = fields.Selection([
        ('male', 'Husband'),
        ('female', 'Wife'),
        ('mixed', 'Mixed'),
    ], compute='_compute_spouse_type')
    
    relationship_ids = fields.Many2many(
        'relative.relationship',
        string='Relationships',
        compute='_compute_relationship_ids',
        inverse='_set_relationship_ids',
    )
    spouse_ids = fields.Many2many('relative', string='Current Relationship(s)', compute='_compute_spouse_ids')

    # Can be used for 'Can contact'
    category_ids = fields.Many2many('res.partner.category', string='Tags')
    note = fields.Html('Note')


    def write(self, vals):
        def _get_record_names(names):
            result = ''
            for name in names:
                result += f', {name}'
            if result == '':
                result = 'False'
            else:
                result = result[2:]

            return result

        field_names = {}
        x2many_field_names = {}
        for key in vals:
            field = self.fields_get(key)[key]
            field_data = {
                'string': field['string'],
                'type': field['type'],
                'model': field.get('relation'),
                'selection': field.get('selection'),
            }
            if field['type'] in ['binary']:
                continue
            elif field['type'] in ['one2many', 'many2many']:
                x2many_field_names[key] = field_data
            else:
                field_names[key] = field_data

        relative_comments = {}

        for relative in self:
            comment = ''
            for key in field_names:
                current_val = getattr(relative, key)
                current_val_str = current_val
                new_val = vals[key]
                new_val_str = new_val
                if field_names[key]['type'] == 'selection':
                    selection_options = {k: v for k, v in field_names[key]['selection']}
                    current_val_str = selection_options.get(current_val)
                    new_val_str = selection_options.get(new_val)
                elif field_names[key]['type'] == 'many2one':
                    current_val_str = current_val.name
                    current_val = current_val.id
                    new_val_str = self.env[field_names[key]['model']].browse(new_val).name

                if current_val != new_val:
                    comment += f'<li>{field_names[key]["string"]}: {html_escape(current_val_str)} -> {html_escape(new_val_str)}</li>'
            
            relative_comments[relative] = comment

        x2many_field_vals = {}
        for relative in self:
            x2many_field_vals[relative] = {}
            for key in x2many_field_names:
                current_val = getattr(relative, key)
                x2many_field_vals[relative][key] = current_val
                
        res = super(Relative, self).write(vals)

        for relative in x2many_field_vals:
            comment = ''
            for key in x2many_field_vals[relative]:
                current_val = x2many_field_vals[relative][key]
                current_val_str = _get_record_names(current_val.mapped('display_name'))
                current_val = current_val.ids

                new_val = getattr(relative, key)
                if new_val.ids == current_val:
                    continue
                
                new_val_str = _get_record_names(new_val.mapped('display_name'))

                comment += f'<li>{x2many_field_names[key]["string"]}: {html_escape(current_val_str)} -> {html_escape(new_val_str)}</li>'
            relative_comments[relative] += comment
        
        base_comment = '<ul>'
        base_comment_end = '</ul>'
        for relative in relative_comments:
            comment = relative_comments.get(relative)
            if comment:
                relative.message_post(body=Markup(base_comment+comment+base_comment_end))
        return res

    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        for relative in self:
            relative.name = f'{relative.title_id.shortcut or ""} {relative.first_name or ""} {relative.last_name or ""} {relative.suffix_id.name or ""}'.strip()

    @api.depends('first_name', 'last_name', 'date_of_birth')
    def _compute_display_name(self):
        for relative in self:
            if relative.date_of_birth and relative.name:
                relative.display_name = f'{relative.name} ({relative.date_of_birth.year})'
            else:
                relative.display_name = relative.name

    # @api.depends('name_orig_ids')
    # def _compute_name_dest_ids(self):
    #     for relative in self:
    #         relative.name_dest_ids = self.search([('name_orig_ids', 'in', relative.id)])

    def _get_lunisolar_date(self, date, after_sunset):
        if not date:
            return False

        request_url = f'https://www.hebcal.com/converter?cfg=json&g2h=1&strict=1&date={date.strftime("%Y-%m-%d")}'
        if after_sunset:
            request_url += '&gs=on'

        response = requests.get(request_url).json()
        return response.get('hebrew')

    @api.depends('date_of_birth', 'birth_after_sunset', 'date_of_birth_approximate')
    def _compute_lunisolar_date_of_birth(self):
        for relative in self:
            relative.lunisolar_date_of_birth = not relative.date_of_birth_approximate and self._get_lunisolar_date(relative.date_of_birth, relative.birth_after_sunset)

    @api.depends('date_of_death', 'death_after_sunset', 'date_of_death_approximate')
    def _compute_lunisolar_date_of_death(self):
        for relative in self:
            relative.lunisolar_date_of_death = not relative.date_of_death_approximate and self._get_lunisolar_date(relative.date_of_death, relative.death_after_sunset)

    @api.depends('date_of_birth', 'date_of_death', 'date_of_birth_approximate', 'date_of_death_approximate')
    def _compute_age(self):
        now = fields.Date.today()
        for relative in self:
            if not relative.date_of_birth:
                relative.age = False
            until = relative.date_of_death or now
            age = relativedelta(until, relative.date_of_birth)
            if relative.date_of_birth_approximate or (relative.date_of_death and relative.date_of_death_approximate):
                relative.age = f'~{age.years} years old'
            else:
                age_str_list = []
                if age.years != 0:
                    age_str_list.append(f'{age.years} year{age.years != 1 and "s" or ""}')
                if age.months != 0:
                    age_str_list.append(f'{age.months} month{age.months != 1 and "s" or ""}')
                if age.days != 0 or not age_str_list:
                    age_str_list.append(f'{age.days} day{age.days != 1 and "s" or ""}')
                relative.age = ', '.join(age_str_list) + ' old'
    
    @api.depends('home_phone', 'mobile_phone')
    def _compute_phone(self):
        for relative in self:
            relative.phone = relative.mobile_phone or relative.home_phone

    def _compute_adopted_parent_ids(self):
        for relative in self:
            relative.adopted_parent_ids = relative.parent_line_ids.mapped('parent_id').ids

    def _compute_step_parent_ids(self):
        for relative in self:
            biological_parents = (relative.father_id | relative.mother_id)
            relative.step_parent_ids = (biological_parents.relationship_ids.mapped(
                lambda relationship: (relationship.male_id | relationship.female_id) - biological_parents
            ) - relative.sibling_ids - relative.half_sibling_ids - relative).ids

    @api.depends('relative_address_line_ids', 'relative_address_line_ids.address_id', 'relative_address_line_ids.address_id.head_of_household_id')
    def _compute_address_ids(self):
        def _get_sort_order(rar):
            match rar.address_type:
                case 'birthplace':
                    address_type = 0
                case 'home':
                    address_type = 1
                case 'death':
                    address_type = 2
                case 'burial':
                    address_type = 3
                case _:
                    address_type = -1

            return address_type, rar.sequence

        for relative in self:
            relative_address_line_id = relative.relative_address_line_ids.sorted(_get_sort_order, reverse=True)[:1]
            if relative_address_line_id:
                relative.current_address_id = relative_address_line_id.address_id
                relative.head_of_household = relative_address_line_id.address_id.head_of_household_id.id == relative.id
            else:
                relative.current_address_id = False

            relative.address_ids = relative.relative_address_line_ids.mapped('address_id')
                
    @api.depends('sibling_ids', 'date_of_birth')
    def _compute_sibling_sequence(self):
        for relative in self:
            children = (relative.sibling_ids | relative).sorted(lambda r: (
                r.date_of_birth and str(r.date_of_birth) or '',
            ))
            # Need this for creating new records, otherwise need to use _origin
            if len(children) == 1:
                relative.sibling_sequence = 1
                continue

            for i, child in enumerate(children):
                if child.id == relative.id:
                    relative.sibling_sequence = i + 1
                    break

    @api.depends('father_id', 'mother_id')
    def _compute_sibling_ids(self):
        for relative in self:
            # relative._origin
            if not relative.father_id and not relative.mother_id:
                relative.sibling_ids = False
                relative.half_sibling_ids = False
                continue

            elif not relative.father_id and relative.mother_id:
                domain = [
                    ('mother_id', '=', relative.mother_id.id),
                    ('id', '!=', relative._origin.id),
                ]
            elif relative.father_id and not relative.mother_id:
                domain = [
                    ('father_id', '=', relative.father_id.id),
                    ('id', '!=', relative._origin.id),
                ]
            else:
                domain = [
                    '|',
                        ('father_id', '=', relative.father_id.id),
                        ('mother_id', '=', relative.mother_id.id),
                    ('id', '!=', relative._origin.id),
                ]

            siblings = relative.search(domain)

            if len(domain) == 4:
                full_siblings = siblings.filtered(lambda r: r.father_id.id == relative.father_id.id and r.mother_id.id == relative.mother_id.id)
                full_siblings = full_siblings.sorted(lambda r: (
                    r.date_of_birth and str(r.date_of_birth) or '',
                ))
            else:
                full_siblings = relative.browse()
            half_siblings = siblings - full_siblings

            relative.sibling_ids = full_siblings.ids
            relative.half_sibling_ids = half_siblings.ids
    
    def _compute_adopted_sibling_ids(self):
        for relative in self:
            parents = relative.father_id | relative.mother_id | relative.adopted_parent_ids
            relative.adopted_sibling_ids = (relative.parent_line_ids.search([
                ('parent_id', 'in', parents.ids),
            ]).mapped('child_id') + parents.child_ids - parents - relative.sibling_ids - relative.step_child_ids - relative).ids
    
    def _compute_step_sibling_ids(self):
        for relative in self:
            relative.step_sibling_ids = (relative.step_parent_ids.child_ids - relative.half_sibling_ids).ids

    def _compute_child_ids(self):
        for relative in self:
            relative.child_ids = self.search([
                '|',
                    ('father_id', '=', relative.id),
                    ('mother_id', '=', relative.id),
            ], order='date_of_birth').ids

            relative.adopted_child_ids = (self.env['relative.parent'].search([
                ('parent_id', '=', relative.id),
            ]).mapped('child_id') - relative.child_ids - relative).ids

            relative.step_child_ids = ((relative.relationship_ids.mapped(lambda relationship: relationship.male_id | relationship.female_id) - relative).child_ids - relative.child_ids - relative).ids

    def _compute_spouse_type(self):
        for relative in self:
            spouse_type = False

            if relative in relative.relationship_ids.male_id:
                spouse_type = 'male'
            if relative in relative.relationship_ids.female_id:
                if spouse_type == 'male':
                    spouse_type = 'mixed'
                else:
                    spouse_type = 'female'

            relative.spouse_type = spouse_type

    def _compute_relationship_ids(self):
        for relative in self:
            relative.relationship_ids = self.env['relative.relationship'].search([
                '|',
                ('male_id', '=', relative.id),
                ('female_id', '=', relative.id),
            ], order='date_of_marriage').ids

    def _set_relationship_ids(self):
        for relative in self:
            old_relationship_ids = self.env['relative.relationship'].search([
                '|',
                    ('male_id', '=', relative.id),
                    ('female_id', '=', relative.id),
            ], order='date_of_marriage')

            (old_relationship_ids - relative.relationship_ids).unlink()

    def _compute_spouse_ids(self):
        for relative in self:
            relationships = self.env['relative.relationship'].search([
                '|',
                    ('male_id', '=', relative.id),
                    ('female_id', '=', relative.id),
                ('divorce_date', '=', False),
                ('status_id.ended', '=', False),
            ])
            relative.spouse_ids = ((relationships.mapped('male_id') | relationships.mapped('female_id')) - relative).ids

    def action_create_relationship_wizard(self):
        self.ensure_one()
        return {
            'name': 'Create Relationship',
            'type': 'ir.actions.act_window',
            'res_model': 'relative.relationship.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def get_parents(self):
        return self.father_id | self.mother_id

    def get_ancestors(self):
        ancestors = self.browse()
        for relative in self:
            immediate_ancestors = relative.get_parents()
            adopted_ancestors = relative.adopted_parent_ids
            ancestors |= immediate_ancestors | adopted_ancestors
            ancestors |= immediate_ancestors.get_ancestors()
        return ancestors

    def get_descendants(self):
        descendants = self.browse()
        for relative in self:
            children = relative.child_ids | relative.adopted_child_ids
            descendants |= children
            descendants |= children.get_descendants()
        return descendants

    def get_relationships(self):
        return self.env['relative.relationship'].search([
            '|',
                ('male_id', 'in', self.ids),
                ('female_id', 'in', self.ids),
        ])

    def generate_family_script(self):
        def _get_parent_char(parent_sex, nth_parnet):
            if nth_parnet > 2:
                return False
            if parent_sex == 'm':
                return 'mXK'[nth_parnet]
            if parent_sex == 'f':
                return 'fYL'[nth_parnet]

        def _get_parent_type_char(parent_reason):
            return {
                'adopted': 'a',
                'foster': 'f',
                'god': 'g',
            }.get(parent_reason, False)

        fs = ''

        tree_complexity = self._context.get('tree_complexity', 'up_down')

        relatives = self
        if tree_complexity == 'everyone':
            relatives |= self.get_ancestors()
            relatives |= relatives.get_descendants()
        elif tree_complexity == 'first_cousins':
            relatives |= self.get_ancestors()
            grandparents = self.get_parents().get_parents()
            relatives |= grandparents.get_descendants()
        elif tree_complexity == 'up_down':
            relatives |= self.get_ancestors() | self.get_descendants()
        else:
            raise UserError(_('You must select a view complexity.'))

        relationships = relatives.get_relationships()
        relatives |= (relationships.mapped('male_id') | relationships.mapped('female_id'))

        for r in relatives:
            relative_str = f'i{r.id}'
            parent_count = {
                'f': 0,
                'm': 0,
            }

            if r.first_name:
                relative_str += f'\tp{r.first_name}'
            
            if r.last_name:
                relative_str += f'\tq{r.last_name}'
            
            if r.sex:
                relative_str += '\tg' + (r.sex == 'male' and 'm' or r.sex == 'female' and 'f' or 'o')
            
            if r.date_of_birth:
                relative_str += '\tb' + r.date_of_birth.strftime('%Y%m%d')
            
            if r.date_of_death:
                relative_str += '\tz1\td' + r.date_of_death.strftime('%Y%m%d')
            
            if r.father_id:
                relative_str += f'\tf{r.father_id.id}\tVb'
                parent_count['f'] += 1
            
            if r.mother_id:
                relative_str += f'\tm{r.mother_id.id}\tVb'
                parent_count['m'] += 1

            if r.sibling_sequence is not False:
                relative_str += f'\tO{r.sibling_sequence}'
            
            for pl in r.parent_line_ids.sorted(lambda pl: pl.reason):
                sex = (r.sex == 'male' and 'f' or r.sex == 'female' and 'm' or False)
                parent_char = _get_parent_char(sex, parent_count[sex])
                if not parent_char:
                    continue

                parent_type_str = ''
                if parent_type_char1 := _get_parent_type_char(pl.reason):
                    parent_type_char0 = 'VWQ'[parent_count[sex]]
                    parent_type_str = f'\t{parent_type_char0}{parent_type_char1}'
                relative_str += f'\t{parent_char}{pl.parent_id.id}{parent_type_str}'
                parent_count[sex] += 1
            
            if current_relationship := r.relationship_ids.filtered(lambda rs: not rs.divorce_date and not rs.status_id.ended and rs.male_id and rs.female_id):
                relative_str += f'\ts{current_relationship[0].mapped(lambda rs: (rs.male_id | rs.female_id) - r).id}'

            fs += relative_str + '\n'
        
        for rs in relationships:
            relationship_str = f'p{rs.male_id.id}\t{rs.female_id.id}\tgr'
            if rs.date_of_marriage:
                relationship_str += f'\tb{rs.date_of_marriage}'
            if rs.marriage_location_id:
                relationship_str += f'\tw{rs.marriage_location_id.display_name}'
            if rs.divorce_date:
                relationship_str += f'\tz{rs.divorce_date}'
            fs += relationship_str + '\n'

        return fs

    def action_pedigree(self):
        self.ensure_one()

        family_script = self.generate_family_script()
        body = {
            'operation': 'temp_view',
            'family': family_script,
            'parent_gen': 15,
        }

        response = requests.post('https://www.familyecho.com/api/', params={'format': 'json'}, data=body)

        if response.ok and (url := response.json().get('url')):
            url = re.sub(r'^http://', 'https://', url)

            return {
                'name': 'Pedigree Chart',
                'type': 'ir.actions.act_window',
                'res_model': 'relative.pedigree.wizard',
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'url': url,
                }
            }
        raise UserError(_('Unable to generate tree.'))
