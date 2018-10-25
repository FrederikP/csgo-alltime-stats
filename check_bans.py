import requests
from dotmap import DotMap
from tinydb import Query, TinyDB

database_file = 'csgo-alltime-stats.db'
db = TinyDB(database_file)

match_table = db.table('matches')
player_table = db.table('players')

player_ids = [player['id'] for player in player_table.all()]


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

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

id_resolve_url = "http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={0}&steamids={1}"

results = []

for ids in chunks(player_ids, 100):
    response = DotMap(requests.get(id_resolve_url.format(api_key, ','.join(ids))).json())
    results.extend(response.players)

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