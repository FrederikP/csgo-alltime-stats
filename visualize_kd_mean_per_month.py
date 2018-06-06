import json
from itertools import groupby, cycle

import numpy as np
from bokeh.models import ColumnDataSource
from bokeh.palettes import Category10
from bokeh.plotting import figure, output_file, show
from bokeh.transform import jitter
from dotmap import DotMap
from pandas import DataFrame, Grouper, to_datetime

def color_gen():
    yield from cycle(Category10[10])

with open('all_maps.json') as data_file:
    map_data = json.load(data_file)


map_data_2 = []

for element in map_data:
    the_map = DotMap(element)
    map_data_2.append(the_map)

map_data = map_data_2

player_scores = [DotMap({'score': player, 'date': the_map.date}) for the_map in map_data for player in the_map.team1.players + the_map.team2.players]

flattened = []
for score in player_scores:
    entry = score.score
    entry.date = score.date
    # Avoid division by zero by messing with the data
    entry.kd = entry.kills / (entry.deaths if entry.deaths > 0 else 1)
    flattened.append(entry)


p = figure(plot_width=1400, plot_height=600, x_axis_type='datetime', title="K/D Mean")

colors = color_gen()
sorted_by_name = sorted(flattened, key=lambda x: x.name)
for key, scores in groupby(sorted_by_name, key=lambda x: x.name):
    scores = [score.toDict() for score in scores]
    if len(scores) > 50:
        df = DataFrame(scores)

        df.date = to_datetime(df.date,format='%Y-%m-%d %H:%M:%S %Z')
        df.index = df.date

        group = df.groupby(Grouper(freq='3M'))
        source = ColumnDataSource(group)

        print(source.column_names)

        p.line(x='date', y='kd_mean', legend=key, source=source, color=next(colors))


show(p)
