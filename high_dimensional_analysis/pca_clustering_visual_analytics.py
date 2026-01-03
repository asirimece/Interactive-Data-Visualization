"""
High-Dimensional Data Exploration — PCA-Based Visual Analytics

This script implements an interactive visual analytics application for
exploring a high-dimensional dataset of technology companies. Dimensionality
reduction is performed using Principal Component Analysis (PCA), and clustering
is applied in the reduced feature space to reveal structural patterns in the data.

The visualization combines multiple linked views to support exploratory
analysis, enabling users to inspect global distributions as well as
selection-specific statistics through direct interaction.

Key features:
- Dimensionality reduction from high-dimensional feature space using PCA
- Clustering of data points in the reduced space
- Scatter plot visualization of principal components
- Dynamic color mapping based on user-selected features
- Lasso selection for interactive subset exploration
- Linked histograms showing feature distributions for all vs. selected data
- Interactive widgets for feature selection and view updates

Technologies:
- pandas and NumPy for data processing
- scikit-learn for PCA and clustering
- Bokeh for interactive plotting, widgets, and callbacks
"""


import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_object_dtype

from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
from sklearn import cluster
from sklearn.impute import SimpleImputer

from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, HoverTool, LassoSelectTool, Select, LinearColorMapper, ColorBar
from bokeh.palettes import TolRainbow, Turbo256
from bokeh.transform import factor_cmap, linear_cmap, log_cmap


pca_data_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQFGt2FAUh_Fb7XAtYasA95ut8X_4a6sqizwcF-QFHdxULsPCf0kXhqn3wJdxNE2Ogf-f1qwyeOIySw/pub?gid=1323235&single=true&output=csv'
pca_data = pd.read_csv(pca_data_url)

pca_data.head()
pca_data.tail()

## 1.1 Principal component analysis (PCA)

def pca(df):
    
    # select the numeric features
    #X = df.iloc[:, 5:]  # column 5 onward
    X = df.select_dtypes(include=np.number)
    
    # use MinMaxScaler to scale the features
    X_scaled = MinMaxScaler().fit_transform(X)
    
    # use SimpleImputer to fill in the missing values with the mean value
    imp = SimpleImputer(strategy='mean')
    X_imp = imp.fit_transform(X_scaled)
    
    # perform PCA to project the features into 2 components
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_imp)

    # append the 2 principal components to the dataframe
    # convert non-numeric values to NaN
    X = X.apply(pd.to_numeric, errors='coerce')
    
    df['PCA 1'] = X_pca[:, 0]
    df['PCA 2'] = X_pca[:, 1]
    return df


# 1.2 Clustering

def clustering(df, n_clusters=2):
    
    # select the principal components
    X_pca = df[['PCA 1', 'PCA 2']]
    
    # sets the random seed to 0 so that the result is reproducible
    np.random.seed(0)

    # use MiniBatchKMeans to perform the clustering
    model = cluster.MiniBatchKMeans(n_clusters=n_clusters, n_init=2)
    model.fit(X_pca)
    
    # append the cluster labels to the dataframe
    y_pred = model.labels_.astype(str)
    
    df['Cluster'] = y_pred

    return df


## 2.1 Define a function to create a color map for the selected feature.

def create_cmap(df, col):
    # create a discete color mapper (factor_cmap) for categorical features
    if is_object_dtype(df[col]):
        l = np.unique(df[col].astype(str))
       
        if len(l) == 2:
            palette = ["#000000", "#FFFFFF"]
        else:
            palette = Turbo256[len(l)]
            
        mapper = factor_cmap(
            col, 
            palette=palette, 
            factors=l
        )
        # (Optional) make a dictionary of category:color pairs
        # it will be used to synchronize the colors in the main plot and the (optional) bar chart
        cat_palette = dict(zip(l, palette))
    # create a continuous color mapper (linear_cmap or log_cmap) for numeric features
    # https://docs.bokeh.org/en/3.1.0/docs/examples/basic/data/color_mappers.html
    elif is_numeric_dtype(df[col]):
        if min(df[col]) >= 0:
            mapper = log_cmap(
                field_name=col,
                palette=Turbo256,
                low=min(df[col]),
                high=max(df[col])
            )
        else:
             mapper = linear_cmap(
                field_name=col,
                palette=Turbo256,
                low=min(df[col]),
                high=max(df[col])
            )
        cat_palette = None
    
    return mapper, cat_palette


