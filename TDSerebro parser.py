import requests, time, xlwt, xlrd, json, jinja2, httplib2, googleapiclient.discovery

from oauth2client.service_account import ServiceAccountCredentials

from mechanicalsoup import StatefulBrowser

from bs4 import BeautifulSoup as bs

from threading import Thread

from random import randint

from datetime import datetime

from tkinter import *

from pprint import pprint

from auth_data import tdserebro_login, tdserebro_password


def create_thread(function, args = ()):
    print('Thread created')

    while True:
        try:
            Thread(target = function, args = args).start()
            break
        except:
            time.sleep(3)


def get_html(url):
	global good_proxies

	def create_thread(function, args):
	    print('Thread created')

	    while True:
	        try:
	            Thread(target = function, args = args).start()
	            break
	        except:
	            time.sleep(3)


	def get_response():
		global number_of_threads
		nonlocal response

		try:
			proxies = good_proxies[randint(0, len(good_proxies) - 1)]

			response_local = requests.get(url, proxies = proxies, timeout = 7)
			if response_local.status_code == 200:
				response = response_local
			else:
				print(response.status_code)
		except Exception as e:
			# raise e

			print(f'Error... {url}')

	if 'tdserebro' in url:
		return requests.get(url).text

	response = None
	while response is None:
		create_thread(get_response, ())
		# thread = Thread(target = get_response, args = ())
		# thread.start()
		time.sleep(3)

	return response.text


class AttachedProduct():
	def __init__(self, articul):
		global not_found_on_amoresilver_articuls

		url = f'https://amoresilver.kz/site_search?search_term={articul}'

		soup = bs(get_html(url), 'html.parser')

		for product_block in soup.select("li[data-qaid='product-block']"):
			if articul in product_block.select_one("div[title='Код:']").text:
				self.url = product_block.select_one('a.b-product-gallery__title').get('href').strip()
				break

		try:
			x = self.url
		except:
			del self
			not_found_on_amoresilver_articuls.append(articul)
			return

		soup = bs(get_html(url), 'html.parser')

		# with open('file.html', 'w', encoding = 'UTF-8') as file:
		# 	file.write(soup.prettify())

		self.name = soup.select_one("a.b-goods-title").text.strip()
		self.articul = soup.select_one("span.b-search-result-info__term").text.strip()
		self.image_link = soup.select_one('img.b-product-gallery__image').get('src').strip()

		# print(self.url, self.name, self.image_link)


# not_found_on_amoresilver_articuls = []
# print(AttachedProduct('94022450').name)
# a = 1 / 0


