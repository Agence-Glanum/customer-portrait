import datetime

import pandas as pd
import streamlit as st

from categories_tree import categories_tree
from customer_overview_functions import customer_overview_main_function
from home_functions import show_eda
from product_affinity_functions import prod_aff_main_function
from rfm_segmentation_functions import rfm_main_function
from most_frequent_pattern import most_frequent_pattern_main_function
from mba_statistics import mba_statistics_main_function
from utils.get_data import filter_data
from utils.get_data import transform_data
from customer_overview_functions import customer_overview_data_function
# from map_function import map_function

st.set_page_config(page_title="Customer Portrait", layout="wide")
st.title(f"Customer Portrait")

with st.sidebar:
    directory = st.selectbox(
        "Choose which data to analyse",
        ["Ici store", "Glanum"])
    address, categories, customer, invoices, invoices_lines, orders, orders_lines, products = transform_data(directory)

    sales_filter = st.radio(
        "Analyze your sales based on",
        ["***Invoice***", "***Order***"], disabled=True,
        captions=["Sold items", "Ordered items"])
    transformed_sales_filter = sales_filter.replace('*', '')
    today = datetime.datetime.now()
    st.write("Choose a date range")

    snapshot_start_date = st.date_input("Start date", format="DD/MM/YYYY", value=invoices["Invoice_date"].min(),
                                        min_value=datetime.date(1970, 1, 1), max_value=datetime.date.today())

    snapshot_end_date = st.date_input("End date", format="DD/MM/YYYY", value=invoices["Invoice_date"].max(),
                                      min_value=datetime.date(1970, 1, 1), max_value=datetime.date.today())

address, categories, customers, invoices, invoices_lines, orders, orders_lines, products = filter_data(
    snapshot_start_date, snapshot_end_date, directory)

home_tab, rfm_seg_tab, mba_tab, customer_tab = st.tabs(["Home", "RFM Segmentation", "MBA", "Customer Overview"])

if sales_filter == "***Invoice***":
    df = invoices
    if not df.empty:
        with home_tab:
            show_eda(invoices, orders, customers, products, categories, snapshot_start_date, snapshot_end_date, directory, transformed_sales_filter)

        with rfm_seg_tab:
            rfm, scaler, kmeans, average_clusters = rfm_main_function(df, snapshot_end_date, customers, directory, snapshot_start_date, transformed_sales_filter)

        with mba_tab:
            mba_statistics, prod_aff_tab, most_freq_tab, product_pred_tab, data_tab = st.tabs(["Statistics", "Product affinity", "Most Frequent Pattern", "Next product prediction", "Data"])
            with mba_statistics:
                mba_statistics_main_function(invoices, invoices_lines, products, categories, snapshot_start_date, snapshot_end_date, directory, transformed_sales_filter)
            with prod_aff_tab:
                prod_aff_main_function(invoices, invoices_lines, products, categories, directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter)
            with most_freq_tab:
                most_frequent_pattern_main_function(invoices_lines, products)
            with data_tab:
                st.subheader(
                    f"Categories details for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]",
                    divider='grey')
                st.dataframe(categories_tree(categories, products, directory), use_container_width=True)

        with customer_tab:
            overview_tab, data_tab = st.tabs(["Customer Overview", "Data"])
            with overview_tab:
                customer_overview_main_function(rfm, scaler, kmeans, average_clusters, invoices, invoices_lines, customers, orders, directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter, address)
            with data_tab:
                customer_data_tab, customers_data_tab = st.tabs(["Customer data", "Customers data"])
                with customer_data_tab:
                    # customer_overview_data_function(rfm, invoices, invoices_lines)
                    customer_overview_data_function(rfm, invoices, invoices_lines)
                with customers_data_tab:
                    # customers_overview_data_function(rfm, invoices, invoices_lines)
                    customer_overview_data_function(rfm, invoices, invoices_lines, show_full_dataframe=True)
        # with map_tab:
        #     # map_function(address)
        #     print("map tab")
    else:
        st.error("No data available for the selected time period !")

if __name__ == '__main__':
    print('#########################################')
    print('Running : main')
