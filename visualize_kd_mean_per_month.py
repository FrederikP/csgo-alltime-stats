import json
from itertools import groupby, cycle

import numpy as np
from bokeh.models import ColumnDataSource
from bokeh.palettes import Category10
from bokeh.plotting import figure, output_file, show
from bokeh.transform import jitter
from dotmap import DotMap
from pandas import DataFrame, Grouper, to_datetime

from csgo_alltime_stats.db import CsgoDatabase


db = CsgoDatabase()
map_data = db.get_all_matches()


def color_gen():
    yield from cycle(Category10[10])

player_scores = [DotMap({'score': player, 'date': the_map.date}) for the_map in map_data for player in the_map.team1.players + the_map.team2.players]

flattened = []
for score in player_scores:
    entry = score.score
    entry.date = score.date
    # Avoid division by zero by messing with the data
    entry.kd = entry.kills / (entry.deaths if entry.deaths > 0 else 1)
    flattened.append(entry)


p = figure(plot_width=1400, plot_height=600, x_axis_type='datetime', title="Kills per Match (avg)")

colors = color_gen()
sorted_by_name = sorted(flattened, key=lambda x: x.name)
for key, scores in groupby(sorted_by_name, key=lambda x: x.name):
    scores = [score.toDict() for score in scores]
    if len(scores) > 50:
        df = DataFrame(data=scores)

        df.date = to_datetime(df.date,format='%Y-%m-%d %H:%M:%S %Z')
        df.set_index('date', inplace=True)
        df = df.resample('1d').mean()
        df = df.rolling('30d').mean()
        df = df.interpolate()
        source = ColumnDataSource(df)

        p.line(x='date', y='kills', legend=key, source=source, color=next(colors), line_width=4)


show(p)