class Product():
	objects = []

	class Sklad():
		objects = []

		class Version():
			objects = []

			def __init__(self, soup):
				self.__class__.objects.append(self)

				self.size = soup.select_one('div div div div').text.replace('р', '').replace('см', '').replace('.', '').strip()
				if '\n' in self.size:
					self.size = self.size[:self.size.find('\n')].strip()
				if self.size == '':
					self.size = 'не указан'
				price = soup.select_one('span.price_sku_from').text
				self.price = float(price[price.find('от') + 2 : price.find('KZT')].replace(' ', '').replace('₽', '').strip())
				quantity = soup.select_one("div[title='Остаток на складе']").text
				self.quantity = int(quantity[:quantity.find('шт')].strip())
				weight = soup.text
				if 'Вес' in weight:
					self.weight = weight[weight.find('Вес') + 4:].strip()
				else:
					self.weight = 'не указан'

				print(f'\t\tРазмер: {self.size}\nЦена: {self.price}\nКоличество: {self.quantity}\nВес: {self.weight}\n'.replace('\n', '\n\t\t'))


		def __init__(self, soup):
			self.__class__.objects.append(self)

			self.name = soup.select_one('h3.wharehouse_title').text.strip()

			self.chars = {li.text.split(':')[0].strip() : li.text.split(':')[1].strip().replace(', ', '|')
						  for li in soup.select('ul:nth-of-type(1) li')}

			print(f'\t{self.name}\n\tХарактеристики: {self.chars}')

			if len(soup.select('div.item-product-quantity-one')) == 1:
				self.versions = [self.__class__.Version(soup.select_one('div.item-product-quantity-one'))]
			else:
				self.versions = [self.__class__.Version(div) for div in soup.select('div.item-product-quantity')]

			self.sizes = []
			for version in self.versions:
				if version.size != 'не указан':
					self.sizes.append(version.size)


	def __init__(self, soup, url):
		global groups_data, thematics_data, number_of_products_viewed, number_of_products_endviewed

		with open('file.html', 'w', encoding = 'UTF-8') as file:
			file.write(soup.prettify())

		number_of_products_viewed += 1

		self.ready_status = False
		
		self.url = url
		self.group_identifier, self.group_name = url[url.rfind('#') + 1:].split('!')
		self.product_identifier = url[url.rfind('/') + 1 : url.find('#')]
		self.marker = url.split('#')[1]

		title = soup.select_one('h4#ModalProductLabel').text
		title = title[:title.find('(Результат')].strip()
		self.name, self.articul = title[:title.rfind(' ')], title[title.rfind(' ') + 1:]
		if '\n' in self.name:
			self.name = self.name[:self.name.find('\n')]
		images = [img.get('src') for img in soup.select('div#img-gallery img')]
		for image_num, image in enumerate(images):
			if image[:4] != 'http':
				images[image_num] = 'https://tdserebro.ru/media/cache/thumb_500' + images[image_num]
		self.images = images
		self.brand = [soup.select_one(f'div.product_page_total > b:nth-of-type({num + 1}) + a').text
					  for num, b in enumerate(soup.select('div.product_page_total > b'))
					  if b.text == 'Бренд:'][0]
		self.name += ' ' + self.brand

		self.sklads = []
		for div in soup.select('div.show-skus > div'):
			self.sklads.append(self.__class__.Sklad(div))


		change_chars = {
			'Вставка': 'Вставка/камень',
			'Толщина': 'Толщина проволоки'
		}
		self.chars = {
			'Наличие, размеры в Алматы (склад 1)': 'Нет',
			'Наличие, размеры в Нурсултане': 'Нет'
		}
		try:
			self.chars['Товарная категория'] = groups_data[self.url[:self.url.find('#')]]
		except:
			pass
		try:
			self.chars['Тематика'] = thematics_data[self.url[:self.url.find('#')]]
		except:
			pass
		self.sizes = []
		self.quantity = 0
		for sklad in self.sklads:
			if sklad.name == 'Склад - АЛМ Основной':
				if len(sklad.sizes) > 0:
					self.chars['Наличие, размеры в Алматы (склад 1)'] = '|'.join(sklad.sizes)
				else:
					self.chars['Наличие, размеры в Алматы (склад 1)'] = 'Да'
			elif sklad.name == 'Склад - АСТ Основной':
				if len(sklad.sizes) > 0:
					self.chars['Наличие, размеры в Нурсултане'] = '|'.join(sklad.sizes)
				else:
					self.chars['Наличие, размеры в Нурсултане'] = 'Да'

			for char, value in sklad.chars.items():
				try:
					self.chars[change_chars[char]] = value
				except:
					self.chars[char] = value

			for version in sklad.versions:
				self.quantity += version.quantity
				if version.size != 'не указан' and version.size not in self.sizes:
					self.sizes.append(version.size)


		if len(self.sklads) == 0 or self.quantity == 0 or 'бижутерия' in self.name.lower():
			number_of_products_endviewed += 1
			self.ready_status = True
			del self
			return
		else:
			self.price = self.sklads[0].versions[0].price * 3


		self.sizes.sort()
		self.name += ' размеры ' + ' '.join(self.sizes)

		if self.name[-8:] == 'размеры ':
			self.name = self.name[:-9]

		try:
			attached_product_articuls = [attached_product_block.p.text.split(':')[1].strip()\
										 for attached_product_block in soup.select('div.product_desc_content')]
			self.attached_products = []
			# print(attached_product_articuls)
			for articul in attached_product_articuls:
				attached_product = AttachedProduct(articul)
				try:
					x = attached_product.name
					self.attached_products.append(attached_product)
				except:
					pass
			if len(self.attached_products) > 0:
				self.name += ' - есть комплект'
		except:
			self.attached_product = ''

		print(f"Наименование: {self.name}\nАртикул: {self.articul}\nИзображения: {', '.join(self.images)}\nБренд: {self.brand}")

		number_of_products_endviewed += 1

		self.__class__.objects.append(self)

		self.ready_status = True

		print()

	def render_template(self):
		global templateEnv

		template = templateEnv.get_template('Description.html')
		output_text = template.render(product_articul = self.articul,
									  attached_products = self.attached_products)

		return output_text


