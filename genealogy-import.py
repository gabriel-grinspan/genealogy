import base64
import binascii
import logging
import re
import requests
import xlrd


_logger = logging.getLogger(__name__)
RELATIVE = self.env['relative']
FAMILY = self.env['relative.family']
ALIAS_TYPE = self.env['relative.alias.type']
ALIAS = self.env['relative.alias']
COUNTRY = self.env['res.country']
STATE = self.env['res.country.state']
CITY = self.env['reltive.city']
CITY_NAME = self.env['reltive.city.name']

relative_map = {}
country_map = {
    'USA': 'United States',
    'UK': 'United Kingdom',
    'uK': 'United Kingdom',
    'London': 'United Kingdom', # this is a mistake
    'Palestine': 'State of Palestine',
    'Russia': 'Russian Federation',
    'Austria-Hungary': ('Austria-Hungary', 'AHHH'),
    'Czechoslovakia': ('Czechoslovakia', 'CSHH'),
    'BSSR': ('Byelorussian Soviet Socialist Republic', 'BYAA'),
    'USSR': ('Union of Soviet Socialist Republics', 'SUHH'),
    'West Germany': ('West Germany', 'DEDE'),
}
state_map = {}
city_map = {}

def get_cell_with_sheet(sheet, row, col):
    cell = sheet.cell(row, col)
    if cell.ctype in [0, 5, 6]:
        return ''
    elif cell.ctype == 1:
        return cell.value.strip()
    elif cell.ctype == 2:
        if cell.value == int(cell.value):
            return str(int(cell.value))
        return str(cell.value)
    elif cell.ctype == 3:
        return xlrd.xldate.xldate_as_datetime(cell.value, 0).strftime('%Y-%m-%d %H:%M:%S')
    elif cell.ctype == 4:
        return 'TRUE' if cell.value == 1 else 'FALSE'
    else:
        return str(cell.value).strip()

