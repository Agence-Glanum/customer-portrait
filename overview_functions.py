import json
import os
import streamlit as st
import plotly.graph_objects as go
from utils.data_viz import show_timelines
from utils.utility_functions import get_customer_location, get_cluster_location


@st.cache_data
def show_details(ml_clusters, segment_1_clusters, segment_2_clusters, product_grouped_df, category_grouped_df):
    with st.expander('Details about the clusters'):
        st.info('The RFM values represent the average value within each cluster.')
        st.dataframe(ml_clusters)
        st.dataframe(segment_1_clusters)
        st.dataframe(segment_2_clusters)
        st.dataframe(product_grouped_df)
        st.dataframe(category_grouped_df)
    return


def customer_overview_function(address, overview_data, directory, snapshot_start_date, snapshot_end_date):
    customer_id = st.selectbox('List of Customers',
                               (overview_data['Customer_ID'].astype(str) + ' - ' + overview_data['Customer_name']))
    customer_id = int(customer_id.split(' - ')[0])
    mean_cltv = overview_data['CLTV'].mean()
    overview_data = overview_data[overview_data['Customer_ID'] == customer_id]

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.write('***RFM clusters***')
    col1.metric('ML cluster', str(overview_data['Cluster RFM'].values[0]))
    col1.metric('Segment 1', str(overview_data['Segment 1'].values[0]))
    col1.metric('Segment 2', str(overview_data['Segment 2'].values[0]))

    col2.write('***MBA clusters***')
    col2.metric('Product cluster', str(overview_data['Product cluster MBA'].values[0]))
    col2.metric('Category cluster', str(overview_data['Category cluster MBA'].values[0]))

    col3.write('***KPIs***')
    col3.metric('Lifetime Value (€)', str(round(overview_data['CLTV'].values[0], 2)),
                str(round((overview_data['CLTV'].values[0] - mean_cltv) / mean_cltv * 100, 2)) + ' %')
    col3.metric('Longevity (days)', str(overview_data['Age'].values[0]))

    show_timelines(directory, snapshot_start_date, snapshot_end_date, customer_id)

    get_customer_location(address, customer_id)

    return


def cluster_overview_function(address, overview_data):
    col1, col2 = st.columns(2)
    column_names = ['Cluster RFM', 'Segment 1', 'Segment 2', 'Product cluster MBA', 'Category cluster MBA']
    cluster_type = col1.selectbox('Cluster type', column_names)
    cluster_ids = overview_data[cluster_type].sort_values(ascending=True).unique()
    cluster_id = col2.selectbox('Cluster', cluster_ids)

    global_mean_cltv = overview_data['CLTV'].mean()
    global_mean_age = overview_data['Age'].mean()
    overview_data = overview_data[overview_data[cluster_type] == cluster_id]
    local_mean_cltv = overview_data['CLTV'].mean()
    local_mean_age = overview_data['Age'].mean()

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric('Customers', len(overview_data))
    col2.metric('Average CLTV', round(local_mean_cltv, 2),
                str(round((local_mean_cltv - global_mean_cltv) / global_mean_cltv * 100, 2)) + ' %')
    col3.metric('Average Longevity', round(local_mean_age, 2),
                str(round((local_mean_age - global_mean_age) / global_mean_age * 100, 2)) + ' %')
    for column in column_names:
        unique_values = overview_data[column].unique()

        labels = []
        values = []

        for value in unique_values:
            count = (overview_data[column] == value).sum()
            labels.append(f"Cluster {value}")
            values.append(count)

        fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig.update_layout(title=f'Distribution of Clusters for {column}')
        st.plotly_chart(fig)

    customer_ids = overview_data[overview_data[cluster_type] == cluster_id]['Customer_ID']
    get_cluster_location(address, customer_ids)

    return