## 2.2 Define a function to plot the principal components.

def plot_pca(source, df, ft_selected):
    
    c = ft_selected
    p = figure(
        title=f'PCA with Color Map on {c}', 
        tools='hover, pan, wheel_zoom, lasso_select, reset',
        tooltips=[('', '@Symbol')],
        toolbar_location='below', 
        width=500,
        height=450        
    )
    # use the function in 2.1 to create a color map for the selected feature
    mapper, _ = create_cmap(df, c)
    r = p.circle(
        # use the 2 principal components as x and y
        x='PCA 1', 
        y='PCA 2', 
        size=8,
        # apply the color map on the glyphs
        fill_color= mapper,
        alpha=0.4, 
        line_color=None,
        # the source will have a column named 'label'
        # which is a copy of the selected feature
        # if the selected feature is categorical
        # this 'label' column will be used to generate the legend
        legend_field= 'label',
        source=source,
    )    
    # p.sizing_mode = 'stretch_both'
    p.background_fill_color = "#fafafa"
    p.xaxis.axis_label = 'PCA component 1'
    p.yaxis.axis_label = 'PCA component 2'
    
    if is_numeric_dtype(df[c]):
        color_mapper = LinearColorMapper(palette=Turbo256, low=min(df[c]), high=max(df[c]))
        color_bar_location = (0, 0)
        color_bar_orientation = 'vertical'

        color_bar = ColorBar(color_mapper=color_mapper, orientation=color_bar_orientation)
        p.add_layout(color_bar, 'left')    
        
        p.legend.items = []
    # for a categorical feature, put the legend to the left of the plot
    elif is_object_dtype(df[c]):
        p.add_layout(p.legend[0], 'left')
        
    p.select(LassoSelectTool).continuous = False
    p.output_backend = 'svg'
    
    return p

## 2.3 Define a function to draw the histogram for a numeric feature.

def draw_hist(df, col, points_selected):
    print("points_selected:", points_selected)
    # get the corresponding rows in the dataframe for the selected points
    if not points_selected:
        s = pd.DataFrame(columns=df.columns)
    else:
        s = df.iloc[points_selected]

    # compute the tops and edges of the bins in the histogram
    # for all the points and the selected points respectively
    top, edges = np.histogram(df[col], bins=50)
    top_s, _ = np.histogram(s[col], bins=edges)
    
    # create a data source for both sets of bins
    source = ColumnDataSource(data=dict(
        left=edges[:-1],
        right=edges[1:],
        all=top,
        selected=top_s,
    ))

    ph = figure(
        width=400,
        height=300, 
        min_border=20,  
        y_range = (0, 1.1*top.max()),
        y_axis_location="right", 
        title=f'Histogram of {col}',
        tools='pan, wheel_zoom, reset', 
        toolbar_location='below', 
    )
    
    ph.xaxis.axis_label = f'{col}'
    ph.yaxis.axis_label = 'Counts'
    ph.xgrid.grid_line_color = None
    ph.background_fill_color = "#fafafa"
    # draw the bins of all points
    h_a = ph.quad(
        bottom=0, 
        left='left', 
        right='right', 
        top='all', 
        source=source,
        legend_label='all',
        color="white", 
        line_color="silver"
    )
    # draw the bins of selected points
    h_s = ph.quad(
        bottom=0, 
        left='left', 
        right='right', 
        top='selected',
        source=source,
        legend_label='selected',
        color='silver', 
        line_color=None, 
        alpha=0.5, 
    )
    ph.legend.orientation = "horizontal"
    ph.legend.location = "top_right"
    # add a hover tool that shows the values of 
    # the range (left and right edges) of a bin
    # the counts of all points in the bin
    # the counts of selected points in the bin
    hover = HoverTool()
    hover.tooltips=[
        ('range', '[@left, @right]'),
        ('all', '@all'),
        ('selected', '@selected')
    ]
    # to avoid overlap, apply the hover tool only on the bins of all points
    hover.renderers = [h_a]       
    ph.add_tools(hover)     
    
    return ph