class Parser():
	objects = []

	def get_browser(self):
		browser = StatefulBrowser()
		url = 'https://tdserebro.ru/login?changeCity=1526384'
		browser.open(url)
		browser.select_form('form.login_form')
		browser['_username'] = tdserebro_login
		browser['_password'] = tdserebro_password
		browser.submit_selected()

		self.browser = browser


	def __init__(self, links_list):
		global Product, all_errors

		self.ready_status = False

		self.__class__.objects.append(self)
		
		self.get_browser()
		self.products = []
		for link in links_list:
			print(f'Parsing {link}')
			self.browser.open(link)
			self.products.append(Product(self.browser.get_current_page(), link))

		self.ready_status = True


def write_to_excel():
	global description_data, no_desc_articuls

	products = Product.objects

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
		# 	print(f'Not found description of articul: {product.articul}')
		# 	no_desc_articuls.append(product.articul)
		# 	pass
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

	write_to_googlesheet()


def write_to_googlesheet():
	sheet = xlrd.open_workbook('Data.xls').sheet_by_index(0)
	data = [[sheet.cell_value(row, col) for col in range(sheet.ncols)] for row in range(sheet.nrows)]
	pprint(data)

	CREDENTIALS_FILE = 'creds.json'
	spreadsheet_id = '1eMVic6fqq3oZ8Cs7C_Il2N0TbNZLj7HYQTUeZKs8iy0'

	credentials = ServiceAccountCredentials.from_json_keyfile_name(
		CREDENTIALS_FILE,
		[
			'https://www.googleapis.com/auth/spreadsheets',
			'https://www.googleapis.com/auth/drive'
		]
	)

	httpAuth = credentials.authorize(httplib2.Http())
	service = googleapiclient.discovery.build('sheets', 'v4', http = httpAuth)

	values = service.spreadsheets().values().batchUpdate(
		spreadsheetId=spreadsheet_id,
		body={
			'valueInputOption': 'USER_ENTERED',
			'data': [
				{
					'majorDimension': 'ROWS',
					'range': f'A1:CA{len(data)}',
					'values': data
				}
			]
		}
	).execute()

	results = service.spreadsheets().batchUpdate(
		spreadsheetId=spreadsheet_id, 
		body={
			"requests": [
				{
					"updateDimensionProperties": {
						"range": {
							"sheetId": 0,
							"dimension": "COLUMNS",
							"startIndex": 0,
							"endIndex": 78
						},
						"properties": {
							"pixelSize": 200
						},
						"fields": "pixelSize"
					}
				},
				{
					"updateDimensionProperties": {
						"range": {
							"sheetId": 0,
							"dimension": "ROWS",
							"startIndex": 0,
							"endIndex": 10000
						},
						"properties": {
							"pixelSize": 50
						},
						"fields": "pixelSize"
					}
				}
			]
		}
	).execute()


def parse_thematics():
	def parse_page(url):
		nonlocal all_links, page_flags

		print(url)

		soup = bs(get_html(url), 'html.parser')

		group_name = soup.select_one('b.selected_filter').text.strip()

		links = {f"https://tdserebro.ru{a.get('href')}" : group_name\
				 for a in soup.select('a.modal-trigger')}

		for link in links:
			try:
				all_links[link].append(links[link])
			except:
				all_links[link] = [links[link]]

		page_flags[url] = True


	def parse_group(url):
		nonlocal all_page_links, group_flags

		soup = bs(get_html(url), 'html.parser')

		try:
			number_of_pages = int(soup.select_one('ul.pagination').select('li')[-1].a.text.strip())
		except:
			number_of_pages = 1

		print(f'{url}: {number_of_pages}')

		for page_number in range(1, number_of_pages + 1):
			page_url = f'{url}&page={page_number}'
			all_page_links.append(page_url)

		group_flags[url] = True


	url = 'https://tdserebro.ru/almaty/search'
	soup = bs(get_html(url), 'html.parser')
	print(len(soup.select('select#filter_themes option')))
	with open('file.html', 'w', encoding = 'UTF-8') as file:
		file.write(soup.prettify())
	group_links = [f"https://tdserebro.ru/almaty/search?filter%5Bthemes%5D%5B0%5D={option.get('value')}&sort=new%3Adesc"\
				   for option in soup.select('select#filter_themes option')]

	all_page_links = []
	group_flags = {}
	for link in group_links:#######################################################################
		group_flags[link] = False
		thread = Thread(target = parse_group, args = (link,))
		thread.start()
		time.sleep(0.5)

	while False in [group_flags[key] for key in group_flags]:
		time.sleep(1)

	print()

	all_links = {}
	page_flags = {}
	for url in all_page_links:#####################################################################
		page_flags[url] = False
		thread = Thread(target = parse_page, args = (url,))
		thread.start()
		time.sleep(0.5)

	while False in [page_flags[key] for key in page_flags]:
		time.sleep(1)

	with open('Links with thematics.json', 'w', encoding = 'UTF-8') as file:
		file.write(json.dumps(all_links, indent = 4))

	print(f'\nThematic links found: {len(all_links)}\n')

	return all_links


