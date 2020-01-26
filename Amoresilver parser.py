import requests

from bs4 import BeautifulSoup as bs

from threading import Thread

from datetime import datetime

import time

import json

import jinja2

from random import randint


class AttachedProduct():
	def __init__(self, articul):
		url = f'https://amoresilver.kz/site_search?search_term={articul}'

		soup = bs(get_html(url), 'html.parser')
		# soup = bs(requests.get(url).text, 'html.parser')

		self.url = soup.select_one('a.b-product-gallery__title').get('href').strip()

		print(self.url)

		soup = bs(get_html(url), 'html.parser')
		# soup = bs(requests.get(url).text, 'html.parser')

		# with open('file.html', 'w', encoding = 'UTF-8') as file:
		# 	file.write(soup.prettify())

		self.name = soup.select_one("a.b-goods-title").text.strip()
		self.articul = soup.select_one("span.b-search-result-info__term").text.strip()
		self.image_link = soup.select_one('img.b-product-gallery__image').get('src').strip()

		print(self.url, self.name, self.image_link)


# AttachedProduct('94013102')
# 
# a = 1 / 0


def create_thread(function, args):
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
		except:
			print(f'Error... {url}')

	response = None
	while response is None:
		create_thread(get_response, ())
		# thread = Thread(target = get_response, args = ())
		# thread.start()
		time.sleep(3)

	return response.text


def parse_product(url):
	global data, product_flags, no_desc_links, number_of_threads

	def render_template(product_articul, attached_products):
		global templateEnv

		template = templateEnv.get_template('Description.html')
		output_text = template.render(product_articul = articul,
									 attached_products = attached_products)

		return output_text

	soup = bs(get_html(url), 'html5lib')
	# soup = bs(requests.get(url).text, 'html5lib')

	try:
		articul = soup.select_one("span[data-qaid='product_code']").text.strip()
		# description_html = soup.select_one("div[data-qaid='product_description']").prettify()
		print(articul)

		attached_products = []
		for span in soup.select('span.b-similar-products__hider'):
			articul = span.text
			articul = articul[articul.find('Артикул:') + 8:].strip()
			print(articul)
			attached_products.append(AttachedProduct(articul))

		description_html = render_template(articul, attached_products)

		print(description_html)

		with open('file with true desc.html', 'w', encoding = 'UTF-8') as file:
			file.write(description_html)

		data[articul] = description_html
	except:
		no_desc_links.append(url)

	print(f'Parsed: {url}')

	product_flags[url] = True


if True:
	pass
	# templateLoader = jinja2.FileSystemLoader(searchpath = "./")
	# templateEnv = jinja2.Environment(loader = templateLoader)
	# 
	# data = {}
	# number_of_threads = 0
	# max_number_of_threads = 100
	# 
	# parse_product('https://amoresilver.kz/p67759904-serebryanoe-koltso-fianitom.html')
	# a = 1 / 0
	# 
	# 
	# with open('Articuls without description.txt', 'r', encoding = 'UTF-8') as file:
	# 	product_links = [f'https://amoresilver.kz/site_search?search_term={articul}'\
	# 					 for articul in file.read().split('\n')]
	# 
	# no_desc_links = []
	# product_flags = {}
	# for link in product_links[:10]:
	# 	product_flags[link] = False
	# 	create_thread(parse_product, (link,))
	# 	time.sleep(0.1)
	# 
	# iterations = 0
	# while False in [product_flags[key] for key in product_flags]:
	# 	iterations += 1
	# 	if iterations >= 60:
	# 		break
	# 
	# 	time.sleep(10)
	# 
	# 	for link in product_flags:
	# 		if product_flags[link] is False:
	# 			print(f'Not ready product flag: {link}')
	# 
	# print('No description URLs:\n' + '\n'.join(no_desc_links))
	# 
	# with open('Description.json', 'w', encoding = 'UTF-8') as json_file:
	# 	json_file.write(json.dumps(data, indent = 4))
	# 
	# a = 1 / 0


def parse_category(url):
	global category_flags, number_of_threads

	def create_thread(function, args):
	    print('Thread created')

	    while True:
	        try:
	            Thread(target = function, args = args).start()
	            break
	        except:
	            time.sleep(3)



	def parse_page(url):
		global product_links, number_of_threads
		nonlocal page_flags

		soup = bs(get_html(url), 'html5lib')

		links = [a.get('href') for a in soup.select('a.b-product-gallery__image-link')]

		for link in links:
			if link not in product_links:
				product_links.append(link)
				print(link)
			else:
				print(f'BAD LINK: {link}')

		print(f'Parsed page: {url}')

		page_flags[url] = True

		number_of_threads -= 1


	soup = bs(get_html(url), 'html5lib')

	number_of_pages = int(soup.select('a.b-pager__link')[-2].text.strip())

	# number_of_pages = 1######################################################################

	page_flags = {}
	for page_number in range(1, number_of_pages + 1):
		page_url = f'{url}/page_{page_number}'
		page_flags[page_url] = False
		print(page_url)
		create_thread(parse_page, (page_url,))
		# thread = Thread(target = parse_page, args = (page_url,))
		# thread.start()
		time.sleep(0.1)

	print(f'Page flags: {len(page_flags)}')

	iterations = 0
	while False in [page_flags[key] for key in page_flags]:
		iterations += 1
		if iterations >= 60:
			break

		time.sleep(5)

		for link in page_flags:
			if page_flags[link] is False:
				print(f'Not ready page flag: {link}')

	print(f'Parsed category: {url}')

	category_flags[url] = True

	number_of_threads -= 1


with open('Perfect proxy list.txt', 'r', encoding = 'UTF-8') as file:
    good_proxies = [{
        'http': f'http://{proxy}',
        'https': f'https://{proxy}'
    } for proxy in file.read().split('\n')]


templateLoader = jinja2.FileSystemLoader(searchpath = "./")
templateEnv = jinja2.Environment(loader = templateLoader)

product_links = []
data = {}
number_of_threads = 0
max_number_of_threads = 100

url = 'https://amoresilver.kz'

soup = bs(get_html(url), 'html5lib')

links = [f"https://amoresilver.kz{a.get('href')}"\
		 for a in soup.select('a.b-product-groups-gallery__image-link')]

print('\n'.join(links))

category_flags = {}
for link in links:#######################################################################
	category_flags[link] = False
	create_thread(parse_category, (link,))
	time.sleep(0.1)

start_time = datetime.now()
while False in [category_flags[key] for key in category_flags] and (datetime.now() - start_time).seconds < 1200:
	time.sleep(10)
	for link in category_flags:
		if category_flags[link] is False:
			print(f'Not ready category flag: {link}')

with open('Amoresilver links.txt', 'w', encoding = 'UTF-8') as file:
	file.write('\n'.join(product_links))


no_desc_links = []
product_flags = {}
for link in product_links:##############################################################
	product_flags[link] = False
	create_thread(parse_product, (link,))
	time.sleep(0.1)

iterations = 0
while False in [product_flags[key] for key in product_flags]:
	iterations += 1
	if iterations >= 60:
		break

	time.sleep(10)

	for link in product_flags:
		if product_flags[link] is False:
			print(f'Not ready product flag: {link}')

print('No description URLs:\n' + '\n'.join(no_desc_links))

with open('Description.json', 'w', encoding = 'UTF-8') as json_file:
	json_file.write(json.dumps(data, indent = 4))