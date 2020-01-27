import requests, json, time, base64, jinja2, xlwt

from threading import Thread

from bs4 import BeautifulSoup as bs

from xlwt import Workbook

from transliterate import translit

from auth_data import sokolov_login, sokolov_password


class SokolovProduct():
    objects = []

    def __init__(self, data):
        global group_identifiers_data

        data = data['attributes']

        self.chars = {}
        self.product_identifier = self.articul = data['article']
        self.name = data['title']

        self.quantity = 0
        if data['has-sizes']:
            self.sizes = data['sizes']
            if len(['lol' for size in self.sizes if size['balance']['hint'].lower() != 'нет на складе']) != 0:
                self.quantity = 1
            self.sizes = [size['size'].replace('р', '').replace('см', '').replace('.', '').strip()\
                          for size in self.sizes]
            self.name += ' размеры ' + ' '.join(self.sizes)

        if data['has-complect']:
            self.name += ' - есть комплект'

        self.attached_products = data['complect-products']

        try:
            self.price = 3 * data['trade-price']
        except TypeError:
            self.quantity = 0

        self.images = data['photos']
        self.images.append(data['photo'])
        self.brand = 'SOKOLOV'

        group_name_replace = {
            'Кресты': 'Крест',
            'Ложки': 'Ложка',
            'Вилки': 'Вилка',
            'Иконки': 'Религия',
            'Шнуры декоративные': 'Шнуры',
            'Сувениры декоративные': 'Сувениры',
            'Пирсинги': 'Пирсинг',
            'Кольца обручальные': 'Обручальные кольца',
            'Зажимы для галстука': 'Аксессуары',
            'Брелоки': 'Аксессуары',
            'Подсвечник': 'Аксессуары',
            # 'Погремушки': 'Крест',##############################################
            # 'Пустышки': 'Крест',##############################################
            # 'Кресты': 'Крест',##############################################
            # 'Кресты': 'Крест',##############################################
            # 'Кресты': 'Крест',##############################################
            '': 'Посуда',
            'Поильники': 'Посуда',
            'Кружки': 'Посуда',
            'Фужеры': 'Столовое серебро',
            'Стаканы': 'Столовое серебро',
            'Рюмки': 'Столовое серебро',
            'Стопки': 'Столовое серебро',
            # 'Стаканы': 'Столовое серебро',
            'Бокалы': 'Столовое серебро'
        }
        try:
            self.group_name = group_name_replace[data['category']]
        except:
            self.group_name = data['category']
        try:
            self.group_identifier = group_identifiers_data[self.group_name.lower()]
        except:
            self.group_identifier = translit(self.group_name.lower(), reversed = True)
            group_identifiers_data[self.group_name.lower()] = self.group_identifier
        self.marker = ''

        if self.quantity == 0 or 'бижутерия' in self.name.lower() + self.group_name.lower() or data['material'] != 'Серебро':
            del self
            return
        elif data['has-sizes']:
            self.chars['Наличие, размеры в России'] = '|'.join(self.sizes)
        else:
            self.chars['Наличие, размеры в России'] = 'Да'

        collections_replace = {
            'sokolov-baby': 'Детская',
            'sokolov-home': 'Дом',
            'wedding': 'Свадьба',
            'just': 'Только ты',
            'just-you': 'Только ты'
        }
        try:
            if len(data['collections']) != 0:
                self.chars['Товарная категория'] = '|'.join([collections_replace[collection['collection']['slug']]\
                                                             for collection in data['collections']])
        except:
            pass
        try:
            for prop in data['props']['proportions']:
                self.chars[prop['name']] = prop['value']
        except:
            pass

        self.chars['Проба'] = data['material'] + ' ' + data['probe']

        if len(data['inserts']) != 0:
            inserts = []
            for insert in data['inserts']:
                if insert['name'] not in inserts:
                    inserts.append(insert['name'])
            self.chars['Вставка/камень'] = '|'.join(inserts)

        plating_replace = {
            'Родаж': 'Родирование'
        }
        try:
            self.chars['Покрытие'] = plating_replace[data['material-plating']]
        except:
            self.chars['Покрытие'] = data['material-plating']

        self.__class__.objects.append(self)


    def render_template(self):
        global templateEnv

        template = templateEnv.get_template('Description.html')
        output_text = template.render(product_articul = self.articul,
                                      attached_products = self.attached_products)

        return output_text


def create_thread(function, args = ()):
    print('Thread created')

    while True:
        try:
            Thread(target = function, args = args).start()
            break
        except:
            time.sleep(3)


