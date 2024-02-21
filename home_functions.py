import streamlit as st
from utils.data_viz import show_timelines, show_boxplot
from utils.utility_functions import compute_kpis, get_customers_heatmap


def show_geodemographic_profiling(address):
    address_type = st.radio('Address type', ['Invoice', 'Delivery'], horizontal=True)

    if address_type == 'Invoice':
        address = address[address['Address_type'] == 'invoice']
        get_customers_heatmap(address)
    elif address_type == 'Delivery':
        address = address[address['Address_type'] == 'delivery']
        get_customers_heatmap(address)
    return


def home_main_function(invoices, orders, customers, products, categories, cltv_df, snapshot_start_date, snapshot_end_date, directory):
    st.subheader(
        f'KPIs for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]',
        divider='grey')
    compute_kpis(invoices, orders, customers, categories, products, cltv_df)

    st.subheader(
        f'Revenue details for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]',
        divider='grey')
    st.write('Timeline of Sales and Orders')
    show_timelines(directory, snapshot_start_date, snapshot_end_date)
    st.write('Boxplot for both Sales and Orders')
    show_boxplot(invoices, orders)

    return
