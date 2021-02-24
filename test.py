from scraper import Ratsit

r = Ratsit()
# res = r.search('Camilla', 'Larsson', '19830728')
res = r.search('Susann', 'Forsman', '19810215')  # has two companies
# res = r.search('Margaretha', 'Lundin', '19590826')  # has a business
print(res)
