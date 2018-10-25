from __future__ import print_function

import getpass
import re
import sys
from base64 import b64encode

import progressbar
import requests
import rsa
from bs4 import BeautifulSoup
from dotmap import DotMap
from tinydb import Query, TinyDB


STEAM_ID_REGEX = r'[0-9]{17}'
id_regex = re.compile(STEAM_ID_REGEX)
id_resolve_url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={0}&vanityurl={1}"

database_file = 'csgo-alltime-stats.db'
db = TinyDB(database_file)

match_table = db.table('matches')
player_table = db.table('players')

def get_encrypted_password(user, password):
    rsa_key_response = DotMap(requests.post('https://steamcommunity.com/login/home/getrsakey/', data={ 'username': user }).json())
    e = int(rsa_key_response.publickey_exp, 16)
    n = int(rsa_key_response.publickey_mod, 16)
    pubkey = rsa.PublicKey(n, e)
    encrypted = rsa.encrypt(password.encode('utf-8'), pubkey)
    encoded = b64encode(encrypted)
    return encoded, rsa_key_response.timestamp

def login():
    user_name = input('Enter user name: ')
    password = getpass.getpass('Enter password (will not be echoed): ')

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
    params.remember_login = 'true'

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

    if login_response.login_complete:
        print('Logged in!')
    else:
        print('Failed to log in with message: {0}'.format(login_response.message))
        sys.exit(1)

    cookie_query = Query()
    db.upsert({'id': 'cookie', 'data': login_response.toDict()}, cookie_query.id == 'cookie')

def get_initial_page():
    cookie_query = Query()
    login_data = DotMap(db.get(cookie_query.id == 'cookie')['data'])
    steamid = login_data.transfer_parameters.steamid
    cookies = []
    sessionid = login_data.transfer_parameters.auth
    cookies.append({
        'name': 'sessionid',
        'value': sessionid
    })
    cookies.append({
        'name': 'steamLogin',
        'value': steamid + '%7C%7C' + login_data.transfer_parameters.auth
    })
    cookies.append({
        'name': 'steamLoginSecure',
        'value': steamid + '%7C%7C' + login_data.transfer_parameters.token_secure
    })


    cookies_all = '; '.join(['{0}={1}'.format(cookie['name'], cookie['value']) for cookie in cookies])

    sessionid = [cookie['value'] for cookie in cookies if cookie['name'].lower() == 'sessionid']


    headers = {
        'Cookie': cookies_all
    }

    initial_url = 'https://steamcommunity.com/profiles/' + steamid + '/gcpd/730/?tab=matchhistorycompetitive'

    response = requests.get(initial_url, headers=headers, allow_redirects=False)
    return response, headers, sessionid, steamid


def get_api_key():
    api_key_query = Query()
    api_key_entry = db.get(api_key_query.id == 'api_key')
    if not api_key_entry:
        api_key = input('Enter steam api key (get it at  https://steamcommunity.com/dev/apikey): ')
        db.insert({'id': 'api_key', 'key': api_key})
    api_key_query = Query()
    return db.get(api_key_query.id == 'api_key')['key']


api_key = get_api_key()
while requests.get('http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key={0}&appid=218620'.format(api_key)).status_code == 401:
    print('Api key invalid. Please re-enter')
    api_key = get_api_key()

needs_login = False
cookie_query = Query()
if db.get(cookie_query.id == 'cookie'):
    response, headers, sessionid, steamid = get_initial_page()
else:
    needs_login = True

if needs_login or response.status_code != 200:
    login()
    response, headers, sessionid, steamid = get_initial_page()

first_page = response.text

def parse_players(rows):
    players = []
    for row in rows:
        player = DotMap() 
        columns = row.find_all('td')
        player_column = columns[0]
        player.name = player_column.get_text().strip()
        profile_id = player_column.find('a')['href'].split('/')[-1]
        if id_regex.match(profile_id):
            player_query = Query()
            existing_player = player_table.get(player_query.id == profile_id)
            if not existing_player:
                player_table.insert({'id': profile_id, 'profile_id': profile_id})
            steamid = profile_id
        else:
            player_query = Query()
            existing_player =  player_table.get(player_query.profile_id == profile_id)
            if existing_player:
                steamid = existing_player['id']
            else:
                response = DotMap(requests.get(id_resolve_url.format(api_key, profile_id)).json()).response
                if response.success == 1:
                    steamid = response.steamid
                    player_table.insert({'id': steamid, 'profile_id': profile_id})
                else:
                    print('Could not resolve steamid for {0}'.format(profile_id))
                    sys.exit(1)
        player.id = steamid
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

def parse_table(html_doc, bar):
    soup = BeautifulSoup(html_doc, 'html.parser')

    map_tables = soup.find_all('table', {'class': 'csgo_scoreboard_inner_left'})
    score_tables = soup.find_all('table', {'class': 'csgo_scoreboard_inner_right'})

    for idx in range(len(map_tables)):
        bar.update(bar.value + 1)
        map_data = DotMap()
        map_table = map_tables[idx]
        map_rows = map_table.find_all('td')
        map_data.map = map_rows[0].get_text().lower().replace('competitive', '').strip()
        map_data.date = map_rows[1].get_text().strip()
        match_query = Query()
        existing_match = match_table.search(match_query.date == map_data.date)
        if existing_match:
            continue
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
        match_table.insert(map_data.toDict())

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
    parse_table(first_page, bar)
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

        parse_table(html, bar)

        if 'continue_token' in as_json:
            continue_token = as_json['continue_token']
        else:
            break
