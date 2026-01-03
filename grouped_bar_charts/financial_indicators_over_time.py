"""
Interactive Financial Data Visualization — Grouped Bar Charts

This script creates an interactive grouped bar chart to visualize
multiple financial indicators for large technology companies over
time. The visualization is designed to support comparison across
years, quarters, and financial metrics.

Key features:
- Nested categorical axes for time and financial items
- Interactive hover tooltips for precise value inspection
- Color encoding to distinguish financial metrics
- Export to a standalone HTML file for interactive viewing

Technologies:
- pandas for data preparation
- Bokeh for interactive visualization
"""


import pandas as pd
from bokeh.plotting import figure
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, FactorRange, NumeralTickFormatter
from bokeh.layouts import gridplot
from bokeh.transform import factor_cmap
from bokeh.models.annotations import Label
from bokeh.palettes import Blues3

# Task 1: Prepare the Data

## 1.1: Use pandas to read a csv file into a dataframe from a link
url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQdNgN-88U31tk1yQytaJdmoLrxuFn1LnbwTubwCd8se2aHh8656xLLHzxHSoiaXMUu8rIcu6gMj5Oq/pub?gid=1242961990&single=true&output=csv'
MAGMA_financials = pd.read_csv(url)


## 1.2: Inspect the columns in the dataframe
subset = ['Net Income', 'Operating Expenses', 'Selling, General & Admin']


## 1.3: Create a nested categorical coordinate
years = ['2019', '2020', '2021', '2022']
quarters = ['Q1', 'Q2', 'Q3', 'Q4']
x = [(year, quarter, item) for year in years for quarter in quarters for item in subset]


## 1.4: Use ColumnDataSource to generate data sources
def create_source(symbol:str) -> ColumnDataSource:
    """
    Creates source based on symbol string.
    :param symbol: String of Company Stock
    :return: Column Datasource
    """

    # Select the company's data from the dataframe and flatten it
    data = MAGMA_financials[MAGMA_financials.Symbol == symbol][subset]
    data_flat = data.stack().values
    y = list(data_flat)

    y_label = ['Net Income', 'Operating Expenses', 'Selling, General & Admin'] * 16
    data = {'x_values':x,'y_values':y,'label':y_label}

    return ColumnDataSource(data=data)

# Create a source for each company and put them in a dictionary in the format sources = { symbol : source, ... }
symbols = MAGMA_financials.Symbol.unique()
sources = {symbol:create_source(symbol) for symbol in symbols}


# Task 2: Draw the Bar Chart

## 2.1: Configure the settings of the figure

# Set the width and hight of the figure. You'll add a hover tool later, for now set the tools to empty
options = dict(width = 700, height = 200, tools='')


def draw_bar_chart(symbol:str):
    """
    For reusability, you'll define a function for drawing the bar chart This function takes a company symbol as an
    argument and returns the corresponding barchart
    :param symbol:
    :return:
    """
    p = figure(
        # Use FactorRange to create the x_range
        x_range = FactorRange(*x) ,
        title = symbol,
        **options
    )

    # Hide the x grid line, Pad the x range
    p.xgrid.grid_line_color = None
    p.x_range.range_padding = 0.1

    # You'll use the legend group to show the item names of the bars so hide x labels and tick lines
    p.xaxis.major_label_text_font_size = '0pt'
    p.xaxis.major_tick_line_color = None

    # Set the y axis label to 'millions USD'
    p.yaxis.axis_label = 'millions USD'

    # Use NumeralTickFormatter to a comma as the thousand separator
    p.yaxis.formatter = NumeralTickFormatter(format='0,0')


    ## 2.2: Configure the bar glyphs
    p.vbar(
            # Draw the bars from the source corresponding to the company symbol
            x = 'x_values' , top = 'y_values' , width = 1 ,
            source = sources.get(symbol),

            # Use the column 'label' in the data source as the legend group
            legend_group = 'label' ,
            line_color = 'White',

            # Use factor_cmap to assign colors to bars according to their item names
            fill_color=factor_cmap(
                'label' , palette = 'Blues3' ,
                factors = subset , start = 1 , end = 3
            )
    )


    ## 2.3: Add a hover tool
    p.add_tools(HoverTool(tooltips=[
        ('','@x_values: @y_values{0,0}')
    ]))


    ## 2.4: Add a legend

    # Set the legend label and glyph sizes
    p.legend.label_text_font_size = '8pt'
    p.legend.label_height = 10
    p.legend.glyph_height = 10
    p.legend.glyph_width = 20
    p.legend.background_fill_alpha = 0.1

    # Set the legend orientation and location
    p.legend.orientation = 'horizontal'
    p.legend.location = 'top_left'

    # Set the output_backend to 'svg' to preserve the resolution when zooming in
    p.output_backend = "svg"

    return p


## 2.5(optional): Add a text label

def make_label(time:str, number:str) -> Label:
    label = Label(

        # Set the postion of the label (x, y) using screen units
        x=550,
        y=40,
        x_units='screen',
        y_units='screen',

        # Set the text content, font size, color, align, background
        text=f'{time}\nlayoffs\n{number}',
        text_font_size='8pt',
        text_font_style='italic',
        text_color='grey',
        text_align='left',
        background_fill_color='White',
        background_fill_alpha=0.6
    )

    return label


# Make a dictionary of the text labels with the provided time and number information
labels = {
    'AMZN': make_label('Jan 2023', '18,000'),
    'META': make_label('Nov 2022', '11,000'),
    'GOOGL': make_label('Jan 2023', '12,000'),
    'MSFT': make_label('Jan 2023', '10,000'),
}

## 2.6(optional): Put two bar charts in a gridplot vertically for comparison

p_AMZN = draw_bar_chart('AMZN')
p_AMZN.add_layout(labels.get('AMZN'))

p_MSFT = draw_bar_chart('MSFT')
p_MSFT.add_layout(labels.get('MSFT'))

p = gridplot([
    [p_AMZN], [p_MSFT]
], toolbar_location = None)


## 2.7: Save the bar chart(s) to a html file with the filename 'dvc_ex1.html'
output_file('dvc_ex1.html')
save(p)


