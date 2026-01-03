"""
Geospatial Visual Analytics — Interactive Company Map with Animation

This script builds an interactive geospatial visualization to explore the
geographic distribution of technology companies across the United States.
Aggregated company metrics are encoded visually to support spatial comparison
and temporal analysis.

The visualization integrates interactive selection, filtering, and animation
to allow users to investigate how company characteristics evolve over time and
vary across locations.

Key features:
- Geographic scatter visualization of company locations
- Visual encoding of company metrics using marker size and color
- Tap-based interaction to reveal detailed information in linked subplots
- Slider-based filtering to restrict data by market capitalization
- Time-based animation illustrating changes across multiple years
- Coordinated updates between main view and detail views

Technologies:
- pandas for data preparation and aggregation
- Bokeh for interactive plotting, widgets, and animation callbacks
"""


import pandas as pd
import numpy as np
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import Div, Range1d, WMTSTileSource, ColorBar
from bokeh.plotting import figure
from bokeh.transform import log_cmap
from bokeh.palettes import Turbo256
from bokeh.models import ColumnDataSource, HoverTool, LogColorMapper, Select, Label, Button, Slider, Text, ColorBar, NumeralTickFormatter, LogTicker


url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vStUglUExt-kL-fVYcit-h4-V1Vg3HUkvDEV6KwZGw_6r46duWKYx9ZGI5Bctkrv05DF0nEWYqR14Qb/pub?gid=860901304&single=true&output=csv'
us_company_map = pd.read_csv(url)

k = 6378137 # Earth radius in meters
us_company_map["x"] = us_company_map.lng * (k * np.pi/180.0)
us_company_map["y"] = np.log(np.tan((90 + us_company_map.lat) * np.pi/360.0)) * k

tile_options = {
    'url': 'http://tile.stamen.com/terrain/{Z}/{X}/{Y}.png',
    'attribution': """
        Map tiles by <a href="http://stamen.com">Stamen Design</a>, under
        <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>.
        Data by <a href="http://openstreetmap.org">OpenStreetMap</a>,
        under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.
    """
}
tile_source = WMTSTileSource(**tile_options)

global main_source, sub_source
main_source = ColumnDataSource()
sub_source = ColumnDataSource()

year = 2022
city = 'San Jose'
market_cap_lower = 0

def create_df(year, city, market_cap_lower, main=True):
    
    df = us_company_map[['Symbol', 'City', 'x', 'y',                          
                         f'Market Cap {year}', f'Employees {year}']].copy()
    
    df.rename(columns={f'Market Cap {year}': 'Market Cap', 
                       f'Employees {year}': 'Employees'}, inplace=True)

    df.loc[df['Market Cap'] < market_cap_lower, ['Symbol', 'Market Cap', 'Employees']] = np.nan
    
    if main:
        main_df = df.groupby('City').agg({
            'x': 'mean',
            'y': 'mean',
            'Symbol': 'count',
            'Market Cap': 'sum',
            'Employees': 'sum'
        }).reset_index()
        main_df['circle_size'] = np.log1p(main_df['Employees'])
        return main_df
    else:
        sub_df = df[df['City'] == city].copy()
        sub_df['circle_size'] = np.log1p(sub_df['Employees'])
        return sub_df

main_df = create_df(year, city, market_cap_lower)
sub_df = create_df(year, city, market_cap_lower, main=False)

main_source.data = main_df
sub_source.data = sub_df


def plot_city(main_df, tile_source):

    main_source.data = main_df
    plot = figure(
        x_range=(-14000000, -7500000), y_range=(2750000, 6250000),
        x_axis_type="mercator", y_axis_type="mercator",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll='wheel_zoom',
        width=1000, height=600,
        title="US Tech Companies Distribution",
        toolbar_location="above"
    )

    plot.add_tile(tile_source)
    
    color_mapper = log_cmap(
        field_name='Market Cap', 
        palette=Turbo256, 
        low=min(main_df['Market Cap']), 
        high=max(main_df['Market Cap'])
    )
    
    plot.circle(
        x='x', y='y', 
        size='circle_size', 
        source=main_source,
        fill_color=color_mapper,
        fill_alpha=0.7,
        line_color=None,
        hover_fill_color='black'
    )

    color_bar = ColorBar(
        color_mapper=color_mapper['transform'], 
        location=(0, 0),
        ticker=LogTicker(),
        formatter=NumeralTickFormatter(format="0,0")
    )

    plot.add_layout(color_bar, 'right')
    
    hover_tool = HoverTool(
        tooltips=[
            ("City", "@City"),
            ("Number of companies", "@Symbol"),
            ("Total Market Cap", "@{Market Cap}{0,0}"),
            ("Total Employees", "@{Employees}{0,0}")
        ]
    )
    
    plot.add_tools(hover_tool)

    return plot

main_plot = plot_city(main_df, tile_source)

## 2.2 Define a function to draw the subplot

