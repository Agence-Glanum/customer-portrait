import json
import pandas as pd
import streamlit as st
import geopandas as gpd
import plotly.express as px
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static


def compute_kpis(invoices, orders, categories, products, cltv_df):
    col1, col2, col3 = st.columns(3)

    col1.metric('Customers', invoices['Customer_ID'].nunique())
    col1.metric('Categories Count', str(len(categories)))
    col1.metric('Products Count', str(len(products)))
    col1.metric('Lifetime value', str(round(cltv_df['CLTV'].mean(), 2)))

    valid_orders = orders[(orders['Status'] != 'draft') & (orders['Status'] != 'cancelled')]
    col2.metric('Orders', valid_orders['Order_ID'].nunique())
    col2.metric('Minimum orders Value', str(round(valid_orders['Total_price'].min(), 2)) + '€')
    col2.metric('Average Order Value', str(round(valid_orders['Total_price'].mean(), 2)) + '€')
    col2.metric('Maximum orders Value', str(round(valid_orders['Total_price'].max(), 2)) + '€')

    col3.metric('Invoices', invoices['Invoice_ID'].nunique())
    col3.metric('Minimum Invoice Value', str(round(invoices['Total_price'].min(), 2)) + '€')
    col3.metric('Average Invoice Value', str(round(invoices['Total_price'].mean(), 2)) + '€')
    col3.metric('Maximum Invoice Value', str(round(invoices['Total_price'].max(), 2)) + '€')

    return


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
    cltv_df = cltv_df[['Customer_ID', 'CLTV']]

    return cltv_df


def get_customers_heatmap(address):
    with open('./utils/Geo/GlobalMap/countries.json') as c:
        countries_data = json.load(c)
    with open('./utils/Geo/GlobalMap/dpts.json', 'r') as f:
        data = json.load(f)

    corsica = pd.read_csv("utils/Geo/base-officielle-codes-postaux.csv")


    address['Address_1'] = address['Address_1'].astype(str).str.strip()
    address['City'] = address['City'].str.strip()
    address['Zip_code'] = address['Zip_code'].str.strip()
    address['Country'] = address['Country'].str.strip()

    zip_codes = address.drop_duplicates(subset=['Address_1', 'Zip_code', 'City', 'Country'])
    zip_codes = zip_codes.drop_duplicates(subset=['Customer_ID'])
    # zip_codes = address.drop_duplicates()

    non_numeric_pattern = r'^[^\d]*$'
    zip_codes = zip_codes[~zip_codes['Zip_code'].str.contains(non_numeric_pattern, na=False)]

    mask = (zip_codes['Country'] != 'FR') & (~zip_codes['Country'].isnull())
    zip_codes.loc[mask, 'Zip_code'] = zip_codes.loc[mask, 'Country']
    zip_codes = zip_codes.dropna(subset=['Zip_code', 'City', 'Country'])

    selected_entries = corsica[corsica['code_commune_insee'].str.startswith(('2A', '2B'))]
    selected_entries["nom_de_la_commune"] = selected_entries["nom_de_la_commune"].str.replace(" ", "-").str.capitalize()
    selected_entries["code_commune_insee"] = selected_entries["code_commune_insee"].str[:2]
    zip_codes['Zip_code'] = zip_codes['Zip_code'].astype(str)
    selected_entries['code_postal'] = selected_entries['code_postal'].astype(str)
    zip_codes['Zip_code'] = zip_codes.apply(
        lambda row: selected_entries.loc[
            (selected_entries['code_postal'] == row['Zip_code']), 'code_commune_insee'].values[0]
        if any(selected_entries['code_postal'] == row['Zip_code'])
        else row['Zip_code'],
        axis=1
    )

    zip_codes["Zip_code"] = zip_codes["Zip_code"].str[:2]
    result = zip_codes.groupby('Zip_code').size().reset_index(name='Count')
    result['Zip_code'] = result['Zip_code'].apply(lambda x: x[1:] if len(x) == 2 and x.startswith('0') else x)

    country_json_copie = list(countries_data.copy())
    gps_json_copie = list(data.copy())

    zip_coder = result['Zip_code'].unique()
    gps_json_copie = [item for item in gps_json_copie if item['numero'] in zip_coder]
    country_json_copie = [item for item in country_json_copie if item['alpha2'] in zip_coder]

    df_gps = pd.json_normalize(gps_json_copie)
    df_countries = pd.json_normalize(country_json_copie)
    df_countries_renamed = df_countries.rename(columns={"latitude": "lat", "longitude": "lng", "alpha2": "numero"})

    result['Zip_code'] = result['Zip_code'].astype(str)

    merged_df_dpts = pd.merge(df_gps, result, how='left', left_on='numero', right_on='Zip_code')
    merged_df_dpts_dropped = merged_df_dpts.drop("nomLong", axis=1)

    merged_df_countries = pd.merge(df_countries_renamed, result, how='left', left_on='numero', right_on='Zip_code')
    merged_df_countries_dropped = merged_df_countries.drop(columns=["numeric", "alpha3"])
    merged_df_countries_dropped = merged_df_countries_dropped.rename(columns={"country": "nomShort"})
    result = pd.concat([merged_df_countries_dropped, merged_df_dpts_dropped], ignore_index=True)
    result['Count'] = pd.to_numeric(result['Count'], errors='coerce')
    result['Count_log'] = np.log1p(result['Count'])
    color_scale_range = [result['Count'].min(), result['Count'].max()]
    # fig = px.density_mapbox(result,
    #                         height=600,
    #                         lat='lat',
    #                         lon='lng',
    #                         z='Count',
    #                         # range_color=color_scale_range,
    #                         color_continuous_scale="plasma",
    #                         radius=10,
    #                         center={"lat": 46.6031, "lon": 1.7394},
    #                         zoom=2,
    #                         mapbox_style="carto-positron"
    #                         )
    #
    # fig.update_layout(
    #     coloraxis_showscale=True,  # Set to True to display the color scale
    #     coloraxis_colorbar=dict(title='Count'),  # Customize the colorbar title
    # )
    # st.write(fig)
    # Create a Folium map centered around the mean of the coordinates
    map_center = [result['lat'].mean(), result['lng'].mean()]
    mymap = folium.Map(location=map_center, zoom_start=5)

    # Create a HeatMap layer from the DataFrame
    heat_data = [[row['lat'], row['lng'], row['Count']] for index, row in result.iterrows()]
    HeatMap(heat_data).add_to(mymap)

    folium_static(mymap)
    return