def parse_groups():
	def parse_page(url):
		nonlocal all_links, page_flags

		print(url)

		soup = bs(get_html(url), 'html.parser')

		group_name = soup.select_one('b.selected_filter').text.strip()

		if 'бижутерия' in group_name.lower():
			return

		links = {f"https://tdserebro.ru{a.get('href')}" : group_name\
				 for a in soup.find_all('a', class_ = 'modal-trigger')}

		for link in links:
			try:
				all_links[link].append(links[link])
			except:
				all_links[link] = [links[link]]

		page_flags[url] = True


	def parse_group(url):
		nonlocal all_page_links, group_flags

		soup = bs(get_html(url), 'html.parser')

		try:
			number_of_pages = int(soup.find('ul', class_ = 'pagination').find_all('li')[-1].a.text.strip())
		except:
			number_of_pages = 1

		print(f'{url}: {number_of_pages}')

		for page_number in range(1, number_of_pages + 1):
			page_url = f'{url}?page={page_number}'
			all_page_links.append(page_url)

		group_flags[url] = True


	url = 'https://tdserebro.ru/almaty'
	soup = bs(get_html(url), 'html.parser')
	col = soup.select_one('li.mega-menu-column')
	group_links = [f"https://tdserebro.ru{a.get('href')}" for a in col.select('ul.cd-accordion-submenu li a')]
	for li in col.select('li.has-children'):
		if len(li.select('ul.cd-accordion-submenu')) == 0:
			group_links.append(f"https://tdserebro.ru{li.label.a.get('href')}")
	print('Group links:\n' + '\n'.join(group_links) + '\n')

	all_page_links = []
	group_flags = {}
	for link in group_links:#######################################################################
		group_flags[link] = False
		thread = Thread(target = parse_group, args = (link,))
		thread.start()
		time.sleep(0.5)

	while False in [group_flags[key] for key in group_flags]:
		time.sleep(1)

	print()

	all_links = {}
	page_flags = {}
	for url in all_page_links:#####################################################################
		page_flags[url] = False
		thread = Thread(target = parse_page, args = (url,))
		thread.start()
		time.sleep(0.5)

	while False in [page_flags[key] for key in page_flags]:
		time.sleep(1)

	with open('Links with groups.json', 'w', encoding = 'UTF-8') as file:
		file.write(json.dumps(all_links, indent = 4))

	print(f'\nGroup links found: {len(all_links)}\n')

	return all_links


# parse_groups()
# a = 1 / 0


