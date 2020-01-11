from mechanicalsoup import StatefulBrowser

import requests

from bs4 import BeautifulSoup as bs

from threading import Thread

import time

import xlwt

from auth_data import tdserebro_login, tdserebro_password


class Product():
	objects = []

	class Sklad():
		objects = []

		class Version():
			objects = []

			def __init__(self, soup):
				self.__class__.objects.append(self)

				self.size = soup.select_one('div div div div').text.strip()
				if self.size == '':
					self.size = 'не указан'
				price = soup.select_one('span.price_sku_from').text
				self.price = price[price.find('от') + 2 : price.find('KZT')].strip()
				quantity = soup.select_one("div[title='Остаток на складе']").text
				self.quantity = quantity[:quantity.find('шт')].strip()
				weight = soup.text
				if 'Вес' in weight:
					self.weight = weight[weight.find('Вес') + 4:].strip()
				else:
					self.weight = 'не указан'

				print(f'\t\tРазмер: {self.size}\nЦена: {self.price}\nКоличество: {self.quantity}\nВес: {self.weight}\n'.replace('\n', '\n\t\t'))


		def __init__(self, soup):
			self.__class__.objects.append(self)

			self.name = soup.select_one('h3.wharehouse_title').text.strip()

			self.chars = {li.text.split(':')[0].strip() : li.text.split(':')[1].strip()
						  for li in soup.select('ul:nth-of-type(1) li')}

			print(f'\t{self.name}\n\tХарактеристики: {self.chars}')

			if len(soup.select('div.item-product-quantity-one')) == 1:
				self.versions = [self.__class__.Version(soup.select_one('div.item-product-quantity-one'))]
			else:
				self.versions = [self.__class__.Version(div) for div in soup.select('div.item-product-quantity')]


	def __init__(self, soup, url):
		self.ready_status = False
		
		self.__class__.objects.append(self)

		self.url = url
		self.group_name = url[url.rfind('#') + 1:]
		self.product_identifier = url[url.rfind('/') + 1 : url.rfind('#')]

		title = soup.select_one('h4#ModalProductLabel').text
		title = title[:title.find('(Результат')].strip()
		self.name, self.articul = title[:title.rfind(' ')], title[title.rfind(' ') + 1:]
		images = [img.get('src') for img in soup.select('div#img-gallery img')]
		for image_num, image in enumerate(images):
			if image[:4] != 'http':
				images[image_num] = 'https://tdserebro.ru/media/cache/thumb_500' + images[image_num]
		self.images = images
		self.brand = [soup.select_one(f'div.product_page_total > b:nth-of-type({num + 1}) + a').text
					  for num, b in enumerate(soup.select('div.product_page_total > b'))
					  if b.text == 'Бренд:'][0]
		try:
			attached_product = soup.select_one('div.product_desc_content p').text
			self.attached_product = attached_product.split(':')[1].strip()
		except:
			self.attached_product = ''

		print(f"Наименование: {self.name}\nАртикул: {self.articul}\nИзображения: {', '.join(self.images)}\nБренд: {self.brand}")

		self.sklads = []
		for div in soup.select('div.show-skus > div'):
			self.sklads.append(self.__class__.Sklad(div))

		change_chars = {
			'Вставка': 'Вставка/камень'
		}
		self.chars = {}
		self.quantity = 0
		for sklad in self.sklads:
			for char, value in sklad.chars.items():
				try:
					self.chars[change_chars[char]] = value
				except:
					self.chars[char] = value

			for version in sklad.versions:
				self.quantity += int(version.quantity)

		if len(self.sklads) == 0 or self.quantity == 0:
			self.__class__.objects.remove(self)
			self.ready_status = True
			del self
			return
		else:
			self.price = self.sklads[0].versions[0].price


		self.ready_status = True

		print()


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
		global Product

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
	products = Product.objects

	print(f'Products parsed: {len(products)}')


	filename = 'Data.xls'
	sheetname = 'Sheet'
	file = xlwt.Workbook()
	sheet = file.add_sheet(sheetname)

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
	sheet.write(0, 15, 'Идентификатор_товара')

	for char_num in range(20):
		sheet.write(0, char_num * 3 + 16, 'Название_Характеристики')
		sheet.write(0, char_num * 3 + 17, 'Измерение_Характеристики')
		sheet.write(0, char_num * 3 + 18, 'Значение_Характеристики')


	char_keys = []
	for i, product in enumerate(products):
		row = i + 1
		sheet.write(row, 0, product.articul)
		sheet.write(row, 1, product.name)
		sheet.write(row, 3, product.attached_product)
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
		sheet.write(row, 15, product.product_identifier)
		
		for char, value in product.chars.items():
			if char in char_keys:
				col = 16 + 3 * char_keys.index(char)
			else:
				char_keys.append(char)
				col = 13 + 3 * len(char_keys)

			sheet.write(row, col, char)
			sheet.write(row, col + 2, value)


	for col in range(100):
		sheet.col(col).width = 256 * 30

	for row in range(100):
		sheet.row(row).height = 256 * 500
		# print(sheet.row(row).height)

	file.save(filename)


def get_products_links():
	def get_html(url):
		return requests.get(url).text


	def parse_page(url):
	    nonlocal all_links, page_flags

	    print(url)

	    soup = bs(get_html(url), 'html.parser')

	    links = [f"https://tdserebro.ru{a.get('href')}#{url[url.rfind('/') + 1 : url.rfind('?')]}"\
	    		 for a in soup.find_all('a', class_ = 'modal-trigger')]

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


	url = 'https://tdserebro.ru'
	soup = bs(get_html(url), 'html.parser')
	group_links = [f"https://tdserebro.ru{li.a.get('href')}" for li in soup.find('div', {'id': 'tab_container'}).find_all('li')[1:]]
	group_links[-1] = "https://tdserebro.ru/samara/group/shnury"
	print('Group links:\n' + '\n'.join(group_links) + '\n')

	all_page_links = []
	group_flags = {link: False for link in group_links}
	for link in group_links:
		# pass
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


# products_links = get_products_links()
products_links = get_products_links2()
# products_links = []

number_of_parsers = 10

list_of_lists_of_links = [[] for i in range(number_of_parsers)]
for list_num, link in enumerate(products_links[3000 : 4000]):
	list_of_lists_of_links[list_num % number_of_parsers].append(link)

for list_of_links in list_of_lists_of_links:
	thread = Thread(target = start_parser, args = (list_of_links,))
	thread.start()
	time.sleep(0.1)

# time.sleep(3)

while False in [parser.ready_status for parser in Parser.objects]:
	# time.sleep(5)
	pass

write_to_excel()


# parser = Parser(list_of_lists_of_links[0])


# def parse_url(product_url):
# 	browser = StatefulBrowser()
# 	url = 'https://tdserebro.ru/login?changeCity=1526384'
# 	browser.open(url)
# 	browser.select_form('form.login_form')
# 	browser['_username'] = tdserebro_login
# 	browser['_password'] = tdserebro_password
# 	browser.submit_selected()
# 
# 	print(f"User: {browser.get_current_page().select_one('a.name_user_header').text.strip()}\n")
# 
# 	browser.open(product_url)
# 	soup = browser.get_current_page()
# 	product = Product(soup)
# 
# parse_url('https://tdserebro.ru/almaty/product_modal/406561')
# 
# write_to_excel()