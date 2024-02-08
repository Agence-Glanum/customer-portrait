import streamlit as st
import plotly.express as px
import geopandas as gpd


def map_function(address):
    address['Zip_code'] = address['Zip_code'].str[:2]
    geojson_path = './utils/Geo/department-contours.geojson'
    # geojson_world = './utils/Geo/curiexplore-countries.geojson'

    gdf_departments = gpd.read_file(geojson_path)
    address['Zip_code'] = address['Zip_code'].astype(str)
    gdf_occurrences = gdf_departments.merge(address['Zip_code'], how='left',
                                            left_on='code', right_on='Zip_code')
    gdf_occurrences['Zip_code'] = gdf_occurrences['Zip_code'].fillna(0)
    fig = px.choropleth_mapbox(address, geojson=gdf_departments, locations='Zip_code', color='Zip_code',
                               color_continuous_scale='Viridis', range_color=(0, 12), mapbox_style='carto-positron',
                               zoom=3.5, center={'lat': 46.6031, 'lon': 1.8883}, opacity=0.8)
    fig.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0}, showlegend=False)
    st.write(fig)
