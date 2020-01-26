import requests, json, time, base64

from threading import Thread

from bs4 import BeautifulSoup as bs

from xlwt import Workbook

from auth_data import sokolov_login, sokolov_password


def create_thread(function, args = ()):
    print('Thread created')

    while True:
        try:
            Thread(target = function, args = args).start()
            break
        except:
            time.sleep(3)


def get_token():
    base_url = 'https://api.b2b.sokolov.net/ru-ru/login'

    headers = {
        'Authorization': f"Basic {str(base64.b64encode(f'{sokolov_login}:{sokolov_password}'.encode('UTF-8')), 'UTF-8')}"
    }

    access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJhODFmNzg5Yi1lY2QyLTQ0NWUtOTY4ZS0zOGMyZDA3MDZiOTEiLCJsb2dpbiI6ImlkNWRiMmYzN2JlM2JmYyIsImlhdCI6MTU4MDA2MzU2MCwiZXhwIjoxNTgwMTQ5OTYwfQ.WqOSbRLEfZgGNlBXGT_kt7GAzicdhOLPsrZ-d-61e1Q'
    # access_token = json.loads(requests.post(base_url, headers = headers).text)['access_token']

    return access_token


def get_and_filter_data():

    def request_to_page(page_number):
        global access_token
        nonlocal all_data, all_articuls, page_flags

        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': f'Bearer {access_token}',
            # 'filter': '{"material":{"nin":["Золото"]}}'
        }

        response_text = requests.get(f'https://api.b2b.sokolov.net/ru-ru/catalog/products?page={page_number}', headers = headers).text
        # print(json.dumps(json.loads(response_text), indent = 4))

        data = json.loads(response_text)
        for product in data['data']:
            if product['attributes']['article'] not in all_articuls and product['attributes']['material'] != 'Золото':
                all_articuls.append(product['attributes']['article'])
                all_data.append(product)

        try:
            page_flags[page_number] = True
        except:
            pass

        return data


    all_articuls = []
    all_data = []
    number_of_pages = int(request_to_page(1)['links']['last']['href'].split('=')[-1])
    # number_of_pages = 10
    page_flags = [None for i in range(number_of_pages + 1)]
    for page_number in range(2, number_of_pages + 1):
        page_flags[page_number] = False
        print(f'Parsing page number {page_number}\nProducts found already: {len(all_data)}\n')
        # create_thread(request_to_page, (page_number,))
        request_to_page(page_number)

    while False in page_flags:
        time.sleep(5)

    with open('Data.json', 'w', encoding = 'UTF-8') as file:
        file.write(json.dumps(all_data, indent = 4))

    return all_data


access_token = get_token()

print(f'Access token: {access_token}')

# data = get_and_filter_data()
with open('Data.json', 'r', encoding = 'UTF-8') as file:
    data = json.loads(file.read())

print(len(data))
for product in data[:10]:
    print(product['attributes']['material'])