def plot_company(sub_df):
    
    main_source = ColumnDataSource(main_df)
    sub_source = ColumnDataSource(sub_df)
    
    x_range = (sub_df['Employees'].min() - 100, sub_df['Employees'].max() + 100)
    y_range = (sub_df['Market Cap'].min() - 10, sub_df['Market Cap'].max() + 10)

    p = figure(
        width=450,
        height=400, 
        min_border=20,
        min_border_top=45,
        x_range=x_range,
        y_range=y_range,
        x_axis_type="log",
        y_axis_type="log",
        y_axis_location="right", 
        title= f"Companies in {city}",
        tools='pan, wheel_zoom, reset', 
        toolbar_location='right'
    )
    p.xaxis.axis_label = 'Number of Employees'
    p.yaxis.axis_label = 'Market Cap in Billion USD'
    p.xaxis.formatter = NumeralTickFormatter(format='0,0 a')
    p.yaxis.formatter = NumeralTickFormatter(format='0,0.00 a')
    p.background_fill_color = "#fafafa"

    color_mapper = log_cmap(
        field_name='Market Cap',
        palette=Turbo256,
        low=sub_df['Market Cap'].min(),
        high=sub_df['Market Cap'].max()
    )

    
    c = p.circle(
        x='Employees',
        y='Market Cap',
        size='circle_size', 
        alpha=0.5,
        fill_color=color_mapper, 
        line_color="white", 
        line_width=1.5, 
        source=sub_source,
    )
    
    hover_company = HoverTool()
    hover_company.tooltips=[
        ('Symbol', '@Symbol'),
        ('Market Cap', '@Market Cap{0,0.00 a}'),
        ('Employees', '@Employees{0,0}')
    ]
    hover_company.renderers = [c]     
    p.add_tools(hover_company)

    t = Text(
        x='Employees', 
        y='Market Cap', 
        text='Symbol',
        text_baseline='middle', 
        text_align='center',
        text_font_size='8pt',
        text_color='black'
    )
    
    p.add_glyph(sub_source, t)

    return p

subplot = plot_company(sub_df)


## 3.1 Define a callback function for the tap tool in the main plot

def tap_update(attr, old, new):
    if new:
        global city
        city_index = new['1d']['indices'][0]
        if isinstance(city_index, int):
            city = main_source.data['City'][city_index]
            sub_df = create_df(year, city, market_cap_lower, main=False)
            sub_source.data = sub_df
            subplot.title.text = f"Companies in {city}"

main_plot.renderers[1].data_source.selected.on_change('indices', tap_update)


## 3.2 Add a slider and define a callback function for it to filter companies by the market cap

slider = Slider(
    title='Market Cap Lower Bound',
    start=0,
    end=main_df['Market Cap'].max(),
    step=100,
    value=market_cap_lower,
    format="0,0"
)


def slider_update(attr, old, new):
    global market_cap_lower
    market_cap_lower = new
    main_source.data = create_df(year, city, market_cap_lower).to_dict('list')
    sub_source.data = create_df(year, city, market_cap_lower, main=False).to_dict('list')

slider.on_change('value', slider_update)


btn = Button(
    label='Play',
    width=60
)

## 4.1 Define a function to update the elements that change along with the year.

def update_year():
    global year, label
    
    if year >= 2022:
        year = 2018
    else:
        year += 1
    print(f"Updating year to {year}")
    
    label.text = str(year)
    
    main_df = create_df(year, city, market_cap_lower)
    slider.end = main_df['Market Cap'].max()
    
    if main_df['Market Cap'].min() <= 0: 
        main_df = main_df[main_df['Market Cap'] > 0] # keep only the rows with Market Cap greater than 0
    sub_df = create_df(year, city, market_cap_lower, main=False)
    
    if sub_df['Market Cap'].min() <= 0: 
        sub_df = sub_df[sub_df['Market Cap'] > 0] 
    main_source.stream(main_df.to_dict('list', into=dict, orient='index'), rollover=len(main_df))
    sub_source.stream(sub_df.to_dict('list', into=dict, orient='index'), rollover=len(sub_df))
    
callback = None

## 4.2 Define a function to wrap the update function in a periodic callback.

def play():
    print("Button has been clicked.")
    
    global callback, year, btn, label
    
    if btn.label == 'Play':
        btn.label = 'Pause'
        callback = curdoc().add_periodic_callback(update_year, 1000)
        print("Starting animation")
    else:
        btn.label = 'Play'
        curdoc().remove_periodic_callback(callback)
        print("Stopping animation")

btn.on_click(play)

# (Optional) Add a text div to explain your app to the user.
div = Div(
    text="""Circle color: Market Cap
            Circle size: Employees
            Move the slider above to filter companies by the market cap.
            Click play button below to show the changes of Market.
            Cap and Employees over years."""
)

layout = row([main_plot, column(subplot, slider, div, btn)])
curdoc().add_root(layout)
curdoc().title = 'US Tech Companies Distribution by City'

