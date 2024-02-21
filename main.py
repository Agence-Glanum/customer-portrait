import os
import datetime
import pandas as pd
import streamlit as st
from mba import mba_main_function
from home_functions import home_main_function, show_geodemographic_profiling
from rfm_segmentation_functions import rfm_main_function
from mba_statistics import mba_statistics_main_function
from utils.get_data import filter_data, get_dates
from overview_functions import overview_main_function
from utils.authentification import get_auth_status, render_login_form, get_user_type, logout
from utils.utility_functions import compute_lifetime_value


def get_folder_names(directory):
    folder_names = []
    for item in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, item)):
            folder_names.append(item)
    return folder_names


def get_filters():
    with st.sidebar:
        if get_auth_status():
            st.button('Logout', on_click=logout)

        companies = get_folder_names('./data')

        directory = st.selectbox(
            'Choose which data to analyse', companies)

        sales_filter = st.radio(
            'Analyze your sales based on',
            ['***Invoice***', '***Order***'],
            captions=['Sold items', 'Ordered items'])
        sales_filter = sales_filter.replace('*', '')

        customer_type = st.radio(
            'Choose the customer\'s type',
            ['B2B', 'B2C'])

        DATE_MIN, DATE_MAX = get_dates(directory)
        st.write('Choose a date range')
        snapshot_start_date = st.date_input('Start date', format='DD/MM/YYYY', value=DATE_MIN,
                                            min_value=datetime.date(1970, 1, 1), max_value=datetime.date.today())
        snapshot_end_date = st.date_input('End date', format='DD/MM/YYYY', value=DATE_MAX,
                                          min_value=datetime.date(1970, 1, 1), max_value=datetime.date.today())
    return directory, sales_filter, customer_type, snapshot_start_date, snapshot_end_date


def data_main():
    directory, sales_filter, customer_type, snapshot_start_date, snapshot_end_date = get_filters()
    address, categories, customers, invoices, invoices_lines, orders, orders_lines, products = filter_data(customer_type,
                                                                                                           sales_filter,
                                                                                                           snapshot_start_date,
                                                                                                           snapshot_end_date,
                                                                                                           directory)
    home_tab, geo_tab, rfm_seg_tab, mba_tab, customer_tab = st.tabs(
        ['Home', 'Geodemographic profiling', 'RFM Segmentation', 'MBA', 'Overview'])

    df_sales, df_lines = invoices, invoices_lines
    if sales_filter == 'Invoice':
        df_sales = invoices[
            (invoices['Paid'] == 1) & (invoices['Customer_ID'] is not None)]
        df_lines = invoices_lines[(invoices_lines['Quantity'] > 0)]

    if sales_filter == 'Order':
        df_sales = orders[(orders['Status'] != 'draft') & (orders['Status'] != 'cancelled')
                          & (orders['Customer_ID'] is not None)]
        df_lines = orders_lines[(orders_lines['Quantity'] > 0)]

    if not df_sales.empty and not df_lines.empty:
        with home_tab:
            cltv_df = compute_lifetime_value(df_sales, df_lines, sales_filter)
            home_main_function(invoices, orders, customers, products, categories, cltv_df, snapshot_start_date, snapshot_end_date, directory)

        with geo_tab:
            st.subheader(
                f'Heatmap for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]')
            show_geodemographic_profiling(address)

        with rfm_seg_tab:
            rfm, ml_clusters, segment_1_clusters, segment_2_clusters = rfm_main_function(
                df_sales, snapshot_end_date, customers, directory,
                snapshot_start_date, sales_filter)

        with mba_tab:
            product_clusters, category_clusters, product_grouped_df, category_grouped_df, product_recommendation, category_recommendation = mba_main_function(
                df_sales, df_lines, products, categories, snapshot_start_date,
                snapshot_end_date, directory, sales_filter)

        with customer_tab:
            overview_data = pd.merge(rfm, product_clusters.reset_index()[['Customer_ID', 'Cluster MBA']],
                                     on='Customer_ID')
            overview_data = overview_data.rename(columns={'Cluster MBA': 'Product cluster MBA'})
            overview_data = pd.merge(overview_data, category_clusters.reset_index()[['Customer_ID', 'Cluster MBA']],
                                     on='Customer_ID')
            overview_data = overview_data.rename(columns={'Cluster MBA': 'Category cluster MBA'})
            overview_data = pd.merge(overview_data, cltv_df, on='Customer_ID')

            overview_main_function(address, overview_data, ml_clusters, segment_1_clusters, segment_2_clusters,
                                   product_grouped_df, category_grouped_df, product_recommendation,
                                   category_recommendation, directory, snapshot_start_date, snapshot_end_date, True,
                                   sales_filter, customer_type)

    else:
        st.error('No data available for the selected time period !')
    return


