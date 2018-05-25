from __future__ import print_function

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import requests

from bs4 import BeautifulSoup

import re

import json
import getpass

options = webdriver.ChromeOptions()

options.add_argument('headless')

driver = webdriver.Chrome(chrome_options=options)

login_Page = 'https://steamcommunity.com/login/home/'

driver.get(login_Page)

try:
    user_field = driver.find_element_by_id('steamAccountName')
    password_field = driver.find_element_by_id('steamPassword')
    sign_in_button = driver.find_element_by_id('SteamLogin')
    
    user_name = input('Enter user name: ')
    user_field.send_keys(user_name)
    password = getpass.getpass('Enter password (will not be echoed): ')
    password_field.send_keys(password)
    sign_in_button.click()

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
                    pass
    
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

def parse_table(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')

    score_tables = soup.find_all('table', {'class': 'csgo_scoreboard_inner_right'})

    player_scores = []

    for score_table in score_tables:
        rows = score_table.find_all('tr')

        headers = []

        for column in rows[0].find_all('th'):
            headers.append(column.get_text())

        for row in rows[1:]:
            player_score = {}
            columns = row.find_all('td')
            if len(columns) > 1:
                for idx, column in enumerate(columns):
                    player_score[headers[idx]] = column.get_text().strip()
                player_scores.append(player_score)
    return player_scores

all_player_scores = []
all_player_scores.extend(parse_table(first_page))

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

    all_player_scores.extend(parse_table(html))

    if 'continue_token' in as_json:
        continue_token = as_json['continue_token']
    else:
        break

print('Saving {0} scores.'.format(len(all_player_scores)))

with open('playerscores.json', 'w') as playerscores_file:
    json.dump(all_player_scores, playerscores_file)
