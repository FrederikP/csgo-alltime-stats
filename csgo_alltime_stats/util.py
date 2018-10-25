import requests


def get_api_key(db):
    api_key = db.get_api_key()
    if not api_key:
        key_invalid = True
        while key_invalid:
            api_key = input('Enter steam api key (get it at  https://steamcommunity.com/dev/apikey): ')
            key_invalid = requests.get('http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key={0}&appid=218620'.format(api_key)).status_code == 401
        db.set_api_key(api_key)
    return api_key
