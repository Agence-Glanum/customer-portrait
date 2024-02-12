import streamlit as st
import plotly.express as px
import geopandas as gpd


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


def get_customer_location(directory, address, customer_id):
    customer_zip = address[address['Customer_ID'] == customer_id]
    customer_zip.loc[:, 'Zip_code'] = customer_zip['Zip_code'].str[:2]

    if directory == 'Ici store':
        geojson_france = './utils/Geo/contour-des-departements.geojson'
        gdf_departements = gpd.read_file(geojson_france)
        france_map = px.choropleth_mapbox(customer_zip, geojson=gdf_departements, locations='Zip_code',
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
        st.info('This feature is not ready yet.')
        # geojson_world = './utils/Geo/curiexplore-pays.geojson'
        # gdf_departements2 = gpd.read_file(geojson_world)
        # gdf_occurences2 = gdf_departements2.merge(customer_zip['Country'], how='left', left_on='code',
        #                                           right_on='Country')
        # gdf_occurences2['Country'] = gdf_occurences2['Country'].fillna(0)
        # world_map = px.choropleth_mapbox(customer_zip, geojson=gdf_occurences2, locations='Country', color='Country',
        #                                  featureidkey='properties.code',
        #                                  color_continuous_scale='Viridis',
        #                                  range_color=(0, 12),
        #                                  mapbox_style='carto-positron',
        #                                  zoom=1, center={'lat': 46.6031, 'lon': 1.8883},
        #                                  opacity=0.8,
        #                                  )
        # world_map.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0}, showlegend=True)
        # st.write(world_map)

    return


def get_cluster_location(directory, address, cluster_id):
    st.write('Map')
    return
