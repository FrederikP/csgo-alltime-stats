from __future__ import print_function

import getpass
import requests
import re
import rsa
import sys

from base64 import b64encode
from bs4 import BeautifulSoup
from dotmap import DotMap


STEAM_ID_REGEX = r'[0-9]{17}'
id_regex = re.compile(STEAM_ID_REGEX)
id_resolve_url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={0}&vanityurl={1}"

def get_api_key(db):
    api_key = db.get_api_key()
    if not api_key:
        key_invalid = True
        while key_invalid:
            api_key = input('Enter steam api key (get it at  https://steamcommunity.com/dev/apikey): ')
            key_invalid = requests.get('http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key={0}&appid=218620'.format(api_key)).status_code == 401
        db.set_api_key(api_key)
    return api_key

def get_initial_page(db):
    login_data = DotMap(db.get_cookie())
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

def get_encrypted_password(user, password):
    rsa_key_response = DotMap(requests.post('https://steamcommunity.com/login/home/getrsakey/', data={ 'username': user }).json())
    e = int(rsa_key_response.publickey_exp, 16)
    n = int(rsa_key_response.publickey_mod, 16)
    pubkey = rsa.PublicKey(n, e)
    encrypted = rsa.encrypt(password.encode('utf-8'), pubkey)
    encoded = b64encode(encrypted)
    return encoded, rsa_key_response.timestamp

def login(db):
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
    db.set_cookie(login_response.toDict())

def parse_players(rows, db, api_key):
    players = []
    for row in rows:
        player = DotMap() 
        columns = row.find_all('td')
        player_column = columns[0]
        player.name = player_column.get_text().strip()
        profile_id = player_column.find('a')['href'].split('/')[-1]
        if id_regex.match(profile_id):
            steamid = profile_id
            existing_player = db.get_player_by_steamid(steamid)
            if not existing_player:
                db.add_player(profile_id, profile_id)
        else:
            existing_player =  db.get_player_by_profile_id(profile_id)
            if existing_player:
                steamid = existing_player['id']
            else:
                response = DotMap(requests.get(id_resolve_url.format(api_key, profile_id)).json()).response
                if response.success == 1:
                    steamid = response.steamid
                    db.add_player(steamid, profile_id)
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

def parse_table(html_doc, bar, db, api_key):
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
        existing_match = db.get_match(map_data.date)
        if existing_match:
            continue
        map_data.wait_time = map_rows[2].get_text().lower().replace('wait time:', '').strip()
        map_data.match_duration = map_rows[3].get_text().lower().replace('match duration:', '').strip()

        score_table = score_tables[idx]
        score_rows = score_table.find_all('tr')
        game_score = score_rows[6].find('td').get_text()
        team_1_score, team_2_score = game_score.split(' : ')
        map_data.team1.score = int(team_1_score)
        map_data.team1.players = parse_players(score_rows[1:6], db, api_key)
        map_data.team2.score = int(team_2_score)
        map_data.team2.players = parse_players(score_rows[7:], db, api_key)
        db.add_match(map_data.toDict())
