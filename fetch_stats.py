from __future__ import print_function

import getpass
import json
import re
import sys

import requests
from bs4 import BeautifulSoup
from dotmap import DotMap

from base64 import b64encode

from Crypto.PublicKey.RSA import construct
from Crypto.Cipher import PKCS1_v1_5

user_name = input('Enter user name: ')
password = getpass.getpass('Enter password (will not be echoed): ')

def get_encrypted_password(user, password):
    rsa_key_response = DotMap(requests.post('https://steamcommunity.com/login/home/getrsakey/', data={ 'username': user }).json())

    e = int(rsa_key_response.publickey_exp, 16)
    n = int(rsa_key_response.publickey_mod, 16)
    pubkey = construct((n, e))
    cipher = PKCS1_v1_5.new(pubkey)
    encrypted = cipher.encrypt(password.encode('utf-8'))
    print(repr(encrypted))
    encoded = b64encode(encrypted)
    return encoded, rsa_key_response.timestamp

encoded_encrypted_password, rsa_timestamp = get_encrypted_password(user_name, password)

params = DotMap()
params.password = encoded_encrypted_password
params.username = user_name
params.rsatimestamp = rsa_timestamp
params.twofactorcode = ''
params.emailauth = ''
params.loginfriendlyname = ''
params.captchagid = '-1'
params.emailsteamid = ''
params.remember_login = 'false'

login_response = DotMap(requests.post('https://steamcommunity.com/login/home/dologin/', data=params.toDict()).json())

if login_response.requires_twofactor:
    token = input('Enter steam guard code: ')
    params.twofactorcode = token
    encoded_encrypted_password, rsa_timestamp = get_encrypted_password(user_name, password)
    params.password = encoded_encrypted_password
    params.rsatimestamp = rsa_timestamp
    login_response = DotMap(requests.post('https://steamcommunity.com/login/home/dologin/', data=params.toDict()).json())

if login_response.emailauth_needed:
    token = input('Enter email auth code: ')
    params.emailauth = token
    login_response = DotMap(requests.post('https://steamcommunity.com/login/home/dologin/', data=params.toDict()).json())

if login_response.success:
    print('Logged in!')
else:
    print('Failed to log in with message: {0}'.format(login_response.message))
    sys.exit(1)

login_response.pprint()


cookies_all = '; '.join(['{0}={1}'.format(cookie['name'], cookie['value']) for cookie in cookies])

sessionid = [cookie['value'] for cookie in cookies if cookie['name'].lower() == 'sessionid']


headers = {
    'Cookie': cookies_all
}

initial_url = url_prefix + '/gcpd/730/?tab=matchhistorycompetitive'

response = requests.get(initial_url, headers=headers)

first_page = response.text

def parse_players(rows):
    players = []
    for row in rows:
        player = DotMap() 
        columns = row.find_all('td')
        player.name = columns[0].get_text().strip()
        player.ping = int(columns[1].get_text())
        player.kills = int(columns[2].get_text())
        player.assists = int(columns[3].get_text())
        player.deaths = int(columns[4].get_text())
        stars = columns[5].get_text().strip()
        if not stars:
            player.stars = 0
        elif len(stars) == 1:
            player.stars = 1
        else:
            player.stars = int(stars[1])
        hsp = columns[6].get_text().strip()
        if not hsp:
            player.hsp = 0
        else:
            player.hsp = int(columns[6].get_text().strip().strip('%'))
        player.score = int(columns[7].get_text())
        players.append(player)
    return players

def parse_table(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')

    map_tables = soup.find_all('table', {'class': 'csgo_scoreboard_inner_left'})
    score_tables = soup.find_all('table', {'class': 'csgo_scoreboard_inner_right'})

    maps = []

    for idx in range(len(map_tables)):
        map_data = DotMap()
        map_table = map_tables[idx]
        map_rows = map_table.find_all('td')
        map_data.map = map_rows[0].get_text().lower().replace('competitive', '').strip()
        map_data.date = map_rows[1].get_text().strip()
        map_data.wait_time = map_rows[2].get_text().lower().replace('wait time:', '').strip()
        map_data.match_duration = map_rows[3].get_text().lower().replace('match duration:', '').strip()

        score_table = score_tables[idx]
        score_rows = score_table.find_all('tr')
        game_score = score_rows[6].find('td').get_text()
        team_1_score, team_2_score = game_score.split(' : ')
        map_data.team1.score = int(team_1_score)
        map_data.team1.players = parse_players(score_rows[1:6])
        map_data.team2.score = int(team_2_score)
        map_data.team2.players = parse_players(score_rows[7:])

        maps.append(map_data)
    return maps

all_maps = []
all_maps.extend(parse_table(first_page))

match = re.search(r"var g_sGcContinueToken = '([0-9]*)';", first_page)
if match:
    continue_token = match.group(1)
else:
    continue_token = None

while continue_token:
    next_url = url_prefix + '/gcpd/730?ajax=1&tab=matchhistorycompetitive&continue_token={0}&sessionid={1}'.format(continue_token, sessionid)
    print('Loading next page...')
    response = requests.get(next_url, headers=headers)
    as_json = response.json()
    if not as_json['success']:
        break
    html = as_json['html']

    all_maps.extend(parse_table(html))

    if 'continue_token' in as_json:
        continue_token = as_json['continue_token']
    else:
        break

print('Saving data of {0} maps.'.format(len(all_maps)))

with open('all_maps.json', 'w') as all_maps_file:
    json.dump(all_maps, all_maps_file)
