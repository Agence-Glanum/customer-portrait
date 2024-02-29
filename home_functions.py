import streamlit as st
from utils.data_viz import show_timelines
from utils.utility_functions import compute_kpis, get_customers_heatmap


def geodemographic_profiling_main_function(address, directory, sales_filter, customer_type,
                                           snapshot_start_date, snapshot_end_date):
    st.subheader(f'Geographical distribution of Customers', divider='grey')
    st.info(f'Company: :blue[{directory}]' +
            f'\n\nData type: :blue[{sales_filter}]' +
            f'\n\nCustomer type: :blue[{customer_type}]' +
            f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
    address_type = st.radio('Address type', ['Invoice', 'Delivery'], horizontal=True)

    if address_type == 'Invoice':
        address = address[(address['Address_type'] == 'invoice') | (address['Address_type'] == 'both')]
    elif address_type == 'Delivery':
        address = address[(address['Address_type'] == 'delivery') | (address['Address_type'] == 'both')]
    try:
        get_customers_heatmap(address)
    except AttributeError:
        st.error('No address for the selected filter !')
    return


def home_main_function(invoices, orders, customers, products, categories, cltv_df, customer_type, snapshot_start_date,
                       snapshot_end_date, directory):
    st.subheader('General KPIs', divider='grey')
    st.info(f'Company: :blue[{directory}]' +
            f'\n\nData type: :blue[Invoices and Orders]' +
            f'\n\nCustomer type: :blue[{customer_type}]' +
            f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon="ℹ️")
    compute_kpis(invoices, orders, customers, categories, products, cltv_df)

    st.subheader(f'Revenue details', divider='grey')
    st.info(f'Company: :blue[{directory}]' +
            f'\n\nData type: :blue[Invoices and Orders]' +
            f'\n\nCustomer type: :blue[{customer_type}]' +
            f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon="ℹ️")
    show_timelines(directory, snapshot_start_date, snapshot_end_date)

    return
