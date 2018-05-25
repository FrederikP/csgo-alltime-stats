from __future__ import print_function

import json
from itertools import groupby

from dotmap import DotMap

with open('all_maps.json') as all_maps_file:
    all_maps = json.load(all_maps_file)

all_maps_2 = []

for element in all_maps:
    the_map = DotMap(element)
    all_maps_2.append(the_map)

all_maps = all_maps_2

player_scores = [player for the_map in all_maps for player in the_map.team1.players + the_map.team2.players]

sorted_by_name = sorted(player_scores, key=lambda x: x.name)

aggregated = DotMap()

for key, scores in groupby(sorted_by_name, key=lambda x: x.name):
    scores = [score for score in scores]
    aggregated[key].number_of_matches = len(scores)
    try:
        aggregated[key].kill_death_ratio = sum(score.kills for score in scores) / sum(score.deaths for score in scores)
    except ZeroDivisionError:
        aggregated[key].kill_death_ratio = '∞'

sorted_by_number_matches = sorted(aggregated.items(), key=lambda x: x[1].number_of_matches, reverse=True)

for entry in sorted_by_number_matches[:10]:
    print('{} -> Number of Matches: {}, K/D : {:.2f}'.format(entry[0], entry[1].number_of_matches, entry[1].kill_death_ratio))
