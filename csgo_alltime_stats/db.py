from dotmap import DotMap
from tinydb import Query, TinyDB

API_KEY_ID = 'api_key'
COOKIE_ID = 'cookie'

class CsgoDatabase():

    def __init__(self, file_path='csgo-alltime-stats.db'):
        self._db = TinyDB(file_path)

        self._match_table = self._db.table('matches')
        self._player_table = self._db.table('players')

    def get_all_matches(self):
        all_matches = self._match_table.all()
        return [DotMap(match) for match in all_matches]

    def get_all_players(self):
        all_players = self._player_table.all()
        return [DotMap(player) for player in all_players]
    
    def get_api_key(self):
        api_key_query = Query()
        api_key_entry = self._db.get(api_key_query.id == API_KEY_ID)
        api_key = None
        if api_key_entry:
            api_key = api_key_entry['key']
        return api_key
    
    def set_api_key(self, api_key):
        api_key_query = Query()
        self._db.upsert({'id': API_KEY_ID, 'key': api_key}, api_key_query.id == API_KEY_ID)
    
    def get_cookie(self):
        cookie_query = Query()
        cookie_entry = self._db.get(cookie_query.id == COOKIE_ID)
        cookie = None
        if cookie_entry:
            cookie = cookie_entry['data']
        return cookie

    def set_cookie(self, cookie):
        cookie_query = Query()
        self._db.upsert({'id': COOKIE_ID, 'data': cookie}, cookie_query.id == COOKIE_ID)

    def get_match(self, match_date):
        match_query = Query()
        return self._match_table.search(match_query.date == match_date)

    def add_match(self, match):
        self._match_table.insert(match)

    def get_player_by_steamid(self, steamid):
        player_query = Query()
        return self._player_table.get(player_query.id == steamid)

    def get_player_by_profile_id(self, profile_id):
        player_query = Query()
        return self._player_table.get(player_query.profile_id == profile_id)

    def add_player(self, steamid, profile_id):
        self._player_table.insert({'id': steamid, 'profile_id': profile_id})
