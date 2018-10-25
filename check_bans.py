from __future__ import print_function

import progressbar
import requests
from dotmap import DotMap

from csgo_alltime_stats.db import CsgoDatabase
from csgo_alltime_stats.util import get_api_key

db = CsgoDatabase()

player_ids = [player['id'] for player in db.get_all_players()]


api_key = get_api_key(db)

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

id_resolve_url = "http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={0}&steamids={1}"

results = []
with progressbar.ProgressBar(max_value=len(player_ids)) as bar:
    for ids in chunks(player_ids, 100):
        response = DotMap(requests.get(id_resolve_url.format(api_key, ','.join(ids))).json())
        results.extend(response.players)
        bar.update(bar.value + len(ids))

vac_banned = 0
game_banned = 0

for player in results:
    if player.VACBanned:
        vac_banned += 1
    elif player.NumberOfGameBans > 0:
        game_banned += 1

print('Total players in my games: {0}'.format(len(results)))
print('Players with VAC bans: {0}'.format(vac_banned))
print('Players with game bans: {0}'.format(game_banned))
