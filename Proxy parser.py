import requests

from bs4 import BeautifulSoup as bs

from threading import Thread

from datetime import datetime

from random import randint

import time


def get_html_proxy(url, proxies = {}):
    return requests.get(url, proxies = proxies, timeout = 7).text


def check_proxy(proxy):
    global good_proxy_list, perfect_proxy_list, good_proxy_file, perfect_proxy_file

    proxies = {
        'http': f'http://{proxy}',
        'https': f'https://{proxy}'
    }

    try:
        start_time = datetime.now()
        html = get_html_proxy('https://icanhazip.com', proxies).strip()
        required_time = (datetime.now() - start_time).seconds

        if 0 < len(html) < 25:
            print(f'\nHTML: {html}\nProxy: {proxy}\nTime: {required_time}\n\n')

            good_proxy_list.append(proxy)

            good_proxy_file.write(proxy + '\n')
            if randint(1, 3) == 3:
                good_proxy_file.close()
                good_proxy_file = open('Proxy list.txt', 'a')

            if required_time <= 2:
                perfect_proxy_list.append(proxy)

                perfect_proxy_file.write(proxy + '\n')
                if randint(1, 3) == 3:
                    perfect_proxy_file.close()
                    perfect_proxy_file = open('Perfect proxy list.txt', 'a')
    except:
        pass


def check_all_proxy(proxy_list):
    for proxy in proxy_list:
        print(proxy)

        thread = Thread(target = check_proxy, args = (proxy,))
        thread.start()
        #check_proxy(proxy)

        time.sleep(0.1)


def search_awmproxy():
    base_url = 'https://awmproxy.net/freeproxy_c61af52d7ff7bbe.txt'

    proxy_list = [proxy for proxy in get_html_proxy(base_url).split('\n')]

    print(f'Proxies found: {len(proxy_list)}\n')

    check_all_proxy(proxy_list)


good_proxy_file = open('Proxy list.txt', 'w')
perfect_proxy_file = open('Perfect proxy list.txt', 'w')

good_proxy_list = []
perfect_proxy_list = []

search_awmproxy()

time.sleep(10)

print(f'Good proxies found: {len(good_proxy_list)}')
print(f'Perfect proxies found: {len(perfect_proxy_list)}')

good_proxy_file.close()
perfect_proxy_file.close()