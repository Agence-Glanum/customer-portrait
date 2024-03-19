import json
import pandas as pd
import streamlit as st
import geopandas as gpd
import plotly.express as px
from utils.data_viz import show_plots


@st.cache_data
def compute_kpis(invoices, orders, customers, categories, products, cltv_df):
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric('Customers', customers['Customer_ID'].nunique())
    col2.metric('Categories Count', str(len(categories)))
    col3.metric('Products Count', str(len(products)))
    col4.metric('Lifetime Value (€)', str(round(cltv_df['CLTV'].mean(), 2)))
    col5.metric('Lifetime Value (days)', str(round(cltv_df['Age'].mean(), 2)))

    return show_plots(invoices, orders)


@st.cache_data
def compute_lifetime_value(df, df_lines, sales_filter):
    df_final = df.merge(df_lines, left_on=sales_filter + '_ID', right_on=sales_filter + '_ID')

    cltv_df = df_final.groupby('Customer_ID').agg(
        {
            sales_filter + '_date': lambda x: (x.max() - x.min()).days,
            sales_filter + '_ID': lambda x: len(x),
            'Quantity': lambda x: x.sum(),
            'Total_price_y': lambda x: x.sum(),
        }
    )
    cltv_df.columns = ['Age', 'Num_transactions', 'Quantity', 'Total_revenue']
    cltv_df = cltv_df.reset_index()
    cltv_df = cltv_df[cltv_df['Quantity'] > 0]
    cltv_df['AOV'] = cltv_df['Total_revenue'] / cltv_df['Num_transactions']
    purchase_freq = sum(cltv_df['Num_transactions']) / len(cltv_df)
    repeat_rate = cltv_df[cltv_df['Num_transactions'] > 1].shape[0] / cltv_df.shape[0]
    churn_rate = 1 - repeat_rate
    cltv_df['CLTV'] = ((cltv_df['AOV'] * purchase_freq) / churn_rate) * .10
    cltv_df = cltv_df[['Customer_ID', 'Age', 'CLTV']]

    return cltv_df


@st.cache_data
def get_customers_heatmap(address):
    with open('./utils/Geo/GlobalMap/countries.json') as c:
        countries_data = json.load(c)
    with open('./utils/Geo/GlobalMap/dpts.json', 'r') as f:
        data = json.load(f)

    corsica = pd.read_csv('utils/Geo/base-officielle-codes-postaux.csv')
    zip_codes = address.drop_duplicates()

    mask = (zip_codes['Country'] != 'FR') & (~zip_codes['Country'].isnull())
    zip_codes.loc[mask, 'Zip_code'] = zip_codes.loc[mask, 'Country']
    zip_codes = zip_codes.dropna(subset=['Zip_code', 'City', 'Country'])

    selected_entries = corsica[corsica['code_commune_insee'].str.startswith(('2A', '2B'))]
    selected_entries.loc[:, 'nom_de_la_commune'] = selected_entries['nom_de_la_commune'].str.replace(' ',
                                                                                                     '-').str.capitalize()
    selected_entries.loc[:, 'code_commune_insee'] = selected_entries['code_commune_insee'].str[:2]
    zip_codes['Zip_code'] = zip_codes['Zip_code'].astype(str)
    selected_entries.loc[:, 'code_postal'] = selected_entries['code_postal'].astype(str)
    zip_codes['Zip_code'] = zip_codes.apply(
        lambda row: selected_entries.loc[
            (selected_entries['code_postal'] == row['Zip_code']), 'code_commune_insee'].values[0]
        if any(selected_entries['code_postal'] == row['Zip_code'])
        else row['Zip_code'],
        axis=1
    )

    zip_codes['Zip_code'] = zip_codes['Zip_code'].str[:2]
    result = zip_codes.groupby('Zip_code').size().reset_index(name='Count')
    result['Zip_code'] = result['Zip_code'].apply(lambda x: x[1:] if len(x) == 2 and x.startswith('0') else x)

    country_json_copie = list(countries_data.copy())
    gps_json_copie = list(data.copy())

    zip_coder = result['Zip_code'].unique()
    gps_json_copie = [item for item in gps_json_copie if item['numero'] in zip_coder]
    country_json_copie = [item for item in country_json_copie if item['alpha2'] in zip_coder]

    df_gps = pd.json_normalize(gps_json_copie)
    df_countries = pd.json_normalize(country_json_copie)
    df_countries_renamed = df_countries.rename(columns={'latitude': 'lat', 'longitude': 'lng', 'alpha2': 'numero'})

    result['Zip_code'] = result['Zip_code'].astype(str)

    merged_df_dpts = pd.merge(df_gps, result, how='left', left_on='numero', right_on='Zip_code')
    merged_df_dpts_dropped = merged_df_dpts.drop('nomLong', axis=1)

    merged_df_countries = pd.merge(df_countries_renamed, result, how='left', left_on='numero', right_on='Zip_code')
    merged_df_countries_dropped = merged_df_countries.drop(columns=['numeric', 'alpha3'])
    merged_df_countries_dropped = merged_df_countries_dropped.rename(columns={'country': 'nomShort'})
    result = pd.concat([merged_df_countries_dropped, merged_df_dpts_dropped], ignore_index=True)

    fig = px.density_mapbox(result,
                            height=600,
                            lat='lat',
                            lon='lng',
                            z='Count',
                            color_continuous_scale='viridis',
                            radius=10,
                            center={'lat': 46.6031, 'lon': 1.7394},
                            zoom=2,
                            mapbox_style='carto-positron')
    fig.update_layout(title='Heatmap of Customers')
    st.write(fig)

    return fig


