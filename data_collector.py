from os.path import dirname, exists

from bs4 import BeautifulSoup
import requests
import pandas as pd
import re

if exists(dirname(__file__) + "/data.csv"):
    print('CSV file already exists. If you want to reload data remove "data.csv."')
    exit(0)

print("Attention! Data collection takes approximately 10 minutes. Please wait.")

convert = {
    '£': 'GBP',
    '₹': 'INR',
    '₩': 'KRW',
    'RUR': 'RUB',
    '$': 'USD',
    '¥': 'JPY',
    '€': 'EUR',
    'FRF': 'FRF',
    'TRL': 'TRY',
    'A$': 'AUD',
    'DEM': 'DEM',
    'R$': 'BRL'
}

with open(dirname(__file__) + '/currency_token.txt', 'r') as f:
    CURRENCY_TOKEN = f.read()

currency = requests.get(f'http://api.exchangeratesapi.io/v1/latest?access_key={CURRENCY_TOKEN}').json()['rates']
currency.update({'FRF': 6.55957, 'DEM': 1.95583})
currency_pattern = re.compile(r"^(\D*)([\d,]*)")

time_pattern = re.compile(r'(?:(\d*)h)?\s?(?:(\d*)min)?')

FILM_URL = r"https://www.imdb.com"
TOP_URL = "https://www.imdb.com/chart/top/?ref_=nv_mv_250"

films_list = []

ans = requests.get(TOP_URL)
bs = BeautifulSoup(ans.content, 'html.parser')

progress = 0

for film in bs.find_all('td', 'titleColumn'):
    film_info = dict()
    # Get film title
    film_info['title'] = film.a.text
    # Get film page on IMDb
    film_page = BeautifulSoup(requests.get(FILM_URL + film.a['href']).content, 'html.parser')
    # Get year
    info_list = film_page.find('ul', 'TitleBlockMetaData__MetaDataList-sc-12ein40-0').children
    film_info['year'] = int(next(info_list).span.text)
    # Get film runtime
    m = time_pattern.match(film_page.find('li', {'data-testid': 'title-techspec_runtime'}).div.text)
    hours = int(m.group(1) if m.group(1) else 0)
    minutes = int(m.group(2) if m.group(2) else 0)
    film_info['runtime'] = hours * 60 + minutes
    # Get film genres
    film_info['genres'] = {genre.span.text for genre in film_page.find_all('a', 'GenresAndPlot__GenreChip-cum89p-3')}
    # Get film rate
    film_info['rate'] = float(film_page.find('span', 'AggregateRatingButton__RatingScore-sc-1ll29m0-1').text)
    # Get director and actors
    peoples = film_page.find('div', 'PrincipalCredits__PrincipalCreditsPanelWideScreen-hdn81t-0').ul.children
    film_info['director'] = next(peoples).ul.li.a.text
    next(peoples)
    actors = next(peoples)
    if actors is not None:
        film_info['actors'] = {i.text.strip().removesuffix('(voice)').strip() for i in actors.div.ul.children}
    # Get film budget
    budget = film_page.find('li', 'BoxOffice__MetaDataListItemBoxOffice-sc-40s2pl-2')
    if budget is not None:
        m = currency_pattern.match(film_page.find('li', 'BoxOffice__MetaDataListItemBoxOffice-sc-40s2pl-2').div.text)
        code = convert[m.group(1).strip()]
        money = int(m.group(2).strip().replace(',', ''))
        if code != 'USD':
            money = int(money / currency[code] * currency['USD'])
        film_info['budget'] = money
    # Get country
    film_info['countries'] = \
        {country.text for country in film_page.find('li', {'data-testid': 'title-details-origin'}).div.ul.children}
    # Add film to film list
    films_list.append(film_info)
    progress += 1
    print(f'\rProcessed: {progress}/250', end='', flush=True)

films = pd.DataFrame(
    films_list,
    columns=[
        'title',
        'rate',
        'year',
        'runtime',
        'budget',
        'genres',
        'director',
        'actors',
        'countries'
    ]
)
films.to_csv(dirname(__file__) + "/data.csv")
