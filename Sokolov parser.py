import requests

from threading import Thread

from bs4 import BeautifulSoup as bs

from xlwt import Workbook

import json

import time

import base64

from auth_data import sokolov_login, sokolov_password



def get_token():
    base_url = 'https://api.b2b.sokolov.net/ru-ru/login'

    headers = {
        'Authorization': f"Basic {str(base64.b64encode(f'{sokolov_login}:{sokolov_password}'.encode('UTF-8')), 'UTF-8')}"
    }

    access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI2MjQ0NjgiLCJpYXQiOjE1Nzg0OTI2OTgsImV4cCI6MTU3ODU3OTA5OH0.-_7RHiNyYwuxHuwbMApR3FBQkcDgWeTE7kSxznXIoF4'
    #access_token = json.loads(requests.post(base_url, headers = headers).text)['access_token']
    #print(access_token)

    return access_token


def get_data():
    global access_token

    def append_data(page_number):
        nonlocal headers, data

        url = f'https://api.b2b.sokolov.net/ru-ru/catalog/products?page={page_number}'
        print(json.loads(requests.get(url, headers = headers).text))
        products = [product for product in json.loads(requests.get(url, headers = headers).text)['data']
                    if product['attributes']['material'] != 'Золото']

        for product in products:
            if product not in data:
                data.append(product)

    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': f"Bearer {access_token}"
    }

    #url = 'https://api.b2b.sokolov.net/ru-ru/catalog/products'
    url = 'https://api.b2b.sokolov.net/ru-ru/catalog/products?page=1&size=120&filter%5Barticle%5D=110187'
    data = json.loads(requests.get(url, headers = headers).text)
    print(data)
    for page_number in range(1, 54):
        #thread = Thread(target = append_data, args = (page_number,))
        #thread.start()
        #time.sleep(0.1)
        #append_data(page_number)
        pass

    #time.sleep(7)

    with open('Data.json', 'w', encoding = 'UTF-8') as file:
        file.write(json.dumps(data, indent = 4))

    #with open('Data.json', 'r', encoding = 'UTF-8') as file:
    #    data = json.loads(file.read())['data']

    return data


def write_basic_info(sheet):
    sheet.write(0, 0, 'Код_товара')
    sheet.write(0, 1, 'Название_позиции')
    sheet.write(0, 2, 'Описание')
    sheet.write(0, 3, 'Тип_товара')
    sheet.write(0, 4, 'Цена')
    sheet.write(0, 5, 'Валюта')
    sheet.write(0, 6, 'Единица_измерения')
    sheet.write(0, 7, 'Оптовая_цена')
    sheet.write(0, 8, 'Ссылка_изображения')
    sheet.write(0, 9, 'Наличие')
    sheet.write(0, 10, 'Количество')
    sheet.write(0, 11, 'Название_группы')
    sheet.write(0, 12, 'Производитель')
    sheet.write(0, 13, 'Страна_производитель')
    sheet.write(0, 14, 'Скидка')
    sheet.write(0, 15, 'Уникальный_идентификатор')
    sheet.write(0, 16, 'Идентификатор_товара')
    for char_num in range(20):
        sheet.write(0, char_num * 3 + 17, 'Название_Характеристики')
        sheet.write(0, char_num * 3 + 18, 'Измерение_Характеристики')
        sheet.write(0, char_num * 3 + 19, 'Значение_Характеристики')


filename = 'Data.xls'
sheetname = 'sheet'
file = Workbook()
file.default_style.font.height = 20 * 36
message_was_shown = False
while True:
    try:
        sheet = file.add_sheet(sheetname)
        write_basic_info(sheet)
        file.save(filename)
        break
    except:
        if not message_was_shown:
            print(f'Please, close "{filename}"\n\nPress enter to exit')
            message_was_shown = True

        time.sleep(1)


access_token = get_token()

print(f'Access token: {access_token}')

data = get_data()
print(len(data))
for product in data[:10]:
    print(product['attributes']['material'])