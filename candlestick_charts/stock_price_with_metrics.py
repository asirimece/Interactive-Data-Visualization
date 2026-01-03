"""
Interactive Stock Price Visualization — Candlestick Chart with Financial Metrics

This script creates an interactive candlestick chart to visualize historical
stock price movements for a large technology company. In addition to price
data, key financial metrics are overlaid on secondary axes to support
investment-oriented analysis.

The visualization is designed to enable temporal exploration and comparison
between price dynamics and underlying financial indicators through interactive
navigation and selective visibility.

Key features:
- Candlestick representation of open, high, low, and close prices
- Overlay of financial metrics on secondary y-axes
- Interactive legend for toggling metric visibility
- Hover tooltips for detailed inspection of prices and metrics
- Panning and zooming for temporal exploration
- Optional range selection for focused time-window analysis

Technologies:
- pandas for data loading and preprocessing
- Bokeh for interactive visualization and layout
"""


import pandas as pd
from bokeh.plotting import figure
from bokeh.io import output_file, save, show
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, CDSView, BooleanFilter, \
    HoverTool, LinearAxis, NumeralTickFormatter, Range1d, RangeTool, BoxZoomTool

from bokeh.layouts import gridplot
from bokeh.transform import factor_cmap
from bokeh.models.annotations import Label
from bokeh.palettes import Blues3
from bokeh.resources  import settings


# Task 1: Prepare the data

stock_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTiM1scE44za7xyuheW_FrUkdSdOKipDgDOWa_03ixmJCWK_ReSqhjzax66nNHyDKARXWIXgFI_EW9X/pub?gid=1661368486&single=true&output=csv'
stock = pd.read_csv(stock_url)

metrics_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRDaf4y17OWjQqxODuxA4q4hsvXRkSqN0na1KtTIpvOZUdc7xHbrkhcygFfDIyVQWI2UbC3YcKUbser/pub?gid=981872466&single=true&output=csv'
metrics = pd.read_csv(metrics_url)

stock['Date'] = pd.to_datetime(stock['Date'])
metrics['Quarter Ended'] = pd.to_datetime(metrics['Quarter Ended'])


# Task 2: Create candlestick chart 
def create_candlestick_chart(symbol):

    source = ColumnDataSource(stock[stock['Symbol'] == symbol])
    
    x_range = Range1d(stock['Date'].min(), stock['Date'].max())
    p = figure(
        width=800, 
        height=400, 
        title=symbol, 
        x_range=x_range,
        x_axis_type='datetime', 
        x_axis_location='above',
        background_fill_color = '#ffffff',
        border_fill_color = '#ffffff',
        tools="pan,wheel_zoom,reset,save", 
        toolbar_location='right',
    )
    
    p.y_range.start = stock['Close'].min() * 0.9
    p.y_range.end = stock['Close'].max() * 1.1
    
    stock_filtered = stock[stock['Symbol'] == symbol]
    inc = stock_filtered['Close'] > stock_filtered['Open']
    dec = ~inc
    inc_view = CDSView(source=source, filters=[BooleanFilter(inc.tolist())])
    dec_view = CDSView(source=source, filters=[BooleanFilter(dec.tolist())])

    w = 24*60*60*1000
    stock_segment = p.segment(
        x0='Date', y0='Low', x1='Date', y1='High', 
        source=source, view=inc_view, color='#00ff00'
    )
    
    stock_inc = p.vbar(
        x='Date', top='Close', bottom='Open', width=w*2, 
        source=source, view=inc_view, fill_color='#00ff00', line_color=None
    )

    stock_dec = p.vbar(
        x='Date', top='Open', bottom='Close', width=w*2, 
        source=source, view=dec_view, fill_color='#ff0000', line_color=None
    )
    
    y_volume = Range1d(start=0, end=stock['Volume'].max() * 1.1)
    p.extra_y_ranges['volume'] = y_volume
    y_volume_axis = LinearAxis(y_range_name='volume', axis_label='Volume', formatter=NumeralTickFormatter(format='0.0a'))
    p.add_layout(y_volume_axis, 'right')
    
    stock_volume = p.vbar(
        x='Date', top='Volume', bottom=0, width=w, 
        source=source, fill_color='#1f77b4', line_color=None, y_range_name='volume'
    )
    
    # hover tool
    hover_stock = HoverTool()
    hover_stock.tooltips=[    
        ('Date', '@Date{%F}'),
        ('Open', '@Open{0,0.00}'),
        ('Close', '@Close{0,0.00}'),
        ('High', '@High{0,0.00}'),
        ('Low', '@Low{0,0.00}'),
        ('Volume', '@Volume{0,0.00}'),
    ]
    
    hover_stock.formatters={
      '@Date': 'datetime',
    }
    
    hover_stock.renderers = [stock_inc, stock_dec]
    p.add_tools(hover_stock)

    p.output_backend = 'svg'
    
    return p