def marketing_main():
    directory, sales_filter, customer_type, snapshot_start_date, snapshot_end_date = get_filters()
    address, categories, customers, invoices, invoices_lines, orders, orders_lines, products = filter_data(customer_type,
                                                                                                           sales_filter,
                                                                                                           snapshot_start_date,
                                                                                                           snapshot_end_date,
                                                                                                           directory)
    statistics_tab, overview_tab = st.tabs(['Statistics', 'Overview'])

    df_sales, df_lines = invoices, invoices_lines
    if sales_filter == 'Invoice':
        df_sales = invoices[
            (invoices['Paid'] == 1) & (invoices['Total_price'] > 0) & (invoices['Customer_ID'] is not None)]
        df_lines = invoices_lines[(invoices_lines['Quantity'] > 0) & (invoices_lines['Total_price'] > 0)]

    if sales_filter == 'Order':
        df_sales = orders[(orders['Status'] != 'draft') & (orders['Status'] != 'cancelled')
                          & (orders['Total_price'] > 0) & (orders['Customer_ID'] is not None)]
        df_lines = orders_lines[(orders_lines['Quantity'] > 0) & (orders_lines['Total_price'] > 0)]

    if not df_sales.empty and not df_lines.empty:
        with statistics_tab:
            cltv_df = compute_lifetime_value(df_sales, df_lines, sales_filter)
            home_main_function(products, categories, cltv_df, snapshot_start_date, snapshot_end_date, directory)
            mba_statistics_main_function(df_sales, df_lines, products, categories, snapshot_start_date,
                                         snapshot_end_date, directory, sales_filter)

        with overview_tab:
            try:
                overview_data = pd.read_csv('./Results/overview_data_' + directory + '_' + sales_filter + '_' + customer_type + '_' + str(snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                ml_clusters = pd.read_csv('./Results/ml_clusters_' + directory + '_' + sales_filter + '_' + customer_type + '_' + str(snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                segment_1_clusters = pd.read_csv('./Results/segment_1_clusters_' + directory + '_' + sales_filter + '_' + customer_type + '_' + str(snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                segment_2_clusters = pd.read_csv('./Results/segment_2_clusters_' + directory + '_' + sales_filter + '_' + customer_type + '_' + str(snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                product_grouped_df = pd.read_csv('./Results/product_grouped_df_' + directory + '_' + sales_filter + '_' + customer_type + '_' + str(snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                category_grouped_df = pd.read_csv('./Results/category_grouped_df_' + directory + '_' + sales_filter + '_' + customer_type + '_' + str(snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                product_recommendation = pd.read_csv('./Results/product_recommendation_' + directory + '_' + sales_filter + '_' + customer_type + '_' + str(snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')
                category_recommendation = pd.read_csv('./Results/category_recommendation_' + directory + '_' + sales_filter + '_' + customer_type + '_' + str(snapshot_start_date) + '_' + str(snapshot_end_date) + '.csv')

                overview_main_function(address, overview_data, ml_clusters, segment_1_clusters, segment_2_clusters,
                                       product_grouped_df, category_grouped_df, product_recommendation,
                                       category_recommendation, directory, snapshot_start_date, snapshot_end_date, False, sales_filter, customer_type)
            except FileNotFoundError:
                st.error('The Data team hasn\'t sent any data yet !')

    else:
        st.error('No data available for the selected time period !')

    return


def main():
    st.set_page_config(page_title='Customer Portrait', layout='centered')
    st.title(f'Customer Portrait')

    if not get_auth_status():
        user = render_login_form()
    else:
        user = get_user_type()

    if user == 'data':
        data_main()
    elif user == 'marketing':
        marketing_main()

    return


if __name__ == '__main__':
    print('#########################################')
    print('Running : main')
    main()
