import base64
import binascii
import logging
import re
import requests
import xlrd
from datetime import datetime
import phonenumbers
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)
RELATIVE = self.env['relative']
TITLE = self.env['res.partner.title']
TRIBE = self.env['relative.tribe']
FAMILY = self.env['relative.family']
ALIAS_TYPE = self.env['relative.alias.type']
ALIAS = self.env['relative.alias']
COUNTRY = self.env['res.country']
STATE = self.env['res.country.state']
CITY = self.env['relative.city']
CITY_NAME = self.env['relative.city.name']
ADDRESS = self.env['relative.address']
ADDRESS_LINE = self.env['relative.address.resident']

relative_map = {}
country_map = {
    'USA': 'United States',
    'Test Country OM': 'United States',
    'UK': 'United Kingdom',
    'Uk': 'United Kingdom',
    'uK': 'United Kingdom',
    'London': 'United Kingdom', # this is a mistake
    'Palestine': 'State of Palestine',
    'Russia': 'Russian Federation',
    'Austria-Hungary': ('Austria-Hungary', 'AHHH'),
    'Czechosolvakia': ('Czechoslovakia', 'CSHH'),
    'Czechoslovakia': ('Czechoslovakia', 'CSHH'),
    'BSSR': ('Byelorussian Soviet Socialist Republic', 'BYAA'),
    'USSR': ('Union of Soviet Socialist Republics', 'SUHH'),
    'West Germany': ('West Germany', 'DEDE'),
    'Yugoslavia': ('Yugoslavia', 'YUCS'),
    'Austalia': 'Australia',
    'Holland': 'Netherlands',
}
state_map = {}

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
    if not name:
        return False
    _logger.info(f'state map: {name}: {state_map.get(name)}')
    state_name = state_map.get(name) or name
    state_code = name
    state_id = STATE.search([
        '|',
            ('name', '=', state_name),
            ('code', '=', state_code),
        ('country_id', '=', country.id)
    ])
    _logger.info(f'found {state_id}')
    if not state_id:
        state_id = STATE.create({
            'name': state_name,
            'code': state_code,
            'country_id': country.id,
        })
    return state_id

def get_city(name, state_id, country_id):
    city_name_id = CITY_NAME.search([
        ('name', '=', name),
        ('country_id', '=', country_id.id),
    ])
    _logger.info(f'city name: {name} => {city_name_id}, {state_id}, {country_id.name}')
    if not city_name_id:
        city_name_id = CITY_NAME.create({
            'name': name,
            'state_id': state_id and state_id.id,
            'country_id': country_id.id,
        })

    return city_name_id