@st.cache_data
def get_customer_location(address, customer_id):
    corsica = pd.read_csv('utils/Geo/base-officielle-codes-postaux.csv')

    selected_entries = corsica[corsica['code_commune_insee'].str.startswith(('2A', '2B'))]
    selected_entries.loc[:, 'nom_de_la_commune'] = selected_entries['nom_de_la_commune'].str.replace(' ',
                                                                                                     '-').str.capitalize()
    selected_entries.loc[:, 'code_commune_insee'] = selected_entries['code_commune_insee'].str[:2]

    address['Zip_code'] = address['Zip_code'].astype(str)
    selected_entries.loc[:, 'code_postal'] = selected_entries['code_postal'].astype(str)

    address['Zip_code'] = address.apply(
        lambda row: selected_entries.loc[
            (selected_entries['code_postal'] == row['Zip_code']), 'code_commune_insee'].values[0]
        if any(selected_entries['code_postal'] == row['Zip_code'])
        else row['Zip_code'],
        axis=1
    )

    customer_zip = address[address['Customer_ID'] == customer_id]
    customer_zip.loc[:, 'Zip_code'] = customer_zip['Zip_code'].str[:2]
    customer_zip.loc[:, 'City'] = customer_zip['City'].str.replace(' ', '-').str.capitalize()

    if (customer_zip['Country'] == 'FR').any():
        geojson_france = './utils/Geo/contour-des-departements.geojson'
        gdf_departements = gpd.read_file(geojson_france)

        france_map = px.choropleth_mapbox(customer_zip, geojson=gdf_departements, locations='Zip_code',
                                          featureidkey='properties.code',
                                          color='Address_type',
                                          color_continuous_scale='Viridis',
                                          range_color=(0, 12),
                                          mapbox_style='carto-positron',
                                          zoom=3.5, center={'lat': 46.6031, 'lon': 1.8883},
                                          opacity=0.8)
        france_map.update_layout(title='Customer Location')
        return st.write(france_map)

    else:
        geojson_world = './utils/Geo/curiexplore-pays.geojson'
        gdf_departements2 = gpd.read_file(geojson_world)
        gdf_occurences2 = gdf_departements2.merge(customer_zip['Country'], how='left', left_on='code',
                                                  right_on='Country')
        gdf_occurences2['Country'] = gdf_occurences2['Country'].fillna(0)
        world_map = px.choropleth_mapbox(customer_zip, geojson=gdf_occurences2, locations='Country',
                                         color='Address_type',
                                         featureidkey='properties.code',
                                         color_continuous_scale='Viridis',
                                         range_color=(0, 12),
                                         mapbox_style='carto-positron',
                                         zoom=1, center={'lat': 46.6031, 'lon': 1.8883},
                                         opacity=0.8)
        world_map.update_layout(title='Customer Location')
        return st.write(world_map)


@st.cache_data
def get_cluster_location(address, customer_ids):
    corsica = pd.read_csv('utils/Geo/base-officielle-codes-postaux.csv')

    selected_entries = corsica[corsica['code_commune_insee'].str.startswith(('2A', '2B'))]
    selected_entries.loc[:, 'nom_de_la_commune'] = selected_entries['nom_de_la_commune'].str.replace(' ',
                                                                                                     '-').str.capitalize()
    selected_entries.loc[:, 'code_commune_insee'] = selected_entries['code_commune_insee'].str[:2]

    address['Zip_code'] = address['Zip_code'].astype(str)
    selected_entries.loc[:, 'code_postal'] = selected_entries['code_postal'].astype(str)

    address['Zip_code'] = address.apply(
        lambda row: selected_entries.loc[
            (selected_entries['code_postal'] == row['Zip_code']), 'code_commune_insee'].values[0]
        if any(selected_entries['code_postal'] == row['Zip_code'])
        else row['Zip_code'],
        axis=1
    )

    customer_zips = address[address['Customer_ID'].isin(customer_ids)]
    customer_zips.loc[:, 'Zip_code'] = customer_zips['Zip_code'].str[:2]
    customer_zips.loc[:, 'City'] = customer_zips['City'].str.replace(' ', '-').str.capitalize()

    geojson_france = './utils/Geo/contour-des-departements.geojson'
    gdf_departements = gpd.read_file(geojson_france)

    france_map = px.choropleth_mapbox(customer_zips[customer_zips['Country'] == 'FR'],
                                      geojson=gdf_departements, locations='Zip_code',
                                      featureidkey='properties.code',
                                      color='Address_type',
                                      color_continuous_scale='Viridis',
                                      range_color=(0, 12),
                                      mapbox_style='carto-positron',
                                      zoom=3.5, center={'lat': 46.6031, 'lon': 1.8883},
                                      opacity=0.8,
                                      )
    france_map.update_layout(title='Cluster Location in France')
    st.write(france_map)

    geojson_world = './utils/Geo/curiexplore-pays.geojson'
    gdf_departements2 = gpd.read_file(geojson_world)
    gdf_occurences2 = gdf_departements2.merge(customer_zips['Country'], how='left', left_on='code',
                                              right_on='Country')
    gdf_occurences2['Country'] = gdf_occurences2['Country'].fillna(0)
    world_map = px.choropleth_mapbox(customer_zips[customer_zips['Country'] != 'FR'], geojson=gdf_occurences2,
                                     locations='Country',
                                     color='Address_type',
                                     featureidkey='properties.code',
                                     color_continuous_scale='Viridis',
                                     range_color=(0, 12),
                                     mapbox_style='carto-positron',
                                     zoom=1, center={'lat': 46.6031, 'lon': 1.8883},
                                     opacity=0.8,
                                     )
    world_map.update_layout(title='Cluster Location worldwide')
    if not customer_zips[customer_zips['Country'] != 'FR'].empty:
        st.write(world_map)

    return france_map, world_map