def populate_state_name_map(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    for row in range(sheet.nrows):
        if row == 0:
            continue
        
        state_code = get_cell(row, 0)
        state_name = get_cell(row, 1)
        state_map[state_code] = state_name

def get_state(name, country):
    state_name = state_map.get(name)
    state_code = name
    state_id = STATE.search([
        '|',
            ('name', '=', state_name),
            ('code', '=', state_code),
        ('country_id', '=', country.id)
    ])

    if not state_id:
        state_id = STATE.create({
            'name': state_name,
            'code': state_code,
            'country_id': country.id,
        })

def populate_city_name_map(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    def get_create_city_name(name, state_id, country_id, note, current_city_name):
        city_name_id = CITY_NAME.search([
            ('name', '=', name),
            ('state_id', '=', state_id and state_id.id or False),
            ('country_id', '=', country_id.id),
        ])
        if not city_name_id:
            city_name_id = CITY_NAME.create({
                'name': name,
                'state_id': state_id and state_id.id or False,
                'country_id': country_id.id,
            })
        
        if not current_city_name:
            city_id = CITY.search([
                ('name_id', '=', city_name_id.id),
            ])
            vals = {
                'name_id': city_name_id.id,
                'state_id': state_id and state_id.id or False,
                'country_id': country_id.id,
                'note': note
            }
            if not city_id:
                city_id = CITY.create(vals)
            else:
                city_id.write(vals)
        
        return city_name_id

    for row in range(sheet.nrows):
        if row == 0:
            continue
        
        name0 = get_cell(row, 0)
        note = get_cell(row, 1)
        name1 = get_cell(row, 2)
        name2 = get_cell(row, 3)
        name3 = get_cell(row, 4)
        current_name = get_cell(row, 5)
        current_state = get_cell(row, 6)
        current_country = get_cell(row, 7)

        country_id = COUNTRY.search([
            ('name', '=', current_country)
        ])
        state_id = get_state(current_state, country_id)

        current_city = get_create_city_name(current_name, state_id, country_id, note, False)
        # TODO
        city0 = get_create_city_name(current_name, False, None, note, city_name_id.city_id)
        city1 = get_create_city_name(current_name, False, None, note, city_name_id.city_id)
        city2 = get_create_city_name(current_name, False, None, note, city_name_id.city_id)
        city3 = get_create_city_name(current_name, False, None, note, city_name_id.city_id)

def get_city(name):
    pass

def get_relative(family_code, relative_number):
    relative_code = family_code+relative_number
    relative = relative_map.get((relative_code))
    if not relative:
        relative = RELATIVE.search([
            ('family_id.code', '=', family_code),
            ('family_number', '=', relative_number),
        ])
        relative_map[relative_code] = relative
    return relative

def get_address(street, city, state, zipcode, country, address_type):
    if not country:
        return False

    country_name = country_map.get(country) or country
    country_code = ''
    if type(country_name) == tuple:
        country_code = country_name[1]
        country_name = country_name[0]
    
    country_id = COUNTRY.search([
        '|',
            ('name', '=', country_name),
            ('code', '=', country_code),
    ])

    if not country_id and country_name and country_code:
        country_id = COUNTRY.create({
            'name': country_name,
            'code': country_code,
        })
    
    if not country_id:
        raise 'Big error'
    
    state_id = False
    if state:
        state_id = get_state(state, country_id)
    
    city_id = False
    if city:
        city_id = get_city(city)


def import_persons(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    def search_create_record(model, name):
        return model.search([('name', '=', name)]) or model.create({
            'name': name,
        })

    def get_create_alias(relative, name, alias_type):
        if relative:
            domain = [
                ('name', '=', name),
                ('alias_type_ids', 'in', alias_type.ids),
                ('relative_id', '=', relative.id)
            ]
            alias = ALIAS.search(domain)
            if alias:
                return alias
        return ALIAS.create({
            'name': name,
            'alias_type_ids': alias_type.ids,
            'relative_id': relative.id,
        })

    output = RELATIVE

    alias_type_jewish = search_create_record(ALIAS_TYPE, 'Jewish')
    alias_type_nickname = search_create_record(ALIAS_TYPE, 'Nickname')

    for row in range(sheet.nrows):
        if row == 0:
            continue

        # variable name each column because nobody can manage this otherwise
        family_code = get_cell(row, 0)
        relative_number = get_cell(row, 1)
        # generation_number = get_cell(row, 2) 
        first_name = get_cell(row, 3)
        last_name = get_cell(row, 4)
        jewish_name = get_cell(row, 5)
        nickname = get_cell(row, 6)
        city_of_birth = get_cell(row, 7)
        state_of_birth = get_cell(row, 8)
        country_of_birth = get_cell(row, 9)
        date_of_birth = get_cell(row, 10)
        jewish_date_of_birth = get_cell(row, 11)
        married = get_cell(row, 12)
        street_of_residence = get_cell(row, 13)
        city_of_residence = get_cell(row, 14)
        state_of_residence = get_cell(row, 15)
        zipcode_of_residence = get_cell(row, 16)
        country_of_residence = get_cell(row, 17)
        phone_country_code = get_cell(row, 18)
        phone_area_code = get_cell(row, 19)
        phone_last8 = get_cell(row, 20)
        blood_related = get_cell(row, 21)
        sex = get_cell(row, 22)
        # alive = get_cell(row, 23)
        head_of_household = get_cell(row, 24)
        has_picture = get_cell(row, 25)
        living_with = get_cell(row, 26)
        # I don't have this data \/
        # title_code = get_cell(row, 27)
        # shcode = get_cell(row, 28)
        # status = get_cell(row, 29)

        # Start importing
        relative_id = get_relative(family_code, relative_number)
        family = FAMILY.search([('code', '=', family_code)]) or FAMILY.create({
            'name': family_code,
            'code': family_code,
        })

        vals = {
            'family_id': family.id,
            'family_number': relative_number,
            'first_name': first_name,
            'last_name': last_name,
        }

        if not relative_id:
            relative_id = relative_id.create(vals)
        else:
            relative_id.write(vals)

        alias_jewish_name = get_create_alias(relative_id, jewish_name, alias_type_jewish)
        alias_nickname = get_create_alias(relative_id, nickname, alias_type_nickname)
        
        output |= relative_id

    return output


attachment = self.env['ir.attachment'].browse(215)  # change id before running
wb = xlrd.open_workbook(file_contents=binascii.a2b_base64(attachment.datas))
state_code_sheet = wb.sheet_by_index(9)
populate_state_name_map(state_code_sheet)


person_sheet = wb.sheet_by_index(0)

result = import_persons(person_sheet)