# Task 3: Add metrics chart to candlestick chart
def add_metrics_plot(main_plot, symbol):
    source = ColumnDataSource(metrics[metrics['Symbol'] == symbol])
    
    main_plot.extra_y_ranges['pe'] = Range1d(start=metrics['PE Ratio'].min() * 0.9, end=metrics['PE Ratio'].max() * 1.1)
    main_plot.extra_y_ranges['eps'] = Range1d(start=metrics['EPS Growth'].min() * 0.9, end=metrics['EPS Growth'].max() * 1.1)
    
    y_pe_axis = LinearAxis(y_range_name='pe', axis_label='PE Ratio', visible=False)
    y_eps_axis = LinearAxis(y_range_name='eps', axis_label='EPS Growth', visible=False)
    
    main_plot.add_layout(y_pe_axis, 'right')
    main_plot.add_layout(y_eps_axis, 'right')
    
    pe_l = main_plot.line(
        x='Quarter Ended', y='PE Ratio', source=source, y_range_name='pe',
        legend_label='PE Ratio', line_color='#00ff00', line_alpha=0.5, line_dash=[4, 2], muted_color='#00ff00', muted_alpha=0.1
    )
    
    pe_c = main_plot.circle(
        x='Quarter Ended', y='PE Ratio', source=source, y_range_name='pe',
        legend_label='PE Ratio', fill_color=None, line_color='#00ff00', size=6, muted_color='#00ff00', muted_alpha=0.1
    )
    
    eps_l = main_plot.line(
        x='Quarter Ended', y='EPS Growth', source=source, y_range_name='eps',
        legend_label='EPS Growth', line_color='#ff0000', line_alpha=0.5, line_dash=[4, 2], muted_color='#ff0000', muted_alpha=0.1
    )
    
    eps_c = main_plot.circle(
        x='Quarter Ended', y='EPS Growth', source=source, y_range_name='eps',
        legend_label='EPS Growth', fill_color=None, line_color='#ff0000', size=6, muted_color='#ff0000', muted_alpha=0.1
    )
    
    main_plot.legend.click_policy = 'mute'
    
    metrics_hover = HoverTool()

    metrics_hover.tooltips=[
        ('Quarter', '@{Quarter Ended}{%F}'),
        ('PE Ratio', '@{PE Ratio}{0,0.00}'),
        ('EPS Growth', '@{EPS Growth}{0,0.00}'),
    ]
    metrics_hover.formatters={
      '@Quarter Ended': 'datetime',
    }
    metrics_hover.mode='mouse' 
    metrics_hover.renderers = [pe_c, eps_c]                
    main_plot.add_tools(metrics_hover)
    
    metrics_plot = main_plot   # Fix the return statement here
    return metrics_plot




#Task 4: Add range selection plot
def add_select_range(main_plot, symbol):
    stock_source = ColumnDataSource(stock[stock['Symbol'] == symbol])
    
    x_range = main_plot.x_range

    select = figure(
        height=100, width=800, x_axis_type='datetime',
        y_axis_type=None, tools="", toolbar_location=None, background_fill_color="#ffffff",
        x_range=x_range
    )

    range_tool = RangeTool(x_range=main_plot.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    
    select.line('Date', 'Close', source=stock_source)
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    
    main_plot.add_tools(range_tool)
    main_plot.toolbar.active_multi = None


    return main_plot, x_range, select


# Example output

symbol = 'AAPL'
p_candlestick = create_candlestick_chart(symbol)
p_combined = add_metrics_plot(p_candlestick, symbol)
p_candlestick, x_range, select = add_select_range(p_combined, symbol)

layout = column(p_combined, select)
output_file('dvc_ex2.html', mode='inline')
save(layout)