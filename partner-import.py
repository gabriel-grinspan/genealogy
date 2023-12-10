import base64
import binascii
import logging
import re
import requests
import xlrd


_logger = logging.getLogger(__name__)
self = self


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


def import_partners(sheet):
    def get_cell(row, col):
        return get_cell_with_sheet(sheet, row, col)

    for row in range(sheet.nrows):
        if row == 0:
            continue

        name = get_cell(row, 4)


attachment = self.env['ir.attachment'].browse(123)  # change id before running
wb = xlrd.open_workbook(file_contents=binascii.a2b_base64(attachment.datas))
partner_sheet = wb.sheet_by_index(0)
