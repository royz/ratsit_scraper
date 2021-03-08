from pprint import pprint
import json
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ReadTimeout


def find_address(soup):
    new_data = {'address': None, 'phone': None}
    try:
        data = soup.find('script', {'type': 'application/ld+json'})
        json_data = json.loads(next(data.children).strip())
        for res in json_data:
            # if address already not found and address is present in current data
            if not new_data['address'] and 'address' in res:
                # get the address
                try:
                    new_data['address'] = {
                        'country': res['address']['addressCountry'],
                        'locality': res['address']['addressLocality'],
                        'zip': res['address']['postalCode'],
                        'street': res['address']['streetAddress']
                    }
                except:
                    pass

                # get the phone number
                try:
                    new_data['phone'] = res['telephone']
                except:
                    pass
    except StopIteration as e:
        print(e)
        pass

    return new_data


def get_details(url):
    try:
        response = requests.get(url, timeout=10)
    except ReadTimeout:
        print('request timed out. retrying...')
        return get_details(url)

    # with open('details.html', 'w', encoding='utf-8') as f:
    #     f.write(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')

    # get the address and phone number
    data = find_address(soup)
    data.update({'url': url})

    # get all company names
    try:
        company_spans = soup.find_all('span', {'class': 'engagement-company'})
        companies = [company_span.text.strip() for company_span in company_spans]
        companies = list(set(companies))
    except:
        companies = []
    data.update({'companies': companies})

    # get businesses
    try:
        business_table = soup.find('div', {'id': 'foretagPaAdressenLista'})
        table_rows = business_table.find_all('tr')[1:]
        businesses = [business.find('a').text.strip() for business in table_rows]
    except Exception as e:
        businesses = []

    data.update({'businesses': businesses})

    # get a list of persons they are living with
    persons_living_with = []
    try:
        report_table = soup.find('table', {'class': 'rapport-table rapport-table--limit-large-screens'})
        for tr in report_table.find_all('tr'):
            persons_living_with.append(tr.text.strip().replace('\n', ''))
    except:
        pass
    data.update({'living_with': persons_living_with})

    pprint(data)


get_details(
    'https://www.ratsit.se/19730218-Anette_Viktoria_Brannstrom_Kage/F7id624rk-2lkikPNkXeIggownTnfW39eLbTCiRO6v4')