def freeze_and_send_data(overview_data, admin, ml_clusters, segment_1_clusters, segment_2_clusters, product_grouped_df,
                         category_grouped_df, product_recommendation, category_recommendation, directory, sales_filter,
                         customer_type, snapshot_start_date, snapshot_end_date):
    if admin:
        with st.form("checkpoint_form"):
            freeze_name = st.text_input('Name this Checkpoint', '')
            description = st.text_area('Description')

            with st.expander('Customers data'):
                st.dataframe(overview_data)
            with st.expander('Recommendation'):
                st.subheader('For products', divider='grey')
                st.dataframe(product_recommendation)
                st.subheader('For categories', divider='grey')
                st.dataframe(category_recommendation)
            with st.expander('Details about the clusters'):
                st.info('You can edit the clusters names !', icon='🚨')
                st.caption('The RFM values represent the average value within each cluster.')

                st.data_editor(ml_clusters, disabled=ml_clusters.columns)
                st.data_editor(segment_1_clusters, disabled=segment_1_clusters.columns)
                st.data_editor(segment_2_clusters, disabled=segment_2_clusters.columns)
                st.data_editor(product_grouped_df, disabled=product_grouped_df.columns)
                st.data_editor(category_grouped_df, disabled=category_grouped_df.columns)

            if st.form_submit_button('Save Checkpoint and Send Data', type='primary'):
                file_path = './Results/' + directory + '/freeze_' + freeze_name + '_' + sales_filter + '_' + customer_type + \
                            '_' + str(snapshot_start_date) + '_' + str(snapshot_end_date) + '.json'

                freeze_data = {
                    "Freeze_name": freeze_name,
                    "Directory": directory,
                    "sales_filter": sales_filter,
                    "customer_type": customer_type,
                    "snapshot_start_date": str(snapshot_start_date),
                    "snapshot_end_date": str(snapshot_end_date),
                    "description": description,
                    "overview_data": './Results/' + directory + '/overview_data_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv',
                    "product_recommendation": './Results/' + directory + '/product_recommendation_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv',
                    "category_recommendation": './Results/' + directory + '/category_recommendation_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv',
                    "ml_clusters": './Results/' + directory + '/ml_clusters_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv',
                    "segment_1_clusters": './Results/' + directory + '/segment_1_clusters_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv',
                    "segment_2_clusters": './Results/' + directory + '/segment_2_clusters_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv',
                    "product_grouped_df": './Results/' + directory + '/product_grouped_df_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv',
                    "category_grouped_df": './Results/' + directory + '/category_grouped_df_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv',
                }

                with open(file_path, "w") as json_file:
                    json.dump(freeze_data, json_file, indent=4)

                overview_data.set_index('Customer_ID', inplace=True)
                overview_data.to_csv(
                    './Results/' + directory + '/overview_data_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                product_recommendation.to_csv(
                    './Results/' + directory + '/product_recommendation_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                category_recommendation.to_csv(
                    './Results/' + directory + '/category_recommendation_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                ml_clusters.to_csv(
                    './Results/' + directory + '/ml_clusters_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                segment_1_clusters.to_csv(
                    './Results/' + directory + '/segment_1_clusters_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                segment_2_clusters.to_csv(
                    './Results/' + directory + '/segment_2_clusters_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                product_grouped_df.to_csv(
                    './Results/' + directory + '/product_grouped_df_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                category_grouped_df.to_csv(
                    './Results/' + directory + '/category_grouped_df_' + sales_filter + '_' + customer_type + '_' + str(
                        snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')

                if os.path.exists(file_path):
                    return st.toast('All the Data has been successfully sent !', icon="✅")
                else:
                    return st.toast("Failed to save Data.")
    else:
        with st.expander('Customers data'):
            st.dataframe(overview_data)
        with st.expander('Recommendation'):
            st.subheader('For products', divider='grey')
            st.dataframe(product_recommendation)
            st.subheader('For categories', divider='grey')
            st.dataframe(category_recommendation)
        show_details(ml_clusters, segment_1_clusters, segment_2_clusters, product_grouped_df, category_grouped_df)
    return


def overview_main_function(address, overview_data, ml_clusters, segment_1_clusters, segment_2_clusters,
                           product_grouped_df, category_grouped_df, product_recommendation, category_recommendation,
                           directory, snapshot_start_date, snapshot_end_date, admin, sales_filter, customer_type):
    customer_overview_tab, cluster_overview_tab, data_tab = st.tabs(
        ['Customer overview', 'Cluster overview', 'Download data'])

    with customer_overview_tab:
        st.subheader(f'Customer Overview', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        customer_overview_function(address, overview_data, directory, snapshot_start_date, snapshot_end_date)
        show_details(ml_clusters, segment_1_clusters, segment_2_clusters, product_grouped_df, category_grouped_df)

    with cluster_overview_tab:
        st.subheader('Cluster Overview', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        cluster_overview_function(address, overview_data)
        show_details(ml_clusters, segment_1_clusters, segment_2_clusters, product_grouped_df, category_grouped_df)

    with data_tab:
        freeze_and_send_data(overview_data, admin, ml_clusters, segment_1_clusters, segment_2_clusters,
                             product_grouped_df,
                             category_grouped_df, product_recommendation, category_recommendation, directory,
                             sales_filter,
                             customer_type, snapshot_start_date, snapshot_end_date)

    return
