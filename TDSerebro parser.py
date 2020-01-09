from mechanicalsoup import StatefulBrowser

import requests

from bs4 import BeautifulSoup as bs

from threading import Thread

import time

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


	def __init__(self, soup):
		self.ready_status = False
		
		self.__class__.objects.append(self)

		title = soup.select_one('h4#ModalProductLabel').text
		title = title[:title.find('(Результат')].strip()
		self.name, self.articul = title[:title.rfind(' ')], title[title.rfind(' ') + 1:]

		self.images = [img.get('src') for img in soup.select('div#img-gallery img')]

		self.brand = [soup.select_one(f'div.product_page_total > b:nth-of-type({num + 1}) + a').text
					  for num, b in enumerate(soup.select('div.product_page_total > b'))
					  if b.text == 'Бренд:'][0]

		print(f"Наименование: {self.name}\nАртикул: {self.articul}\nИзображения: {', '.join(self.images)}\nБренд: {self.brand}")

		self.sklads = []
		for div in soup.select('div.show-skus > div'):
			self.sklads.append(self.__class__.Sklad(div))

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

		#print(f"User: {browser.get_current_page().select_one('a.name_user_header').text.strip()}\n")

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
			self.products.append(Product(self.browser.get_current_page()))

		self.ready_status = True


def write_to_excel():
	products = Product.objects

	print(f'Products parsed: {len(products)}')

	for product in products:
		pass


def get_products_links():
	def get_html(url):
		return requests.get(url).text


	def parse_page(url):
	    nonlocal all_links, page_flags

	    soup = bs(get_html(url), 'html.parser')

	    links = [f"https://tdserebro.ru{a.get('href')}" for a in soup.find_all('a', class_ = 'modal-trigger')]

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
			page_url = f'https://tdserebro.ru/almaty/group/sergi?page={page_number}'
			all_page_links.append(page_url)

		group_flags[url] = True


	url = 'https://tdserebro.ru'
	soup = bs(get_html(url), 'html.parser')
	group_links = [f"https://tdserebro.ru{li.a.get('href')}" for li in soup.find('div', {'id': 'tab_container'}).find_all('li')[1:]]
	group_links[-1] = "https://tdserebro.ru/samara/group/shnury"
	print('Group links:\n' + '\n'.join(group_links))

	all_page_links = []
	group_flags = {link: False for link in group_links}
	for link in group_links:
		pass
		thread = Thread(target = parse_group, args = (link,))
		thread.start()
		time.sleep(0.5)

	while False in [group_flags[key] for key in group_flags]:
		time.sleep(1)

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

	print(f'Links found: {len(all_links)}\n')

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

number_of_parsers = 10

list_of_lists_of_links = [[] for i in range(number_of_parsers)]
for list_num, link in enumerate(products_links[:100]):
	list_of_lists_of_links[list_num % number_of_parsers].append(link)

for list_of_links in list_of_lists_of_links:
	thread = Thread(target = start_parser, args = (list_of_links,))
	thread.start()
	time.sleep(0.1)

time.sleep(3)

while False in [parser.ready_status for parser in Parser.objects]:
	time.sleep(10)

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