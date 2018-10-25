import numpy as np
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, output_file, show
from bokeh.transform import jitter
from dotmap import DotMap
from pandas import DataFrame, Grouper, to_datetime
from csgo_alltime_stats.db import CsgoDatabase


db = CsgoDatabase()
map_data = db.get_all_matches()

data = [{'date': map_entry.date, 'rounds': map_entry.team1.score + map_entry.team2.score} for map_entry in map_data]

df = DataFrame(data)

df.date = to_datetime(df.date,format='%Y-%m-%d %H:%M:%S %Z')
df.index = df.date

group = df.groupby(Grouper(freq='M')).sum()
source = ColumnDataSource(group)

print(source.column_names)

p = figure(plot_width=1400, plot_height=600, x_axis_type='datetime', title="Rounds")

p.line(x='date', y='rounds',  source=source, alpha=0.3)


show(p)