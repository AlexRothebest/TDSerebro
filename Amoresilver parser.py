import requests

from bs4 import BeautifulSoup as bs

from threading import Thread

import time


def get_html(url):
	return requests.get(url).text


def parse_product(url):
	global data

	soup = bs(get_html(url), 'html5lib')

	articul = soup.select_one("span[data-qaid='product_code']").text.strip()
	attached_products = [a.get('href') for a in soup.select('a.b-similar-products__image-link')]

	print(f"Articul: {articul}\nAttached products: {', '.join(attached_products)}")

	data[articul] = attached_products


def parse_page(url):
	global product_links

	soup = bs(get_html(url), 'html5lib')

	links = [f"https://amoresilver.kz/{a.get('href')}"\
			 for a in soup.select('a.b-product-gallery__image-link')]

	print('\n'.join(links))

	for link in links:
		if link not in product_links:
			product_links.append(link)
			print(link)
			break


def parse_category(url):
	soup = bs(get_html(url), 'html5lib')

	number_of_pages = int(soup.select('a.b-pager__link')[-2].text.strip())

	for page_number in range(1, number_of_pages + 1):
		page_url = f'{url}/page_{page_number}'
		print(page_url)
		thread = Thread(target = parse_page, args = (page_url,))
		thread.start()
		time.sleep(0.1)


group_links = []
product_links = []
data = {}

url = 'https://amoresilver.kz/'

soup = bs(get_html(url), 'html5lib')

links = [f"https://amoresilver.kz/{a.get('href')}"\
		 for a in soup.select('a.b-product-groups-gallery__image-link')]

print('\n'.join(links))

category_flags = 

for link in links:
	parse_category(link)