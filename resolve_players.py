import json
import re

import progressbar
import requests

from dotmap import DotMap


STEAM_ID_REGEX = r'[0-9]{17}'
id_regex = re.compile(STEAM_ID_REGEX)

with open('all_maps.json') as data_file:
    map_data = json.load(data_file)

map_data_2 = []

for element in map_data:
    the_map = DotMap(element)
    map_data_2.append(the_map)

map_data = map_data_2

ids = set([player.id for the_map in map_data for player in the_map.team1.players + the_map.team2.players])

api_key = input('Enter steam api key: ')

id_resolve_url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={0}&vanityurl={1}"

resolved_ids = set()

for id in progressbar.progressbar(ids):
    if id_regex.match(id):
        resolved_ids.add(id)
    else:
        response = DotMap(requests.get(id_resolve_url.format(api_key, id)).json()).response
        if response.success == 1:
            resolved_ids.add(response.steamid)
        else:
            print('Could not resolve steamid for {0}'.format(id))

with open('players.json', 'w') as players_file:
    json.dump(list(resolved_ids), players_file)

