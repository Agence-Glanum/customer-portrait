import datetime
import streamlit as st
from categories_tree import categories_tree
from customer_overview_functions import customer_overview_main_function
from home_functions import show_eda
from product_affinity_functions import prod_aff_main_function
from rfm_segmentation_functions import rfm_main_function
from most_frequent_pattern import most_frequent_pattern_main_function
from mba_statistics import mba_statistics_main_function
from utils.get_data import filter_data, get_dates
from customer_overview_functions import customer_overview_data_function
from map import create_map
# from map_function import map_function

st.set_page_config(page_title="Customer Portrait", layout="wide")
st.title(f"Customer Portrait")

with st.sidebar:
    directory = st.selectbox(
        "Choose which data to analyse",
        ["Ici store", "Glanum"])

    DATE_MIN, DATE_MAX = get_dates(directory)

    sales_filter = st.radio(
        "Analyze your sales based on",
        ["***Invoice***", "***Order***"],
        captions=["Sold items", "Ordered items"])
    transformed_sales_filter = sales_filter.replace('*', '')
    today = datetime.datetime.now()
    st.write("Choose a date range")

    snapshot_start_date = st.date_input("Start date", format="DD/MM/YYYY", value=DATE_MIN,
                                        min_value=datetime.date(1970, 1, 1), max_value=datetime.date.today())

    snapshot_end_date = st.date_input("End date", format="DD/MM/YYYY", value=DATE_MAX,
                                      min_value=datetime.date(1970, 1, 1), max_value=datetime.date.today())

address, categories, customers, invoices, invoices_lines, orders, orders_lines, products = filter_data(
    snapshot_start_date, snapshot_end_date, directory)

home_tab, rfm_seg_tab, mba_tab, customer_tab, map_tab = st.tabs(["Home", "RFM Segmentation", "MBA", "Customer Overview", "Map"])

if sales_filter == "***Invoice***":
    df_sales = invoices[(invoices['Paid'] == 1) & (invoices['Total_price'] > 0) & (invoices['Customer_ID'] is not None)]
    df_lines = invoices_lines[(invoices_lines['Quantity'] > 0) & (invoices_lines['Total_price'] > 0)]

if sales_filter == "***Order***":
    df_sales = orders[(orders['Status'] != 'draft') & (orders['Status'] != 'cancelled')
                      & (orders['Total_price'] > 0) & (orders['Customer_ID'] is not None)]
    df_lines = orders_lines[(orders_lines['Quantity'] > 0) & (orders_lines['Total_price'] > 0)]

if not df_sales.empty and not df_lines.empty:
    with home_tab:
        show_eda(invoices, orders, customers, products, categories, snapshot_start_date, snapshot_end_date, directory, transformed_sales_filter)

    with rfm_seg_tab:
        rfm, scaler, kmeans, average_clusters = rfm_main_function(df_sales, snapshot_end_date, customers, directory, snapshot_start_date, transformed_sales_filter)

    with mba_tab:
        mba_statistics, prod_aff_tab, most_freq_tab, product_pred_tab, data_tab = st.tabs(["Statistics", "Product affinity", "Most Frequent Pattern", "Next product prediction", "Data"])
        with mba_statistics:
            mba_statistics_main_function(df_sales, df_lines, products, categories, snapshot_start_date, snapshot_end_date, directory, transformed_sales_filter)
        with prod_aff_tab:
            prod_aff_main_function(df_sales, df_lines, categories, products, directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter)
        with most_freq_tab:
            most_frequent_pattern_main_function(df_lines, products, transformed_sales_filter)
        with data_tab:
            st.subheader(
                    f"Categories details for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]",
                    divider='grey')
            st.dataframe(categories_tree(categories, products, directory), use_container_width=True)

    with customer_tab:
        overview_tab, data_tab = st.tabs(["Customer overview", "Data"])
        with overview_tab:
            cltv_df = customer_overview_main_function(rfm, scaler, kmeans, average_clusters, df_sales, df_lines, transformed_sales_filter)
        with data_tab:
            customer_data_tab, customers_data_tab = st.tabs(["Customer data", "Customers data"])
            with customer_data_tab:
                customer_overview_data_function(rfm, df_sales, df_lines, transformed_sales_filter)
            with customers_data_tab:
                customer_overview_data_function(rfm, df_sales, df_lines, transformed_sales_filter, show_full_dataframe=True)

    with map_tab:
        create_map(address, 'City', 'Customer_Count', 'Customer')
else:
    st.error("No data available for the selected time period !")

if __name__ == '__main__':
    print('#########################################')
    print('Running : main')
