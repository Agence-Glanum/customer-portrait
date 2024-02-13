import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.data_viz import show_timelines
from utils.utility_functions import get_customer_location, get_cluster_location


def customer_overview_function(address, overview_data, directory, snapshot_start_date, snapshot_end_date):
    customer_id = st.selectbox('Customers',
                               (overview_data['Customer_ID'].astype(str) + ' - ' + overview_data['Customer_name']))
    customer_id = int(customer_id.split(' - ')[0])
    mean_cltv = overview_data['CLTV'].mean()
    overview_data = overview_data[overview_data['Customer_ID'] == customer_id]

    col1, col2, col3 = st.columns(3)

    col1.write('***RFM clusters***')
    col1.metric('ML cluster', 'Cluster ' + str(overview_data['Cluster RFM'].values[0]))
    col1.metric('Segment 1', str(overview_data['Segment 1'].values[0]))
    col1.metric('Segment 2', str(overview_data['Segment 2'].values[0]))

    col2.write('***MBA clusters***')
    col2.metric('Product cluster', 'Cluster ' + str(overview_data['Product cluster MBA'].values[0]))
    col2.metric('Category cluster', 'Cluster ' + str(overview_data['Category cluster MBA'].values[0]))

    col3.metric('Lifetime value', str(round(overview_data['CLTV'].values[0], 2)),
                str(round((overview_data['CLTV'].values[0] - mean_cltv) / mean_cltv * 100, 2)) + ' %')

    st.subheader('Timeline of Sales and Orders')
    path = './data/Glanum/' if directory == 'Glanum' else './data/IciStore/'
    invoices = pd.read_csv(f'{path}/Invoices.csv')
    orders = pd.read_csv(f'{path}/Orders.csv')

    show_timelines(invoices[(invoices['Customer_ID'] == customer_id)],
                   orders[(orders['Customer_ID'] == customer_id)], snapshot_start_date, snapshot_end_date)

    st.subheader('Customer Location')
    get_customer_location(address, customer_id)

    return


def cluster_overview_function(address, overview_data):
    global_mean_cltv = overview_data['CLTV'].mean()

    col1, col2 = st.columns(2)
    column_names = ['Cluster RFM', 'Segment 1', 'Segment 2', 'Product cluster MBA', 'Category cluster MBA']
    cluster_type = col1.selectbox('Cluster type', column_names)
    cluster_ids = overview_data[cluster_type].sort_values(ascending=True).unique()
    cluster_id = col2.selectbox('Cluster', cluster_ids)

    overview_data = overview_data[overview_data[cluster_type] == cluster_id]
    st.dataframe(
        overview_data[['Cluster RFM', 'Segment 1', 'Segment 2', 'Product cluster MBA', 'Category cluster MBA', 'CLTV']])

    st.subheader("Quick recap", divider='grey')
    col1, col2 = st.columns(2)
    col1.write(f"- **Customers**: {len(overview_data)}")
    local_mean_cltv = overview_data['CLTV'].mean()
    col2.write(f"- **Average CLTV**: {round(local_mean_cltv, 2)} "
               f" ({str(round((local_mean_cltv - global_mean_cltv) / global_mean_cltv * 100, 2)) + ' %'})")
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

    st.subheader('Cluster Location')
    get_cluster_location(address, cluster_id)

    return


def overview_main_function(address, overview_data, ml_clusters, segment_1_clusters, segment_2_clusters,
                           product_grouped_df, category_grouped_df, product_recommendation, category_recommendation,
                           directory, snapshot_start_date, snapshot_end_date):
    customer_overview_tab, cluster_overview_tab, data_tab = st.tabs(['Customer overview', 'Cluster overview', 'Download data'])

    def show_details():
        with st.expander('Details about the clusters'):
            st.dataframe(ml_clusters)
            st.dataframe(segment_1_clusters)
            st.dataframe(segment_2_clusters)
            st.dataframe(product_grouped_df)
            st.dataframe(category_grouped_df)

    with customer_overview_tab:
        customer_overview_function(address, overview_data, directory, snapshot_start_date, snapshot_end_date)
        show_details()

    with cluster_overview_tab:
        cluster_overview_function(address, overview_data)
        show_details()
    with data_tab:
        with st.expander('Customers data'):
            st.dataframe(overview_data)
        with st.expander('Recommendation'):
            st.subheader('For products', divider='grey')
            st.dataframe(product_recommendation)
            st.subheader('For categories', divider='grey')
            st.dataframe(category_recommendation)
        show_details()
    return