## 2.4 (Optional) Define a function to draw a bar chart for a categorical feature.

def draw_bar_chart(df, col, points_selected):
    # get the corresponding rows in the dataframe for the selected points
    s = df.iloc[points_selected] if len(points_selected) > 0 else pd.DataFrame(columns=df.columns)
    
    # count the number in the categories
    # for all the points and the selected points respectively
    dis = df[col].value_counts()
    dis_s = s.value_counts()
    cat = dis.index.values
    count = dis.values
    
    # note that if the selected points do not have a certain category
    # the corresponding count should be zero
    count_s = []
    for c in cat:
        count_s.append(dis_s[c] if c in dis_s.index else 0)
    
    # use the color palette you created before in the create_cmap function
    # synchronize the color map of the bars with the pca plot
    # i.e. each category should have the same color in the pca plot and the bar chart
    _, cat_palette = create_cmap(df, col)
    cat_color = [cat_palette[c] for c in cat]
    # create a data source for both sets of bars
    source = ColumnDataSource(data=dict(
        x=np.concatenate((cat, cat)),
        counts=np.concatenate((count, count_s)),
        color=cat_color + cat_color,
        label=['all'] * len(cat) + ['selected'] * len(cat)
    ))

    pb = figure(
        x_range=cat, 
        y_range=(0, count.max()*1.1),
        y_axis_location="right",  
        width=400,
        height=300, 
        min_border=20, 
        title=f'Distribution of {col}',
        tools='pan, wheel_zoom, reset',
        toolbar_location='below', 
    )
    
    pb.background_fill_color = "#fafafa"
    pb.xaxis.axis_label = f'{col}'
    pb.yaxis.axis_label = 'Counts'
    # draw the bars of all points
    bar_all = pb.vbar(
        x='x',
        top='counts',
        width=0.6, 
        color='white',
        line_color="silver",
        legend_label='all',
        source=source,
        ##
        muted_alpha=0.2,
        muted_color='white',
        muted_line_color='silver'
        ##
    )
    # draw the bars of selected points
    bar_selected = pb.vbar(
        x='x',
        top='counts',
        width=0.6, 
        color='color',
        #alpha=0.4,
        alpha=0.8,
        legend_label='selected',
        source=source,
        ##
        muted_alpha=0.2,
        muted_color='color',
        muted_line_color=None
        ##
    )

    pb.xgrid.grid_line_color = None
    pb.xaxis.major_label_orientation = np.pi/2
    pb.legend.orientation = "horizontal"
    pb.legend.location = "top_right"
    ##
    pb.legend.click_policy="mute"
    ##
    
    
    # add a hover tool that shows the values of 
    # the category of a bar
    # the counts of all points in the bar
    # the counts of selected points in the bar
    hover = HoverTool()
    hover.tooltips=[
            ('category', '@x'),
            ('all', '@counts{(0,0)}'),
            ('selected', '@counts{(0,0)}'),
        ]
    hover.renderers = [bar_all]   
    pb.add_tools(hover)      
    pb.output_backend = 'svg'
        
    return pb

# Define a function to draw the subplot 
# according to the data type of the selected feature
# and the indices of the selected points in the PCA plot

def draw_subplot(df, ft_selected, points_selected):
    cs = ft_selected
    rs = points_selected
    if is_numeric_dtype(df[cs]):
        sub_p = draw_hist(df, cs, rs)
    elif is_object_dtype(df[cs]):
        sub_p = draw_bar_chart(df, cs, rs)
    return sub_p