def get_products_links():
	def parse_page(url):
		nonlocal all_links, page_flags

		print(url)

		soup = bs(get_html(url), 'html.parser')

		group_name = soup.select_one('b.selected_filter').text.strip()
		# links = [f"https://tdserebro.ru{a.get('href')}#{url[url.rfind('/') + 1 : url.rfind('?')]}!{group_name}"\
		# 		 for a in soup.find_all('a', class_ = 'modal-trigger')]
		links = []
		for product_block in soup.select('div.product'):
			if len(product_block.select('div.marker_hit')) > 0:
				marker = 'Хит'
			else:
				marker = ''	
			links.append(f"https://tdserebro.ru{product_block.select_one('a.modal-trigger').get('href')}#{marker}#{url[url.rfind('/') + 1 : url.rfind('?')]}!{group_name}")

		for link in links:
			if link not in all_links:
				all_links.append(link)

		page_flags[url] = True


	def parse_group(url):
		nonlocal all_page_links, group_flags

		soup = bs(get_html(url), 'html.parser')

		try:
			number_of_pages = int(soup.find('ul', class_ = 'pagination').find_all('li')[-1].a.text.strip())
		except:
			number_of_pages = 1

		print(f'{url}: {number_of_pages}')

		for page_number in range(1, number_of_pages + 1):
			page_url = f'{url}?page={page_number}'
			all_page_links.append(page_url)

		group_flags[url] = True


	url = 'https://tdserebro.ru/almaty'
	soup = bs(get_html(url), 'html.parser')
	col = soup.select('li.mega-menu-column')[1]
	group_links = [f"https://tdserebro.ru{a.get('href')}" for a in col.select('ul.cd-accordion-submenu li a')]
	for li in col.select('li.has-children'):
		if len(li.select('ul.cd-accordion-submenu')) == 0:
			group_links.append(f"https://tdserebro.ru{li.label.a.get('href')}")
	print('Group links:\n' + '\n'.join(group_links) + '\n')

	all_page_links = []
	group_flags = {link: False for link in group_links}
	for link in group_links:
		thread = Thread(target = parse_group, args = (link,))
		thread.start()
		time.sleep(0.5)

	while False in [group_flags[key] for key in group_flags]:
		time.sleep(1)

	print()

	all_links = []
	page_flags = {link: False for link in all_page_links}
	for url in all_page_links:
		thread = Thread(target = parse_page, args = (url,))
		thread.start()
		time.sleep(0.5)

	while False in [page_flags[key] for key in page_flags]:
		time.sleep(1)

	with open('Links.txt', 'w', encoding = 'UTF-8') as file:
		file.write('\n'.join(all_links))

	print(f'\nLinks found: {len(all_links)}\n')

	return all_links


def get_products_links2():
	with open('Links.txt', 'r', encoding = 'UTF-8') as file:
		all_links = file.read().split('\n')

	print(f'Links found: {len(all_links)}\n')

	return all_links


def start_parser(list_of_links):
	parser = Parser(list_of_links)


def create_interface():
    global root

    root = Tk()
    root.title('TDSerebro parser')
    root.minsize(260, 110)

    save_button = Button(root, text = 'Занести уже собранные\nданные в файл', width = 25, height = 2)
    save_button.bind('<Button-1>', lambda event: create_thread(write_to_excel, ()))
    save_button.place(x = 40, y = 30)

    root.mainloop()


write_to_googlesheet()
exit()


create_thread(create_interface)


with open('Description.json', 'r', encoding = 'UTF-8') as file:
	description_data = json.loads(file.read())

with open('Links with groups.json', 'r', encoding = 'UTF-8') as file:
	groups_data = json.loads(file.read())


templateLoader = jinja2.FileSystemLoader(searchpath = "./")
templateEnv = jinja2.Environment(loader = templateLoader)


with open('Perfect proxy list.txt', 'r', encoding = 'UTF-8') as file:
    good_proxies = [{
        'http': f'http://{proxy}',
        'https': f'https://{proxy}'
    } for proxy in file.read().split('\n')]


# parse_thematics()

# products_links = get_products_links()
products_links = get_products_links2()

number_of_parsers = 100
not_found_on_amoresilver_articuls = []
number_of_products_viewed = 0
number_of_products_endviewed = 0

list_of_lists_of_links = [[] for i in range(number_of_parsers)]
products_links = products_links[3300 : 3800]
# products_links = ['https://tdserebro.ru/almaty/product_modal/407208##!']
for list_num, link in enumerate(products_links):
	list_of_lists_of_links[list_num % number_of_parsers].append(link)

for list_of_links in list_of_lists_of_links:
	create_thread(start_parser, (list_of_links,))
	# thread = Thread(target = start_parser, args = (list_of_links,))
	# thread.start()
	# time.sleep(0.1)

time.sleep(3)

start_time = datetime.now()
l = len(products_links)
while False in [parser.ready_status for parser in Parser.objects] and (datetime.now() - start_time).seconds < 3600:
	print(len(Product.objects))
	with open('Len.txt', 'w', encoding = 'UTF-8') as file:
		# file.write(str(len(Product.objects)))
		file.write(f'{len(Product.objects)}/{number_of_products_endviewed}/{number_of_products_viewed}/{l}')

	time.sleep(10)

print(Product.objects[0].price)

print(number_of_products_viewed)

no_desc_articuls = []

write_to_excel()

write_to_googlesheet()

with open('Articuls without description.txt', 'w', encoding = 'UTF-8') as file:
	file.write('\n'.join(no_desc_articuls))

print('Not found articuls on amoresilver.kz:\n' + '\n'.join(not_found_on_amoresilver_articuls))

exit()