def get_customer_location(address, customer_id):
    df_adresses = address
    corsica = pd.read_csv("utils/Geo/base-officielle-codes-postaux.csv")

    selected_entries = corsica[corsica['code_commune_insee'].str.startswith(('2A', '2B'))]
    selected_entries["nom_de_la_commune"] = selected_entries["nom_de_la_commune"].str.replace(" ", "-").str.capitalize()
    selected_entries["code_commune_insee"] = selected_entries["code_commune_insee"].str[:2]

    df_adresses['Zip_code'] = df_adresses['Zip_code'].astype(str)
    selected_entries['code_postal'] = selected_entries['code_postal'].astype(str)

    df_adresses['Zip_code'] = df_adresses.apply(
        lambda row: selected_entries.loc[
            (selected_entries['code_postal'] == row['Zip_code']), 'code_commune_insee'].values[0]
        if any(selected_entries['code_postal'] == row['Zip_code'])
        else row['Zip_code'],
        axis=1
    )

    customer_zip = df_adresses[df_adresses['Customer_ID'] == customer_id]
    customer_zip.loc[:, 'Zip_code'] = customer_zip['Zip_code'].str[:2]
    customer_zip["City"] = customer_zip["City"].str.replace(" ", "-").str.capitalize()

    if (customer_zip["Country"] == "FR").any():
        geojson_france = './utils/Geo/contour-des-departements.geojson'
        gdf_departements = gpd.read_file(geojson_france)

        france_map = px.choropleth_mapbox(customer_zip, geojson=gdf_departements, locations='Zip_code',
                                          featureidkey='properties.code',
                                          color='Zip_code',
                                          color_continuous_scale='Viridis',
                                          range_color=(0, 12),
                                          mapbox_style='carto-positron',
                                          zoom=3.5, center={'lat': 46.6031, 'lon': 1.8883},
                                          opacity=0.8,
                                          )
        france_map.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0}, showlegend=True)
        st.write(france_map)

    else:
        geojson_world = './utils/Geo/curiexplore-pays.geojson'
        gdf_departements2 = gpd.read_file(geojson_world)
        gdf_occurences2 = gdf_departements2.merge(customer_zip['Country'], how='left', left_on='code',
                                                  right_on='Country')
        gdf_occurences2['Country'] = gdf_occurences2['Country'].fillna(0)
        world_map = px.choropleth_mapbox(customer_zip, geojson=gdf_occurences2, locations='Country', color='Country',
                                         featureidkey='properties.code',
                                         color_continuous_scale='Viridis',
                                         range_color=(0, 12),
                                         mapbox_style='carto-positron',
                                         zoom=1, center={'lat': 46.6031, 'lon': 1.8883},
                                         opacity=0.8,
                                         )
        world_map.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0}, showlegend=True)
        st.write(world_map)

    return


def get_cluster_location(address, cluster_id):
    st.write('Map')
    return
