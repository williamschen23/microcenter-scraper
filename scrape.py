import csv
import os
import pytz
import requests
import re
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

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
            writer.writerow(['Time', 'Category', 'Name', 'Part_ID', 'Link', 'Full_Price', 'Discounted_Price', 'Saved_Price'])
        writer.writerows(data)

def write_csv_bundles(data, filename='bundles_data.csv'):
    file_is_empty = not os.path.exists(filename) or os.path.getsize(filename) == 0
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        if file_is_empty:
            print(f'{bcolors.OKGREEN}Writing headers{bcolors.ENDC}')
            writer.writerow(['Time', 'Category', 'Name', 'Link', 'Full_Price', 'Discounted_Price', 'Saved_Price'])
        writer.writerows(data)

def write_hdf5_bundles(data):
    columns = ['Time', 'Category', 'Name', 'Link', 'Full_Price', 'Discounted_Price', 'Saved_Price']
    df = pd.DataFrame(data, columns=columns)
    df['Time'] = df['Time'].astype('S36')
    df['Full_Price'] = df['Full_Price'].astype('float16')
    df['Discounted_Price'] = df['Discounted_Price'].astype('float16')
    df['Saved_Price'] = df['Saved_Price'].astype('float16')

    with pd.HDFStore('data.h5', mode='a', complevel=9, complib='zlib') as hdf:
        for name, group in df.groupby('Name'):
            # get and filter stuff
            subgroup = group[['Time', 'Full_Price', 'Discounted_Price', 'Saved_Price']]
            name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
            link = group['Link'].iloc[0]
            
            hdf.append(f'Bundle/{name}', subgroup, format='table', data_columns=True, index=False)
            hdf.get_storer(f'Bundle/{name}').attrs.link = link

def write_hdf5(data):
    columns = ['Time', 'Category', 'Name', 'Part_ID', 'Link', 'Full_Price', 'Discounted_Price', 'Saved_Price']
    df = pd.DataFrame(data, columns=columns)
    df['Time'] = df['Time'].astype('S36')
    df['Full_Price'] = df['Full_Price'].astype('float16')
    df['Discounted_Price'] = df['Discounted_Price'].astype('float16')
    df['Saved_Price'] = df['Saved_Price'].astype('float16')

    with pd.HDFStore('data.h5', mode='a', complevel=9, complib='zlib') as hdf:
        for name, group in df.groupby('Name'):
            # get stuff
            part = str(group['Part_ID'].iloc[0])
            subgroup = group[['Time', 'Full_Price', 'Discounted_Price', 'Saved_Price']]
            category = group['Category'].iloc[0]
            link = group['Link'].iloc[0]
            
            # filter
            part = re.sub(r'[^a-zA-Z0-9_]', '_', part)
            name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
            category = re.sub(r'[^a-zA-Z0-9_]', '_', category)
            
            # append stuff
            hdf.append(f'{category}/{name}', subgroup, format='table', data_columns=True, index=False)
            hdf.get_storer(f"{category}/{name}").attrs.part_id = part
            hdf.get_storer(f"{category}/{name}").attrs.link = link

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
        # try:
            doc = fetch_html(bundle_link)
            curr_time = current_time()
            if not doc:
                continue
            
            bundles = doc.find_all('div', class_='two') + doc.find_all('div', class_='four') + doc.find_all('div', id='Base') + doc.find_all('div', id='Upgrade')
            print(f'{bcolors.OKGREEN}Found {len(bundles)} bundles at {bundle_link}{bcolors.ENDC}')

            for bundle in bundles:
                # filtering the empty spots
                if(bundle.text == ''):
                    continue

                # filter price
                if bundle.find('div', class_='savings'):
                    temp = bundle.find('div', class_='savings').text.split('\n')[0]
                    full_price = float(temp[temp.index('$')+1:].replace(',', ''))
                    curr_price = float(bundle.find('div', class_='price').text[1:].replace(',', ''))
                else:
                    full_price = curr_price = float(bundle.find('div', class_='price').text[1:].replace(',', ''))
                discounted = float('{:2f}'.format(full_price - curr_price))

                name = bundle.find(class_='B').text.replace('\r\n', ',').replace('\n', ',').replace(u'\u2122', '')
                link = 'https://microcenter.com' + bundle.find('a').get('href')

                all_data.append([curr_time, 'Bundle', name, link, full_price, curr_price, discounted])

        # except Exception as e:
            # print(f"{bcolors.FAIL}An error occurred: {e}{bcolors.ENDC}")
    
    return all_data

def scrape_anything_else(links):
    all_data = []

    for link in links:
        page = 1
        while True:
            url = get_link(link, page)
            doc = fetch_html(url)
            curr_time = current_time()
            if not doc:
                break

            products = doc.find_all('li', class_='product_wrapper')
            if not products:
                break
            
            print(f'{bcolors.OKGREEN}Found {len(products)} items at {url}{bcolors.ENDC}')

            for product in products:
                # product id
                temp_text = product.find('p', class_='sku').text
                product_id = int(temp_text[temp_text.index(' ')+1:])
                
                # link, name, category
                data = product.find('div', class_='pDescription').find('a')
                product_link = 'https://microcenter.com' + data.get('href')
                name = data.text
                category = data['data-category']
                
                # prices
                price_tag = product.find('span', itemprop='price')
                if price_tag:
                    full_price_element = product.find('div', class_='standardDiscount')
                    price = float(price_tag.text[price_tag.text.index('$')+1:].replace(',', ''))
                    if full_price_element:
                        temp = full_price_element.find('strike').text
                        full_price = float(temp[temp.index('$')+1:].replace(',', ''))
                    else:
                        full_price = price
                    discounted = float('{:.2f}'.format(full_price-price))
                else:
                    price = full_price = discounted = -1

                
                all_data.append([curr_time, category, name, product_id, product_link, full_price, price, discounted])

            page += 1
        
    return all_data

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

    bundle_data = []
    bundle_data += scrape_bundles(bundle_links)
    
    parts_data = []
    parts_data += scrape_anything_else(processors)
    parts_data += scrape_anything_else(motherboards)
    parts_data += scrape_anything_else(gpu)
    parts_data += scrape_anything_else(ram)
    parts_data += scrape_anything_else(storage)
    parts_data += scrape_anything_else(cases)
    parts_data += scrape_anything_else(power_supply)
    parts_data += scrape_anything_else(monitors)

    write_csv_bundles(bundle_data)
    write_csv(parts_data)
    write_hdf5_bundles(bundle_data)
    write_hdf5(parts_data)