import pandas as pd
import streamlit as st
import plotly.express as px
import geopandas as gpd
from utils.data_viz import show_timelines


def get_info(rfm, customer_id, scaler, kmeans):
    col_names = ['Recency', 'Frequency', 'Monetary']
    features = rfm[rfm['Customer_ID'] == customer_id][col_names]
    scaled_features = scaler.transform(features.values)
    customer_cluster = kmeans.predict(scaled_features)

    customer_segment_1 = rfm[rfm['Customer_ID'] == customer_id]['Segment 1']
    customer_segment_2 = rfm[rfm['Customer_ID'] == customer_id]['Segment 2']

    return customer_cluster, customer_segment_1, customer_segment_2


def compute_lifetime_value(df, df_lines, transformed_sales_filter):
    df_final = df.merge(df_lines, left_on=transformed_sales_filter + '_ID', right_on=transformed_sales_filter + '_ID')

    cltv_df = df_final.groupby('Customer_ID').agg(
        {
            transformed_sales_filter + '_date': lambda x: (x.max() - x.min()).days,
            transformed_sales_filter + '_ID': lambda x: len(x),
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


def get_clusters(rfm, df_sales, df_lines, product_clusters, category_clusters, product_grouped_df,
                 category_grouped_df, ml_clusters, segment_1_cluters, segment_2_cluters,
                 transformed_sales_filter, show_full_dataframe=False):
    cltv_df = compute_lifetime_value(df_sales, df_lines, transformed_sales_filter)

    merged_df = pd.merge(cltv_df, rfm[['Customer_ID', 'Customer_name', 'Cluster RFM', 'Segment 1', 'Segment 2']],
                         on='Customer_ID', how='inner')
    merged_df = pd.merge(merged_df, product_clusters['Cluster MBA'], on='Customer_ID', how='inner').rename(
        columns={'Cluster MBA': 'Product Cluster MBA'})
    merged_df = pd.merge(merged_df, category_clusters['Cluster MBA'], on='Customer_ID', how='inner').rename(
        columns={'Cluster MBA': 'Category Cluster MBA'})

    if show_full_dataframe:
        st.dataframe(merged_df, use_container_width=True)
    else:
        customer_id = st.selectbox('Customer', (
                (merged_df['Customer_ID'].astype(int)).astype(str) + ' - ' + merged_df['Customer_name']))
        customer_id = int(customer_id.split(' - ')[0])
        st.dataframe(merged_df[merged_df['Customer_ID'] == customer_id], use_container_width=True)

    product_grouped_df = product_grouped_df.reset_index().rename(columns={'Cluster MBA': 'Product Cluster MBA'})
    category_grouped_df = category_grouped_df.reset_index().rename(columns={'Cluster MBA': 'Category Cluster MBA'})

    return ml_clusters, segment_1_cluters, segment_2_cluters, product_grouped_df, category_grouped_df


def get_map(directory, address, customer_id):
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


def customer_overview_function(address, rfm, scaler, kmeans, df_sales,
                               df_lines, sales_filter, directory, snapshot_start_date, snapshot_end_date):
    cltv_df = compute_lifetime_value(df_sales, df_lines, sales_filter)
    customer_id = st.selectbox('Customers', (rfm['Customer_ID'].astype(str) + ' - ' + rfm['Customer_name']))
    customer_id = int(customer_id.split(' - ')[0])

    col1, col2, col3 = st.columns(3)

    customer_cluster, customer_segment_1, customer_segment_2 = get_info(rfm, customer_id, scaler, kmeans)

    col1.write('RFM clusters')
    col1.metric('ML cluster', 'Cluster ' + str(customer_cluster[0]))
    col1.metric('Segment 1', str(customer_segment_1.iloc[0]))
    col1.metric('Segment 2', str(customer_segment_2.iloc[0]))

    col2.write('MBA clusters')
    col2.metric('Product cluster', 0)
    col2.metric('Category cluster', 0)

    cltv = round(cltv_df[cltv_df['Customer_ID'] == customer_id]['CLTV'], 2)
    mean_cltv = round(cltv_df['CLTV'].mean(), 2)
    diff = round(cltv - mean_cltv, 2).values[0]
    col3.metric('Lifetime value', cltv, diff)

    st.subheader('Timeline of Sales and Orders')
    path = './data/Glanum/' if directory == 'Glanum' else './data/IciStore/'
    invoices = pd.read_csv(f'{path}/Invoices.csv')
    orders = pd.read_csv(f'{path}/Orders.csv')

    show_timelines(invoices[(invoices['Customer_ID'] == customer_id)],
                   orders[(orders['Customer_ID'] == customer_id)], snapshot_start_date, snapshot_end_date)

    st.subheader('Customer Location')
    get_map(directory, address, customer_id)

    return


def customer_overview_main_function(address, rfm, scaler, kmeans, df_sales, df_lines, sales_filter, directory,
                                    snapshot_start_date, snapshot_end_date):
    customer_overview_tab, cluster_overview_tab, data_tab = st.tabs(['Customer overview', 'Cluster overview', 'Data'])
    with customer_overview_tab:
        customer_overview_function(address, rfm, scaler, kmeans, df_sales, df_lines, sales_filter, directory,
                                   snapshot_start_date, snapshot_end_date)
    with cluster_overview_tab:
        st.write()
    with data_tab:
        st.write()

        # ml_clusters, segment_1_cluters, segment_2_cluters, product_grouped_df, category_grouped_df = get_clusters(
        #     rfm, df_sales, df_lines, product_clusters, category_clusters, product_grouped_df,
        #     category_grouped_df, ml_clusters, segment_1_cluters, segment_2_cluters,
        #     transformed_sales_filter, show_full_dataframe=False)
        # st.dataframe(ml_clusters)
        # st.dataframe(segment_1_cluters)
        # st.dataframe(segment_2_cluters)
        # st.dataframe(product_grouped_df)
        # st.dataframe(category_grouped_df)
    return