def populate_city_names(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    def get_create_city_name(name, state_id, country_id, note, city_id=False):
        city_name_id = get_city(name, state_id, country_id)
        
        _logger.info(f'city id: {city_id}')
        if not city_id:
            city_id = CITY.search([
                ('name_id', '=', city_name_id.id),
            ])

            if not city_id:
                city_id = CITY.create({
                    'name_id': city_name_id.id,
                    'state_id': city_name_id.state_id.id,
                    'country_id': country_id.id,
                    'note': note,
                })

        _logger.info(f'city id: {city_id}')
        if city_id:
            _logger.info(f'cityname: {city_name_id} city id: {city_name_id.city_id} -> {city_id}')
            city_id.name_ids |= city_name_id

        return city_name_id

    germany_id = COUNTRY.search([('code', '=', 'DE')])
    hungary_id = COUNTRY.search([('code', '=', 'HU')])
    czechia_id = COUNTRY.search([('code', '=', 'CZ')])
    russia_id = COUNTRY.search([('code', '=', 'RU')])

    for row in range(sheet.nrows):
        if row == 0:
            continue
        
        name0 = get_cell(row, 0)
        note = get_cell(row, 1)
        german_name = get_cell(row, 2)
        hungarian_name = get_cell(row, 3)
        czech_name = get_cell(row, 4)
        current_name = get_cell(row, 5)
        current_state = get_cell(row, 6)
        current_country = get_cell(row, 7)

        country_id = COUNTRY.search([
            ('name', '=', current_country)
        ])
        _logger.info(f'{current_state}, {country_id.name}, {row}')
        state_id = get_state(current_state, country_id)
        current_name_id = get_create_city_name(current_name, state_id, country_id, note)

        german_name_id = False
        hungary_name_id = False
        czech_name_id = False
        russia_name_id = False
        if german_name:
            german_name_id = get_create_city_name(german_name, False, germany_id, False, current_name_id.city_id)
        if hungarian_name:
            hungary_name_id = get_create_city_name(hungarian_name, False, hungary_id, False, current_name_id.city_id)
        if czech_name:
            if len(russian_name := czech_name.split(' (Russian)')) > 1:
                russia_name_id = get_create_city_name(russian_name[0], False, russia_id, False, current_name_id.city_id)
            else:
                czech_name_id = get_create_city_name(czech_name, False, czechia_id, False, current_name_id.city_id)

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

def get_address(street, city, state, zipcode, country, address_type, relative_id=False, note=False):
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
            ('code', '=', country_code or country_name),
    ])

    if not country_id and country_name and country_code:
        country_id = COUNTRY.create({
            'name': country_name,
            'code': country_code,
        })
    
    if not country_id:
        _logger.info([street, city, state, zipcode, country, address_type, relative_id, note, country_id, country_name, country_code])
        raise 'Big error'
    
    state_id = False
    _logger.info(state)
    if state:
        state_id = get_state(state, country_id)
    
    city_name_id = False
    if city:
        city_name_id = get_city(city, state_id, country_id)

        if city_name_id and not city_name_id.state_id and state_id:
            city_name_id.state_id = state_id.id

    if not city_name_id:
        city_name_id = False
    # _logger.info(f'{city_name_id}, {city_name_id.ids}, {city_name_id.ids == []}')
    address_id = ADDRESS.search([
        ('street', '=', street),
        ('city_name_id', '=', city_name_id and city_name_id.id),
        ('state_id', '=', state_id and state_id.id),
        ('zip', '=', zipcode),
        ('country_id', '=', country_id.id),
    ] + ([
        ('note', '=', False),
    ] if not note else [
        ('note', 'ilike', note),
    ]))

    if not address_id:
        address_id = ADDRESS.create({
            'street': street,
            'city_name_id': city_name_id and city_name_id.id,
            'state_id': state_id and state_id.id,
            'zip': zipcode,
            'country_id': country_id.id,
            'note': note,
        })

    if relative_id:
        ADDRESS_LINE.create({
            'relative_id': relative_id.id,
            'address_id': address_id.id,
            'address_type': address_type,
        })

    return address_id

def get_datetime(date: str):
    if date == '0':
        return False, False
    try:
        return datetime.strptime(date,'%Y%m%d'), False
    except:
        try:
            return datetime.strptime(date,'%Y%m00'), True
        except:
            return datetime.strptime(date,'%Y0000'), True

def compare_hebrew_date(date: datetime, hebrew_date: str) -> bool:
    request_url = f'https://www.hebcal.com/converter?cfg=json&g2h=1&strict=1&date={date.strftime("%Y-%m-%d")}'
    _logger.info(f'requesting, {date}')
    response = requests.get(request_url).json()
    hebrew_day = int(hebrew_date[-2:])
    res_hebrew_day = response.get('hd')
    if res_hebrew_day == hebrew_day:
        return False
    if res_hebrew_day + 1 == hebrew_day:
        return True

    request_url = request_url[:-2] + str(int(request_url[-2:]) + 1).zfill(2)
    _logger.info('requesting?')
    _logger.info(request_url)
    response = requests.get(request_url).json()
    if response.get('hd') == hebrew_day:
        return True

    raise ValidationError(f'What day is it man?\n\n{date} {hebrew_date} {response.get("hd")} != {hebrew_day}')

def get_sex(nice):
    return {
        'M': 'male',
        'F': 'female',
    }.get(nice)

