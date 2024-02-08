import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show_kpis(invoices, orders, categories, products):
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric('Customers', invoices['Customer_ID'].nunique())
    col1.metric('Categories Count', str(len(categories)))
    col1.metric('Products Count', str(len(products)))
    col2.metric('Invoices', invoices['Invoice_ID'].nunique())
    col2.metric('Orders', orders['Order_ID'].nunique())

    col3.metric('Average Invoice Value', str(round(invoices['Total_price'].mean(), 2)) + '€')
    col3.metric('Average Order Value', str(round(orders['Total_price'].mean(), 2)) + '€')

    col4.metric('Minimum Invoice Value', str(round(invoices['Total_price'].min(), 2)) + '')
    col4.metric('Maximum Invoice Value', str(round(invoices['Total_price'].max(), 2)) + '')

    col5.metric('Minimum orders Value', str(round(orders['Total_price'].min(), 2)) + '')
    col5.metric('Maximum orders Value', str(round(orders['Total_price'].max(), 2)) + '')


def show_boxplot(invoices, orders):
    fig = make_subplots(rows=1, cols=1)

    fig.add_trace(go.Box(x=invoices['Total_price'], name='Invoices'))
    fig.add_trace(go.Box(x=orders['Total_price'], name='Orders'))
    fig.update_layout(xaxis_title='Monetary value')
    fig.update_layout(showlegend=True)

    st.plotly_chart(fig, use_container_width=True)


def show_timelines(invoices, orders, snapshot_start_date, snapshot_end_date):
    invoices['Invoice_date'] = pd.to_datetime(invoices['Invoice_date']).dt.normalize()
    orders['Order_date'] = pd.to_datetime(orders['Order_date']).dt.normalize()

    min_date = min(invoices['Invoice_date'].min(), orders['Order_date'].min())
    max_date = max(invoices['Invoice_date'].max(), orders['Order_date'].max())

    min_value = min(invoices['Total_price'].min(), orders['Total_price'].min())
    max_value = max(invoices['Total_price'].max(), orders['Total_price'].max())

    paid_invoices = invoices[(invoices['Paid'] == 1) & (invoices['Total_price'] > 0)]
    unpaid_invoices = invoices[(invoices['Paid'] == 0) & (invoices['Total_price'] > 0)]
    valid_orders = orders[(orders['Status'] != 'draft') & (orders['Status'] != 'cancelled')
                          & (orders['Total_price'] > 0)]
    invalid_orders = orders[(orders['Status'] == 'draft') | (orders['Status'] == 'cancelled')
                            & (orders['Total_price'] > 0)]

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(x=paid_invoices['Invoice_date'], y=paid_invoices['Total_price'],
                              name='Paid Invoices', line=dict(color='blue')))
    fig2.add_trace(go.Scatter(x=unpaid_invoices['Invoice_date'], y=unpaid_invoices['Total_price'],
                              name='Unpaid Invoices', line=dict(color='red')))
    fig2.add_trace(go.Scatter(x=valid_orders['Order_date'], y=valid_orders['Total_price'],
                              name='Valid Orders', line=dict(color='green')))
    fig2.add_trace(go.Scatter(x=invalid_orders['Order_date'], y=invalid_orders['Total_price'],
                              name='Invalid Orders', line=dict(color='pink')))
    fig2.update_layout(xaxis_title='Date', yaxis_title='Monetary value')
    fig2.add_shape(type='rect', x0=snapshot_start_date, x1=snapshot_end_date, y0=min_value, y1=max_value,
                   fillcolor='lightblue', opacity=0.5, layer='below', line_width=0)
    fig2.update_xaxes(range=[min_date, max_date])

    st.plotly_chart(fig2, use_container_width=True)


def show_eda(invoices, orders, customers, products, categories, snapshot_start_date, snapshot_end_date, directory,
             transformed_sales_filter):
    st.subheader(
        f'KPIs for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]',
        divider='grey')
    show_kpis(invoices, orders, categories, products)

    st.subheader(
        f'Revenue details for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]',
        divider='grey')
    st.write('Timeline of Sales and Orders')
    show_timelines(invoices, orders, snapshot_start_date, snapshot_end_date)
    st.write('Boxplot for both Sales and Orders')
    show_boxplot(invoices, orders)