def write_to_excel():
    global description_data, no_desc_articuls

    products = SokolovProduct.objects

    print(f'Products parsed: {len(products)}')


    filename = 'Data.xls'
    sheetname = 'Sheet'
    excel_file = xlwt.Workbook()
    sheet = excel_file.add_sheet(sheetname)

    sheet.write(0, 0, 'Код_товара')
    sheet.write(0, 1, 'Название_позиции')
    sheet.write(0, 2, 'Поисковые_запросы')
    sheet.write(0, 3, 'Описание')
    sheet.write(0, 4, 'Тип_товара')
    sheet.write(0, 5, 'Цена')
    sheet.write(0, 6, 'Валюта')
    sheet.write(0, 7, 'Единица_измерения')
    sheet.write(0, 8, 'Количество')
    sheet.write(0, 9, 'Ссылка_изображения')
    sheet.write(0, 10, 'Наличие')
    sheet.write(0, 11, 'Скидка')
    sheet.write(0, 12, 'Производитель')
    sheet.write(0, 13, 'Страна_производитель')
    sheet.write(0, 14, 'Название_группы')
    sheet.write(0, 15, 'Идентификатор_группы')
    sheet.write(0, 16, 'Уникальный_идентификатор')
    sheet.write(0, 17, 'Идентификатор_товара')
    sheet.write(0, 18, 'Ярлык')

    for char_num in range(20):
        sheet.write(0, char_num * 3 + 19, 'Название_Характеристики')
        sheet.write(0, char_num * 3 + 20, 'Измерение_Характеристики')
        sheet.write(0, char_num * 3 + 21, 'Значение_Характеристики')


    with open('Unique identifiers.json', 'r', encoding = 'UTF-8') as json_file:
        data = json.loads(json_file.read())
        max_id = data['max_id']
        unique_ids = data['identifiers']

    with open('Links with groups.json', 'r', encoding = 'UTF-8') as json_file:
        groups_data = json.loads(json_file.read())

    with open('Links with thematics.json', 'r', encoding = 'UTF-8') as json_file:
        thematics_data = json.loads(json_file.read())

    char_keys = []
    for i, product in enumerate(products):
        row = i + 1
        sheet.write(row, 0, product.articul)
        sheet.write(row, 1, product.name)
        # try:
        sheet.write(row, 3, product.render_template())
        # except:
        #   print(f'Not found description of articul: {product.articul}')
        #   no_desc_articuls.append(product.articul)
        #   pass
        sheet.write(row, 4, 'r')
        sheet.write(row, 5, product.price)
        sheet.write(row, 6, 'KZT')
        sheet.write(row, 7, 'шт.')
        sheet.write(row, 8, product.quantity)
        sheet.write(row, 9, ', '.join(product.images))
        sheet.write(row, 10, '+')
        sheet.write(row, 11, '50%')
        sheet.write(row, 12, product.brand)
        sheet.write(row, 13, 'Россия')
        sheet.write(row, 14, product.group_name)
        sheet.write(row, 15, product.group_identifier)
        try:
            sheet.write(row, 16, unique_ids[product.articul])
        except:
            unique_ids[product.articul] = str(max_id + 1)
            max_id -= -1
            sheet.write(row, 16, unique_ids[product.articul])
        sheet.write(row, 17, product.product_identifier)
        sheet.write(row, 18, product.marker)
        
        for char, value in product.chars.items():
            if char in char_keys:
                col = 19 + 3 * char_keys.index(char)
            else:
                char_keys.append(char)
                col = 16 + 3 * len(char_keys)

            sheet.write(row, col, char)
            sheet.write(row, col + 2, value)

    data = {
        'max_id': max_id,
        'identifiers': unique_ids
    }

    with open('Unique identifiers.json', 'w', encoding = 'UTF-8') as json_file:
        json_file.write(json.dumps(data, indent = 4))


    for col in range(100):
        sheet.col(col).width = 256 * 30

    for row in range(100):
        sheet.row(row).height = 256 * 500
        # print(sheet.row(row).height)

    excel_file.save(filename)

    # write_to_googlesheet()


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


with open('Group identifiers.json', 'r', encoding = 'UTF-8') as file:
    group_identifiers_data = json.loads(file.read())
    group_identifiers_data['посуда'] = 'posuda'


templateLoader = jinja2.FileSystemLoader(searchpath = "./")
templateEnv = jinja2.Environment(loader = templateLoader)


access_token = get_token()

print(f'Access token: {access_token}')

# data = get_and_filter_data()
with open('Data.json', 'r', encoding = 'UTF-8') as file:
    data = json.loads(file.read())

print(len(data))
for product_data in data:
    print(f"{product_data['attributes']['title']} - {product_data['id']}")
    product = SokolovProduct(product_data)

write_to_excel()