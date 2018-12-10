from __future__ import print_function

import re

import progressbar
import requests


from bs4 import BeautifulSoup
from dotmap import DotMap


from csgo_alltime_stats.db import CsgoDatabase
from csgo_alltime_stats.util import get_api_key, get_initial_page, login, parse_players, parse_table

db = CsgoDatabase()

api_key = get_api_key(db)

needs_login = False
if db.get_cookie():
    response, headers, sessionid, steamid = get_initial_page(db)
else:
    needs_login = True

if needs_login or response.status_code != 200:
    login(db)
    response, headers, sessionid, steamid = get_initial_page(db)

first_page = response.text

count_url = 'https://steamcommunity.com/profiles/' + steamid + '/gcpd/730/?tab=matchmaking'
response = requests.get(count_url, headers=headers, allow_redirects=False)
soup = BeautifulSoup(response.text, 'html.parser')

table = soup.find('table', {'class': 'generic_kv_table'})
tds = table.find_all('tr')[1].find_all('td')
wins = int(tds[1].get_text())
ties = int(tds[2].get_text())
losses = int(tds[3].get_text())
total_matches = wins + ties + losses

print('Loading {0} matches ({1} won, {2} tied, {3} lost)'.format(total_matches, wins, ties, losses))


with progressbar.ProgressBar(max_value=total_matches) as bar:
    parse_table(first_page, bar, db, api_key)
    match = re.search(r"var g_sGcContinueToken = '([0-9]*)';", first_page)
    if match:
        continue_token = match.group(1)
    else:
        continue_token = None

    while continue_token:
        next_url = 'https://steamcommunity.com/profiles/' + steamid + '/gcpd/730?ajax=1&tab=matchhistorycompetitive&continue_token={0}&sessionid={1}'.format(continue_token, sessionid)
        response = requests.get(next_url, headers=headers)
        as_json = response.json()
        if not as_json['success']:
            break
        html = as_json['html']

        parse_table(html, bar, db, api_key)

        if 'continue_token' in as_json:
            continue_token = as_json['continue_token']
        else:
            break
