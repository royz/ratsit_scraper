import re
from pprint import pprint
import json
import requests
from bs4 import BeautifulSoup
import os
import glob
import openpyxl
import time

BASE_DIR = os.path.dirname(__file__)
CACHE_PATH = os.path.join(BASE_DIR, 'cache.json')


class Ratsit:
    def __init__(self):
        self.session = None
        self.cache = None
        self.cache_written_at = 0
        self.read_cache()
        self.init_session()

    def init_session(self):
        self.session = requests.session()
        self.session.headers = headers = {
            'authority': 'www.ratsit.se',
            'accept': '*/*',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/88.0.4324.182 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.ratsit.se',
        }

    def search(self, first_name, last_name, person_number):
        if not self.cache:
            self.read_cache()

        person_hash = self.get_hash(first_name, last_name, person_number)

        if person_hash in self.cache:
            return self.cache.get(person_hash)

        data = {
            'Typ': '2',
            'p': '1',
            'FNamn': first_name,
            'ENamn': last_name,
            'PNr': person_number,
            'Telefon': '',
            'Gatuadress': '',
            'PostNr': '',
            'PostOrt': '',
            'Kommun': '',
            'Man': 'true',
            'Kvinna': 'true',
            'Relation': 'true',
            'EjRelation': 'true',
            'AlderFran': '',
            'AlderTill': '',
            'HarBolagsengagemang': 'true',
            'HarEjBolagsengagemang': 'true',
            'page': '1',
            'clientQueryId': '1'
        }
        try:
            response = self.session.post('https://www.ratsit.se/Sok/SokPersonPartial', data=data)
            primary = response.json()['htmlPrimary']
            soup = BeautifulSoup(primary, 'html.parser')
            return self.get_details(
                'https://www.ratsit.se' +
                soup.find('div', {'class': 'search-list-item'}).find('a')['href']
                , person_hash)
        except:
            return None

    def get_details(self, url, person_hash):
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # get the address and phone number
        data = self.find_address(response.text)

        # get company name
        try:
            company = soup.find('span', {'class': 'engagement-company'}).text.strip()
        except:
            company = None
        data.update({'company': company})

        # get a list of persons they are living with
        persons_living_with = []
        try:
            report_table = soup.find('table', {'class': 'rapport-table rapport-table--limit-large-screens'})
            for tr in report_table.find_all('tr'):
                persons_living_with.append(tr.text.strip().replace('\n', ''))
        except:
            pass
        data.update({'living_with': persons_living_with})

        # add the data into cache
        self.cache[person_hash] = data
        # save the cache into a file
        self.write_cache()

        return data

    @staticmethod
    def print_details(details):
        address = details.get('address')
        phone = details.get('phone')
        company = details.get('company')
        living_with = details.get('living_with')

        if address:
            print(f"address: {address['street']}, {address['locality']}, {address['zip']}")
        if len(living_with) > 0:
            print('living with: ' + '\n             '.join(living_with))
        if phone:
            print(f"phone: {phone}")
        if company:
            print(f"company: {company}")

    @staticmethod
    def find_address(text):
        try:
            match = ''.join((re.findall(r'(\[{"@context)(.*)(}])', text)[0]))
            json_data = json.loads(match)
            for res in json_data:
                if 'address' in res:
                    return {
                        'address': {
                            'country': res['address']['addressCountry'],
                            'locality': res['address']['addressLocality'],
                            'zip': res['address']['postalCode'],
                            'street': res['address']['streetAddress']
                        },
                        'phone': res['telephone'],
                    }
        except:
            return {'address': None, 'phone': None}

    @staticmethod
    def get_hash(first_name, last_name, person_number):
        """
        create an unique hashable string with the person's info
        :param first_name: str
        :param last_name: str
        :param person_number: str
        :return: str
        """
        return f'{first_name}-{last_name}-{person_number}'

    def read_cache(self):

        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, encoding='utf-8') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
        else:
            self.cache = {}

    def write_cache(self):
        # write the cache every 60 seconds
        if time.time() < self.cache_written_at + 60:
            return

        with open(CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2)


class Excel:
    def __init__(self):
        self.file_name = None
        self.file_path = None
        self.input = []
        self.output = []

    def read_input(self):
        files = glob.glob(os.path.join(BASE_DIR, '*.xlsx'))
        file_names = [file.split(os.path.sep)[-1] for file in files]
        print('choose a file:')
        for i, file in enumerate(file_names):
            print(f'{i + 1}. {file}')
        try:
            idx = int(input('file number: ')) - 1
            self.file_name = file_names[idx]
            self.file_path = files[idx]

            # read the data
            workbook = openpyxl.load_workbook(self.file_path)
            sheet = workbook.active
            for i, row in enumerate(sheet.iter_rows()):
                if i == 0:
                    continue

                self.input.append({
                    'row': i,
                    'first_name': row[1].value,
                    'last_name': row[2].value,
                    'person_number': row[0].value,
                })
        except:
            print('the file does not exist')
            quit()

    def write_data(self, data):
        pass


if __name__ == '__main__':
    ratsit = Ratsit()
    excel = Excel()
    excel.read_input()

    # result = ratsit.search('Johanna', 'Hallberg', '19720111')
    # ratsit.print_details(result)
