from dotmap import DotMap
from tinydb import Query, TinyDB

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