def import_persons(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    def search_create_record(model, name):
        return model.search([('name', '=', name)]) or model.create({
            'name': name,
        })

    def get_create_alias(relative, name, alias_type):
        if not name:
            return ALIAS
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
    
    def get_create_record(model, name):
        if not name:
            return model
        record_id = model.search([('name', '=', name)])
        if not record_id:
            record_id = model.create({
                'name': name,
            })
        return record_id

    output = RELATIVE
    error_log = []

    alias_type_jewish = search_create_record(ALIAS_TYPE, 'Jewish')
    alias_type_nickname = search_create_record(ALIAS_TYPE, 'Nickname')

    for row in range(sheet.nrows):
        if row == 0:
            continue
        # if not (680 < row < 684):
        #     continue

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
        phone_last7 = get_cell(row, 20)
        blood_related = get_cell(row, 21)
        sex = get_cell(row, 22)
        alive = get_cell(row, 23)
        head_of_household = get_cell(row, 24)
        has_picture = get_cell(row, 25)
        living_with = get_cell(row, 26)
        title_code = get_cell(row, 27)
        shcode = get_cell(row, 28)
        # I don't have this data \/
        # status = get_cell(row, 29)

        # Start importing
        family = FAMILY.search([('code', '=', family_code)]) or FAMILY.create({
            'name': family_code,
            'code': family_code,
        })

        relative_id = RELATIVE.search([
            ('family_id', '=', family.id),
            ('family_number', '=', relative_number),
        ]) or RELATIVE.create({
            'family_id': family.id,
            'family_number': relative_number,
        })

        # process date of birth

        date_of_birth, approximate_dob = get_datetime(date_of_birth)
        try:
            born_at_night = date_of_birth and not approximate_dob and compare_hebrew_date(date_of_birth, jewish_date_of_birth)
        except Exception as error:
            error_log.append(error)
            born_at_night = False
        phone = phone_country_code and phone_area_code and phone_last7 and f'+{phone_country_code}{phone_area_code}{phone_last7}'
        try:
            phone_number = phone and phonenumbers.format_number(phonenumbers.parse(phone), phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except Exception as error:
            if family.code == 'GR' and relative_number == 127:
                phone_number = '+42 5793937'
            else:
                error_log.append(f'{phone}, {error}')
                phone_number = False

        vals = {
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date_of_birth,
            'date_of_birth_approximate': approximate_dob,
            'birth_after_sunset': born_at_night,
            'mobile_phone': phone_number,
            'sex': get_sex(sex),
            'note': f'Lives with: {living_with}\nMarried: {married}\nLiving: {alive}\nBlood related: {blood_related}\nHoH: {head_of_household}\nNeed to import picture: {has_picture}',
        }

        relative_id.write(vals)

        alias_jewish_name = get_create_alias(relative_id, jewish_name, alias_type_jewish)
        alias_nickname = get_create_alias(relative_id, nickname, alias_type_nickname)
        address_of_birth = get_address(False, city_of_birth, state_of_birth, False, country_of_birth, 'birthplace', relative_id=relative_id)
        address_of_residence = get_address(street_of_residence, city_of_residence, state_of_residence, zipcode_of_residence, country_of_residence, 'home', relative_id=relative_id)

        relative_id.title_id = get_create_record(TITLE, title_code)
        relative_id.tribe_id = get_create_record(TRIBE, shcode)
        
        # Use this to populate the map
        relative_id = get_relative(family_code, relative_number)
        output |= relative_id

    return error_log


def allocate_parent_child(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    # def get_relative(family_code, family_number):
    #     return RELATIVE.search([
    #         ('family_id.code', '=', family_code),
    #         ('family_number', '=', family_number),
    #     ])

    output = []

    for row in range(sheet.nrows):
        if row == 0:
            continue

        family_code = get_cell(row, 0)
        family_number = get_cell(row, 1)
        relative_id = get_relative(family_code, family_number)

        if not relative_id:
            _logger.info('relative not found')
            output.append([family_code, family_number, row])
        
        parent_type = get_cell(row, 2)
        parent_type = parent_type == 'M' and 'mother_id' or parent_type == 'F' and 'father_id' or None
        if parent_type is None:
            _logger.info('unsure parent type')
            output.append([parent_type, row])
            continue

        parent_family_code = get_cell(row, 4)
        parent_family_number = get_cell(row, 5)
        parent_id = parent_family_code and get_relative(parent_family_code, parent_family_number)
        parent_name = not parent_id and get_cell(row, 3)
        if parent_name and not getattr(relative_id, parent_type):
            parent_id = RELATIVE.create({
                'first_name': parent_name,
                'note': 'Created from Parent-Child Sheet.'
            })
        
        if parent_id and hasattr(type(parent_id), '_name'):
            setattr(relative_id, parent_type, parent_id.id)

    return output

def process_aliases(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    output = []

    for row in range(sheet.nrows):
        if row == 0:
            continue

        family_code = get_cell(row, 0)
        family_number = get_cell(row, 1)
        relative_id = get_relative(family_code, family_number)

        if not relative_id:
            _logger.info('relative not found')
            output.append([family_code, family_number, row])

        alias_type = get_cell(row, 2)
        alias_type_id = ALIAS_TYPE.search([
            ('name', '=', alias_type),
        ]) or ALIAS_TYPE.create({
            'name': alias_type,
        })

        alias = get_cell(row, 3)
        alias_note = get_cell(row, 4)
        if not alias:
            continue

        alias_id = ALIAS.search([
            ('relative_id', '=', relative_id.id),
            # ('alias_type_ids', 'in', alias_type_id.ids),
            ('name', '=', alias),
            ('note', '=', alias_note),
        ])

        if alias_id:
            alias_id.alias_type_ids |= alias_type_id
        else:
            ALIAS.create({
                'relative_id': relative_id.id,
                'alias_type_ids': alias_type_id.ids,
                'name': alias,
                'note': alias_note,
            })

    return output

def fill_named_after(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    output = []
    pattern = re.compile(r'\b[A-Z]{2}\d{1,4}[.,;:!]*\b')

    for row in range(sheet.nrows):
        if row == 0:
            continue

        family_code = get_cell(row, 0)
        family_number = get_cell(row, 1)
        relative_id = get_relative(family_code, family_number)

        name_orig_description = relative_id.name_orig_description or ''
        add_name_orig_description = get_cell(row, 3)
        relative_id.name_orig_description = (name_orig_description + ' ' + add_name_orig_description).strip()
        
        ancestors = pattern.findall(add_name_orig_description)
        for ancestor in ancestors:
            name_orig_id = get_relative(ancestor[:2], ancestor[2:])
            if name_orig_id:
                relative_id.name_orig_ids |= name_orig_id
            else:
                if not relative_id.note:
                    relative_id.note = ''
                relative_id.note += f'Mismatched named after family code/ID: {ancestor}'
                output.append(ancestor)

    return output

def add_emails(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    output = []

    for row in range(sheet.nrows):
        if row == 0:
            continue

        family_code = get_cell(row, 0)
        family_number = get_cell(row, 1)
        relative_id = get_relative(family_code, family_number)

        email_name = get_cell(row, 2)
        email_domain = get_cell(row, 3)
        if email_domain:
            relative_id.email = f'{email_name}@{email_domain}'.lower()

    return output

def process_deaths(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    output = []

    for row in range(sheet.nrows):
        if row == 0:
            continue

        family_code = get_cell(row, 0)
        family_number = get_cell(row, 1)
        relative_id = get_relative(family_code, family_number)

        city_of_death = get_cell(row, 2)
        state_of_death = get_cell(row, 3)
        country_of_death = get_cell(row, 4)

        date_of_death = get_cell(row, 5)
        jewish_date_of_death = get_cell(row, 6)
        
        city_of_burial = get_cell(row, 7)
        state_of_burial = get_cell(row, 8)
        country_of_burial = get_cell(row, 9)
        note0 = get_cell(row, 10)
        note1 = get_cell(row, 11)
        note = (note0 or '') + (note1 or '')
        
        date_of_death, approximate_dod = get_datetime(date_of_death)
        try:
            died_at_night = date_of_death and not approximate_dod and compare_hebrew_date(date_of_death, jewish_date_of_death)
        except Exception as error:
            output.append(error)
            died_at_night = False

        relative_id.write({
            'date_of_death': date_of_death,
            'date_of_death_approximate': approximate_dod,
            'death_after_sunset': died_at_night,
        })

        _logger.info(row)
        if country_of_death:
            get_address(False, city_of_death, state_of_death, False, country_of_death, 'death', relative_id=relative_id)
        if country_of_burial:
            get_address(False, city_of_burial, state_of_burial, False, country_of_burial, 'burial', relative_id=relative_id, note=note)

    return output


def append_notes(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    output = []

    for row in range(sheet.nrows):
        if row == 0:
            continue

        family_code = get_cell(row, 0)
        family_number = get_cell(row, 1)
        relative_id = get_relative(family_code, family_number)

        if not relative_id.note:
            relative_id.note = ''
        relative_id.note += get_cell(row, 3)

    return output

def create_marriages(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    def _get_marriage_status(status):
        status_id = self.env['relative.relationship.status'].search([('name', '=', status)])

        if not status_id:
            status_id = self.env['relative.relationship.status'].create({
                'name': status,
            })
        
        return status_id


    output = []

    for row in range(sheet.nrows):
        if row == 0:
            continue

        _logger.info(row)

        relative0_id = get_relative(get_cell(row, 0), get_cell(row, 1))
        relative1_id = get_relative(get_cell(row, 9), get_cell(row, 10))

        if relative0_id.sex == 'male':
            male_id = relative0_id
            female_id = relative1_id
        elif relative1_id.sex == 'male':
            male_id = relative1_id
            female_id = relative0_id
        else:
            output.append(f'wat, {relative0_id} & {relative1_id}')
            male_id = relative0_id
            female_id = relative1_id

        city_of_marriage = get_cell(row, 4)
        state_of_marriage = get_cell(row, 5)
        country_of_marriage = get_cell(row, 6)
        date_of_marriage = get_cell(row, 7)
        jewish_date_of_marriage = get_cell(row, 8)
        status = get_cell(row, 11)

        address_of_marriage = get_address(False, city_of_marriage, state_of_marriage, False, country_of_marriage, 'marriage')
        status_id = _get_marriage_status(status)


        date_of_marriage, approximate_dom = get_datetime(date_of_marriage)
        try:
            married_at_night = date_of_marriage and not approximate_dom and compare_hebrew_date(date_of_marriage, jewish_date_of_marriage)
        except Exception as error:
            output.append(error)
            married_at_night = False

        marriage_id = self.env['relative.relationship'].search([
            ('male_id', '=', male_id.id),
            ('female_id', '=', female_id.id),
            ('date_of_marriage', '=', date_of_marriage and date_of_marriage.strftime('%Y-%m-%d %H:%M:%S')),
            ('date_of_marriage_approximate', '=', approximate_dom),
            ('marriage_after_sunset', '=', married_at_night),
            ('status_id', '=', status_id.id),
            ('marriage_location_id', '=', address_of_marriage and address_of_marriage.id),
        ])

        if not marriage_id:
            marriage_id = self.env['relative.relationship'].create({
                'male_id': male_id.id,
                'female_id': female_id.id,
                'date_of_marriage': date_of_marriage and date_of_marriage.strftime('%Y-%m-%d %H:%M:%S'),
                'date_of_marriage_approximate': approximate_dom,
                'marriage_after_sunset': married_at_night,
                'status_id': status_id.id,
                'marriage_location_id': address_of_marriage and address_of_marriage.id,
            })


    return output



attachment = self.env['ir.attachment'].browse(20)  # change id before running
wb = xlrd.open_workbook(file_contents=binascii.a2b_base64(attachment.datas))
errors = []

state_code_sheet = wb.sheet_by_index(9)
populate_state_name_map(state_code_sheet)

person_sheet = wb.sheet_by_index(0)
errors += import_persons(person_sheet)

city_sheet = wb.sheet_by_index(8)
populate_city_names(city_sheet)

parent_child_sheet = wb.sheet_by_index(1)
errors += allocate_parent_child(parent_child_sheet)

alias_sheet = wb.sheet_by_index(3)
errors += process_aliases(alias_sheet)

named_after_sheet = wb.sheet_by_index(4)
errors += fill_named_after(named_after_sheet)

spouse_sheet = wb.sheet_by_index(5)
errors += create_marriages(spouse_sheet)

email_sheet = wb.sheet_by_index(6)
errors += add_emails(email_sheet)

death_sheet = wb.sheet_by_index(7)
errors += process_deaths(death_sheet)

notes_sheet = wb.sheet_by_index(10)
errors += append_notes(notes_sheet)

result = errors

_logger.info('Process finished successfully!')
