import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
import pytz
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

price_pattern = re.compile(r'\$\d{1,3}(,\d{3})*(\.\d{2})?')
session = requests.Session()

def write_csv(data, filename='data.csv'):
    file_is_empty = not os.path.exists(filename) or os.path.getsize(filename) == 0
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        if file_is_empty:
            print(f'{bcolors.OKGREEN}Writing headers{bcolors.ENDC}')
            writer.writerow(['Time', 'Category', 'Name', 'Part ID', 'Link', 'Full Price', 'Discounted Price', 'Saved Price'])
        writer.writerows(data)

def regex_search(text):
    match = price_pattern.search(text)
    return match.group() if match else 'N/A'

def get_link(page, page_number=1):
    return f'https://www.microcenter.com/search/search_results.aspx?Ntk=all&sortby=match&N={page}&myStore=false&rpp=96&storeID=145&sortby=pricelow&page={page_number}'

def current_time():
    return datetime.now(tz=pytz.timezone('America/New_York'))

def fetch_html(url):
    try:
        result = session.get(url)
        result.raise_for_status()
        return BeautifulSoup(result.text, 'html.parser')
    except requests.RequestException as e:
        print(f'{bcolors.FAIL}Failed to retrieve {url}: {e}{bcolors.ENDC}')
        return None

def scrape_bundles(bundle_links):
    all_data = []

    for bundle_link in bundle_links:
        try:
            doc = fetch_html(bundle_link)
            if not doc:
                continue

            bundles = doc.find_all('div', id=lambda x: x and x.startswith('BUNDLES'))
            print(f'{bcolors.OKGREEN}Found {len(bundles)} bundles at {bundle_link}{bcolors.ENDC}')

            for div in bundles:
                next_div = div.find_all('div', recursive=False)
                for _, name in zip(*[iter(next_div)] * 2):
                    link = 'https://microcenter.com' + name.find('a').get('href')
                    full_name = name.find('h3').text
                    parts = [item.strip() for item in full_name.split('\n') if item.strip() and 'Combo' not in item]
                    part_print = ', '.join(parts)
                    full_price = regex_search(name.find('span').text)
                    price = regex_search(name.find('div', class_='price').text)
                    saved_price = '${:.2f}'.format(float(full_price[1:].replace(',', '')) - float(price[1:].replace(',', '')))

                    all_data.append([current_time(), 'Bundle', part_print, 'N/A', link, full_price, price, saved_price])

        except Exception as e:
            print(f"{bcolors.FAIL}An error occurred: {e}{bcolors.ENDC}")
    
    write_csv(all_data)

def scrape_anything_else(links):
    all_data = []

    for link in links:
        page = 1
        while True:
            url = get_link(link, page)
            doc = fetch_html(url)
            if not doc:
                break

            products = doc.find_all('li', class_='product_wrapper')
            if not products:
                break
            
            print(f'{bcolors.OKGREEN}Found {len(products)} items at {url}{bcolors.ENDC}')

            for product in products:
                product_id = product.find('p', class_='sku').text
                description = product.find('div', class_='pDescription')
                data = description.find('a')
                data_link = 'https://microcenter.com' + data.get('href')
                name = data.text
                category = data['data-category']
                
                price_tag = product.find('span', itemprop='price')
                full_price_element = product.find('div', class_='standardDiscount')

                if price_tag:
                    price = regex_search(price_tag.text)
                    full_price = regex_search(full_price_element.find('strike').text) if full_price_element else price
                    saved_price = '${:.2f}'.format(float(full_price[1:].replace(',', '')) - float(price[1:].replace(',', '')))
                else:
                    price = full_price = saved_price = 'N/A'

                
                all_data.append([current_time(), category, name, product_id, data_link, full_price, price, saved_price])

            page += 1
        
    write_csv(all_data)

if __name__ == '__main__':
    bundle_links = ['https://www.microcenter.com/site/content/bundle-and-save.aspx', 'https://www.microcenter.com/site/content/intel-bundle-and-save.aspx']
    
    # 0 is AMD, 1 is Intel. Motherboards are for ATX sized builds and AMD processors are on the AM5 socket.
    processors = ['4294966995+4294819840+4294805803', '4294966995+4294820689']
    motherboards = ['4294966996+4294818892+4294805803+4294818900', '4294966996+4294818573+4294818900']

    # 0 is AMD 6000 and 7000 series, 1 is Nvidia 3000 and 4000 series
    gpu = ['4294966937+4294820651+4294803792+4294803793', '4294966937+4294805677+4294808776']

    # 0 is ram
    ram = ['4294966965+4294806893']

    # 0 is storage, nvme drives and PCIe 4.0 or 5.0
    storage = ['4294945779+4294818519+4294809042+4294810863+4294805207']

    # 0 is PC cases
    cases = ['4294964318+4294808235+4294821195']

    # 0 is PSU
    power_supply = ['4294966654+4294818900']

    # 0 is monitors
    monitors = ['4294966896+4294806820+591']

    
    scrape_bundles(bundle_links)
    scrape_anything_else(processors)
    scrape_anything_else(motherboards)
    scrape_anything_else(gpu)
    scrape_anything_else(ram)
    scrape_anything_else(storage)
    scrape_anything_else(cases)
    scrape_anything_else(power_supply)
    scrape_anything_else(monitors)