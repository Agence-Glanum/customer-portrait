import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_viz import show_timelines
from customer_overview_functions import compute_lifetime_value


def show_kpis(invoices, invoices_lines, orders, categories, products, transformed_sales_filter):
    # cltv_df = compute_lifetime_value(invoices, invoices_lines, transformed_sales_filter)

    col1, col2, col3 = st.columns(3)

    col1.metric('Customers', invoices['Customer_ID'].nunique())
    col1.metric('Categories Count', str(len(categories)))
    col1.metric('Products Count', str(len(products)))
    # col1.metric('Average LTV', round(cltv_df['CLTV'].mean(), 2))

    valid_orders = orders[(orders['Status'] != 'draft') & (orders['Status'] != 'cancelled')]
    col2.metric('Orders', valid_orders['Order_ID'].nunique())
    col2.metric('Minimum orders Value', str(round(valid_orders['Total_price'].min(), 2)) + '€')
    col2.metric('Average Order Value', str(round(valid_orders['Total_price'].mean(), 2)) + '€')
    col2.metric('Maximum orders Value', str(round(valid_orders['Total_price'].max(), 2)) + '€')

    col3.metric('Invoices', invoices['Invoice_ID'].nunique())
    col3.metric('Minimum Invoice Value', str(round(invoices['Total_price'].min(), 2)) + '€')
    col3.metric('Average Invoice Value', str(round(invoices['Total_price'].mean(), 2)) + '€')
    col3.metric('Maximum Invoice Value', str(round(invoices['Total_price'].max(), 2)) + '€')

    return


def show_boxplot(invoices, orders):
    fig = make_subplots(rows=1, cols=1)

    fig.add_trace(go.Box(x=invoices['Total_price'], name='Invoices'))
    fig.add_trace(go.Box(x=orders['Total_price'], name='Orders'))
    fig.update_layout(xaxis_title='Monetary value')
    fig.update_layout(showlegend=True)

    st.plotly_chart(fig, use_container_width=True)

    return


def show_eda(products, categories, invoices_lines, snapshot_start_date, snapshot_end_date, directory, transformed_sales_filter):
    path = './data/Glanum/' if directory == 'Glanum' else './data/IciStore/'
    invoices = pd.read_csv(f'{path}/Invoices.csv')
    orders = pd.read_csv(f'{path}/Orders.csv')

    st.subheader(
        f'KPIs for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]',
        divider='grey')
    show_kpis(invoices, invoices_lines, orders, categories, products, transformed_sales_filter)

    st.subheader(
        f'Revenue details for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]',
        divider='grey')
    st.write('Timeline of Sales and Orders')
    show_timelines(invoices, orders, snapshot_start_date, snapshot_end_date)
    st.write('Boxplot for both Sales and Orders')
    show_boxplot(invoices, orders)

    return
