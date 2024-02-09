import os
import datetime
import streamlit as st
from dotenv import load_dotenv
from mba import show_mba
from customer_overview_functions import customer_overview_main_function
from home_functions import show_eda
from product_affinity_functions import prod_aff_main_function
from rfm_segmentation_functions import rfm_main_function
from most_frequent_pattern import most_frequent_pattern_main_function
from mba_statistics import mba_statistics_main_function
from utils.get_data import filter_data, get_dates
from customer_overview_functions import customer_overview_data_function
from next_product_prediction import next_prod_pred_main_function

load_dotenv()
data_username = os.environ.get('DATA_USERNAME')
data_password = os.environ.get('DATA_PASSWORD')
marketing_username = os.environ.get('MARKETING_USERNAME')
marketing_password = os.environ.get('MARKETING_PASSWORD')


def get_filters(flag):
    with st.sidebar:
        if get_auth_status():
            st.button('Logout', on_click=logout)

        directory = st.selectbox(
            'Choose which data to analyse',
            ['Ici store', 'Glanum'], disabled=flag)

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
        ['Home', 'Geodemographic profiling', 'RFM Segmentation', 'MBA', 'Customer Overview'])

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
        with home_tab:
            show_eda(invoices, orders, customers, products, categories, snapshot_start_date, snapshot_end_date,
                     directory, sales_filter)

        with geo_tab:
            st.write('Map')

        with rfm_seg_tab:
            rfm, scaler, kmeans, average_clusters = rfm_main_function(df_sales, snapshot_end_date, customers, directory,
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
                apriori_rules, fpgrowth_rules = most_frequent_pattern_main_function(df_lines, products, categories,
                                                                                    sales_filter)
            with product_pred_tab:
                next_prod_pred_main_function(apriori_rules, fpgrowth_rules, products)
            with data_tab:
                show_mba(directory, products, product_clusters, category_clusters)

        with customer_tab:
            overview_tab, data_tab = st.tabs(['Customer overview', 'Data'])
            with overview_tab:
                customer_overview_main_function(directory, invoices,orders, address, rfm, scaler, kmeans, average_clusters, df_sales,
                                                df_lines, snapshot_start_date, snapshot_end_date, sales_filter)
            with data_tab:
                customer_data_tab, customers_data_tab = st.tabs(['Customer data', 'Customers data'])
                with customer_data_tab:
                    customer_overview_data_function(rfm, df_sales, df_lines, sales_filter)
                with customers_data_tab:
                    customer_overview_data_function(rfm, df_sales, df_lines, sales_filter, show_full_dataframe=True)
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
        ['Statistics', 'RFM Results', 'MBA Results', 'Cluster Overview'])
    with statistics_tab:
        st.write('Hello')


def get_user_type():
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    return st.session_state.user_type


def set_user_type(user_type):
    st.session_state.user_type = user_type


def authenticate(username, password):
    if (username == data_username) & (password == data_password):
        return 'data'
    elif (username == marketing_username) & (password == marketing_password):
        return 'marketing'
    else:
        return None


def get_auth_status():
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = False
    return st.session_state.auth_status


def set_auth_status(status):
    st.session_state.auth_status = status


def render_login_form():
    placeholder = st.empty()
    with placeholder.form('authentifiation'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        login = st.form_submit_button('Login')
    if login:
        auth_result = authenticate(username, password)
        if auth_result:
            placeholder.empty()
            set_auth_status(True)
            set_user_type(auth_result)
            return auth_result
        else:
            st.write('Wrong username or password !')
            st.stop()
    return None


def logout():
    set_auth_status(False)
    set_user_type(None)


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