# Plotting

# Get the dataframe with principal components and cluster labels
df = pca(pca_data)
print("Dataframe after PCA:\n", df.head())  # Print the first 5 rows of the dataframe after PCA

df = clustering(df)
print("\nDataframe after clustering:\n", df.head())  # Print the first 5 rows of the dataframe after clustering

# Select a initial feature for the PCA plot
pca_ft_selected = 'Market Cap'

# Select a initial feature for the subplot
sub_ft_selected = 'Mean Recommendation'

# The initial indices of selected points is an empty list
points_selected = []

# Add a column named 'label' in the dataframe
# which is a copy the selected feature.
# It will be updated when you choose a different feature 
# in the selection widget for the PCA plot.
df['label'] = pca_ft_selected

# create the data source for the PCA plot using ColumnDataSource
p_pca_source = ColumnDataSource(data=df)
print("\nColumnDataSource for PCA plot:\n", p_pca_source.data)  # Print the data in the ColumnDataSource

# Create the initial PCA plot and the subplot
p_pca = plot_pca(p_pca_source, df, pca_ft_selected)
print("\nPCA plot:\n", p_pca)  # Print the PCA plot object

p_sub = draw_subplot(df, sub_ft_selected, points_selected)
print("\nSubplot:\n", p_sub)  # Print the subplot object


# 3.1 Add two Select widgets

select_col_pca = Select(
    title='Select a feature to apply a color map in the PCA plot:', 
    value=pca_ft_selected,
    # You are free to choose which features to include in the options
    # as long as there is at least one categorical feature, e.g. 'Cluster'
    options=[
        'Market Cap', 'Cluster'  # Add more options as required
    ],
    width=200,
    margin=(20, 10, 10, 20)
)

select_col_sub = Select(
    title='Select a feature to show in the subplot:', 
    value=sub_ft_selected, 
    # You are free to choose which features to include in the options
    # it is optional to include any categorical feature
    options=[
        'Mean Recommendation' 
    ],
    width=200,
    margin=(10, 10, 10, 20)
)

# arrange the plots and widgets in a layout
layout = row(
    column(
      p_pca, 
      width=500, 
    ), 
    column(
      select_col_pca, 
      select_col_sub, 
      p_sub,
      width=350,
    ), 
)


# 3.2 Define the callback functions for the selection widgets

def update_pca_col(attrname, old, new):
    
    global pca_ft_selected
    pca_ft_selected = new
    p_pca_source.data['label'] = df[new]
    p_pca = plot_pca(p_pca_source, df, pca_ft_selected)
    layout.children[0].children[0] = p_pca

# Callback function of the Select widget for the subplot:
# when you select a new feature
# a new subplot of this feature will be drawn to replace the previous one in the layout
# the new subplot will keep the previous selection of points by the lasso selection tool 

def update_sub_col(attrname, old, new):
    global sub_ft_selected
    sub_ft_selected = new
    layout.children[1].children[2] = draw_subplot(df, sub_ft_selected, points_selected)

select_col_pca.on_change('value', update_pca_col)
select_col_sub.on_change('value', update_sub_col)

## 3.3 Define the callback functions for the lasso selection tool in the PCA plot

# when you select some points with the lasso selection tool,
# a new subplot will be drawn to replace the previous one in the layout
# with the new selection of points reflected in the bins / bars of the selected points
# Example:
# https://github.com/bokeh/bokeh/blob/branch-.1/examples/server/app/selection_histogram.py
def lasso_update(attr, old, new):
   
    global points_selected
    points_selected = new.indices
    layout.children[1].children[2] = draw_subplot(df, sub_ft_selected, points_selected)

p_pca.renderers[0].data_source.selected.on_change('indices', lasso_update)

curdoc().add_root(layout)
curdoc().title = 'PCA'