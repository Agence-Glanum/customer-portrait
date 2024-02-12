import datetime
import pandas as pd
import streamlit as st
from mba import show_mba
from home_functions import show_eda
from product_affinity_functions import prod_aff_main_function
from rfm_segmentation_functions import rfm_main_function
from most_frequent_pattern import most_frequent_pattern_main_function
from mba_statistics import mba_statistics_main_function
from utils.get_data import filter_data, get_dates
from overview_functions import overview_main_function
from next_product_prediction import next_prod_pred_main_function
from utils.authentification import get_auth_status, render_login_form, get_user_type, logout
from utils.utility_functions import compute_lifetime_value


def get_filters(flag):
    with st.sidebar:
        if get_auth_status():
            st.button('Logout', on_click=logout)

        directory = st.selectbox(
            'Choose which data to analyse',
            ['Ici store', 'Glanum', 'Olist'], disabled=flag)

        sales_filter = st.radio(
            'Analyze your sales based on',
            ['***Invoice***', '***Order***'],
            captions=['Sold items', 'Ordered items'])
        sales_filter = sales_filter.replace('*', '')

        client_type = st.radio(
            'Choose the customer\'s type',
            ['B2B', 'B2C'])

        DATE_MIN, DATE_MAX = get_dates(directory)
        st.write('Choose a date range')
        snapshot_start_date = st.date_input('Start date', format='DD/MM/YYYY', value=DATE_MIN,
                                            min_value=datetime.date(1970, 1, 1), max_value=datetime.date.today())
        snapshot_end_date = st.date_input('End date', format='DD/MM/YYYY', value=DATE_MAX,
                                          min_value=datetime.date(1970, 1, 1), max_value=datetime.date.today())
    return directory, sales_filter, client_type, snapshot_start_date, snapshot_end_date


def data_main():
    directory, sales_filter, client_type, snapshot_start_date, snapshot_end_date = get_filters(False)
    address, categories, customers, invoices, invoices_lines, orders, orders_lines, products = filter_data(client_type,
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
            show_eda(products, categories, cltv_df, snapshot_start_date, snapshot_end_date, directory)

        with geo_tab:
            st.write('Map')

        with rfm_seg_tab:
            rfm, ml_clusters, segment_1_clusters, segment_2_clusters = rfm_main_function(
                df_sales, snapshot_end_date, customers, directory,
                snapshot_start_date, sales_filter)

        with mba_tab:
            mba_statistics, prod_aff_tab, most_freq_tab, product_pred_tab, data_tab = st.tabs(
                ['Statistics', 'Product affinity', 'Most Frequent Pattern', 'Next product prediction', 'Data'])
            with mba_statistics:
                mba_statistics_main_function(df_sales, df_lines, products, categories, snapshot_start_date,
                                             snapshot_end_date, directory, sales_filter)
            with prod_aff_tab:
                product_clusters, category_clusters = prod_aff_main_function(df_sales, df_lines, categories, products,
                                                                             directory, snapshot_start_date,
                                                                             snapshot_end_date, sales_filter)
            with most_freq_tab:
                apriori_rules_products, fpgrowth_rules_products, apriori_rules_categories, fpgrowth_rules_categories = most_frequent_pattern_main_function(
                    df_lines, products, categories,
                    sales_filter)
            with product_pred_tab:
                next_prod_pred_main_function(apriori_rules_products, fpgrowth_rules_products, products)
            with data_tab:
                product_grouped_df, category_grouped_df = show_mba(directory, products, product_clusters, category_clusters,
                                                                   apriori_rules_products, fpgrowth_rules_products,
                                                                   apriori_rules_categories, fpgrowth_rules_categories)

        with customer_tab:
            overview_data = pd.merge(rfm, product_clusters.reset_index()[['Customer_ID', 'Cluster MBA']],
                                     on='Customer_ID')
            overview_data = overview_data.rename(columns={'Cluster MBA': 'Product cluster MBA'})
            overview_data = pd.merge(overview_data, category_clusters.reset_index()[['Customer_ID', 'Cluster MBA']],
                                     on='Customer_ID')
            overview_data = overview_data.rename(columns={'Cluster MBA': 'Category cluster MBA'})
            overview_data = pd.merge(overview_data, cltv_df, on='Customer_ID')

            overview_main_function(address, overview_data, ml_clusters, segment_1_clusters, segment_2_clusters,
                                   product_grouped_df, category_grouped_df, directory, snapshot_start_date, snapshot_end_date)

    else:
        st.error('No data available for the selected time period !')
    return


def marketing_main():
    directory, sales_filter, client_type, snapshot_start_date, snapshot_end_date = get_filters(True)
    address, categories, customers, invoices, invoices_lines, orders, orders_lines, products = filter_data(client_type,
                                                                                                           snapshot_start_date,
                                                                                                           snapshot_end_date,
                                                                                                           directory)
    statistics_tab, rfm_tab, mba_tab, cluster_tab = st.tabs(
        ['Statistics', 'RFM Results', 'MBA Results', 'Overview'])

    df_sales, df_lines = invoices, invoices_lines
    if sales_filter == 'Invoice':
        df_sales = invoices[
            (invoices['Paid'] == 1) & (invoices['Total_price'] > 0) & (invoices['Customer_ID'] is not None)]
        df_lines = invoices_lines[(invoices_lines['Quantity'] > 0) & (invoices_lines['Total_price'] > 0)]

    if sales_filter == 'Order':
        df_sales = orders[(orders['Status'] != 'draft') & (orders['Status'] != 'cancelled')
                          & (orders['Total_price'] > 0) & (orders['Customer_ID'] is not None)]
        df_lines = orders_lines[(orders_lines['Quantity'] > 0) & (orders_lines['Total_price'] > 0)]

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
