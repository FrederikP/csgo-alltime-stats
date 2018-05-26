from __future__ import print_function

import getpass
import json
import re
import sys

import requests
from bs4 import BeautifulSoup
from dotmap import DotMap
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

options = webdriver.ChromeOptions()

options.add_argument('headless')

driver = webdriver.Chrome(chrome_options=options)

login_Page = 'https://steamcommunity.com/login/home/'

driver.get(login_Page)

def handle_login_branches():
    logged_in = False
    while not logged_in:
        try:
            WebDriverWait(driver, 0.5).until(EC.visibility_of_element_located((By.CLASS_NAME, 'profile_header')))
            logged_in = True
        except TimeoutException:
            try:
                two_factor_field = WebDriverWait(driver, 0.5).until(
                    EC.visibility_of_element_located((By.ID, 'twofactorcode_entry'))
                )
                two_factor_button = driver.find_element_by_css_selector('#login_twofactorauth_buttonset_entercode > div.auth_button.leftbtn')

                two_factor_token = input('Enter two factor token: ').upper()
                two_factor_field.send_keys(two_factor_token)

                two_factor_button.click()
                logged_in = True

            except TimeoutException:
                try:
                    auth_code_field = WebDriverWait(driver, 0.5).until(
                        EC.visibility_of_element_located((By.ID, 'authcode'))
                    )
                    auth_code_button = driver.find_element_by_css_selector('#auth_buttonset_entercode > div.auth_button.leftbtn')

                    auth_code = input('Enter auth code: ').upper()
                    auth_code_field.send_keys(auth_code)

                    auth_code_button.click()

                    continue_button = WebDriverWait(driver, 20).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, '#success_continue_btn > div.auth_button_h3'))
                    )
                    continue_button.click()
                    logged_in = True
                except TimeoutException:
                    try:
                        error_display = WebDriverWait(driver, 0.5).until(
                            EC.visibility_of_element_located((By.ID, 'error_display'))
                        )
                        print('Got error message when trying to login: {}'.format(error_display.text))
                        sys.exit(1)
                    except TimeoutException:
                        pass

try:
    user_field = driver.find_element_by_id('steamAccountName')
    password_field = driver.find_element_by_id('steamPassword')
    sign_in_button = driver.find_element_by_id('SteamLogin')
    
    user_name = input('Enter user name: ')
    user_field.send_keys(user_name)
    password = getpass.getpass('Enter password (will not be echoed): ')
    password_field.send_keys(password)
    sign_in_button.click()

    handle_login_branches()
    
    print('Logged in. Waiting for profile to grab cookieeeeees')
    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CLASS_NAME, 'profile_header')))

    url_prefix = driver.current_url

    cookies = driver.get_cookies()

    cookies_all = '; '.join(['{0}={1}'.format(cookie['name'], cookie['value']) for cookie in cookies])

    sessionid = [cookie['value'] for cookie in cookies if cookie['name'].lower() == 'sessionid']
finally:
    driver.quit()

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
        player.hsp = int(columns[6].get_text().strip('%'))
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
