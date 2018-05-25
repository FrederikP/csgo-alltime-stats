from __future__ import print_function

import json

from itertools import groupby

with open('playerscores.json') as playerscores_file:
    player_scores = json.load(playerscores_file)

sorted_by_name = sorted(player_scores, key=lambda x: x['Player Name'])

aggregated = {}

for key, group in groupby(sorted_by_name, key=lambda x: x['Player Name']):
    group = [entry for entry in group]
    aggregated[key] = {
        'Number of Matches': len(group),
        'K/D': '{:.1%}'.format(sum(int(entry['K']) for entry in group) / sum(int(entry['D']) for entry in group))
    }

sorted_by_number_matches = sorted(aggregated.items(), key=lambda x: x[1]['Number of Matches'], reverse=True)

for entry in sorted_by_number_matches[:10]:
    print('{} -> Number of Matches: {}, K/D : {}'.format(entry[0], entry[1]['Number of Matches'], entry[1]['K/D']))
