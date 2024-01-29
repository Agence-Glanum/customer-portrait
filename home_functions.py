import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def show_eda(invoices, orders, customers, products, categories, snapshot_start_date, snapshot_end_date, directory, transformed_sales_filter):
    st.subheader(f"KPIS for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]", divider='grey')
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Customers", invoices['Customer_ID'].nunique())
    col1.metric("Categories Count", str(len(categories)))
    col1.metric("Products Count", str(len(products)))
    col2.metric("Invoices", invoices['Invoice_ID'].nunique())
    col2.metric("Orders", orders['Order_ID'].nunique())

    col3.metric("Average Invoice Value", str(round(invoices['Total_price'].mean(), 2)) + "€")
    col3.metric("Average Order Value", str(round(orders['Total_price'].mean(), 2)) + "€")

    col4.metric("Minimum Invoice Value", str(round(invoices['Total_price'].min(), 2)) + "")
    col4.metric("Maximum Invoice Value", str(round(invoices['Total_price'].max(), 2)) + "")

    col5.metric("Minimum orders Value", str(round(orders['Total_price'].min(), 2)) + "")
    col5.metric("Maximum orders Value", str(round(orders['Total_price'].max(), 2)) + "")

    # invoices['Invoice_date'] = pd.to_datetime(invoices['Invoice_date']).dt.normalize()
    # orders['Order_date'] = pd.to_datetime(orders['Order_date']).dt.normalize()
    #
    # line_chart_invoice_data = invoices.groupby('Invoice_date').Invoice_ID.nunique()
    # line_chart_order_data = orders.groupby('Order_date').Order_ID.nunique()
    #
    # st.subheader('Sales and Orders evolution through time', divider='grey')
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=line_chart_invoice_data.index, y=invoices['Total_price'].values,
    #                          name='Invoices'))
    # fig.add_trace(go.Scatter(x=line_chart_order_data.index, y=orders['Total_price'].values,
    #                          name='Orders'))
    # st.plotly_chart(fig, use_container_width=True)

    ################################
    line_chart_invoices = pd.read_csv(f"./data/{directory}/invoices.csv")
    line_chart_orders = pd.read_csv(f"./data/{directory}/orders.csv")

    line_chart_invoices['Invoice_date'] = pd.to_datetime(line_chart_invoices['Invoice_date']).dt.normalize()
    line_chart_orders['Order_date'] = pd.to_datetime(line_chart_orders['Order_date']).dt.normalize()

    line_chart_invoice_data = line_chart_invoices.groupby('Invoice_date').Invoice_ID.nunique()
    line_chart_order_data = line_chart_orders.groupby('Order_date').Order_ID.nunique()
    min_date = min(line_chart_invoice_data.index.min(), line_chart_order_data.index.min())
    max_date = max(line_chart_invoice_data.index.max(), line_chart_order_data.index.max())
    st.subheader(f"Sales and Orders evolution through time for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]", divider='grey')


    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=line_chart_invoices['Invoice_date'], y=line_chart_invoices['Total_price'].values,
                              name='Invoices'))
    fig2.add_trace(go.Scatter(x=line_chart_orders['Order_date'], y=line_chart_orders['Total_price'].values,
                              name='Orders'))
    #
    fig2.add_shape(type='rect',
                   x0=snapshot_start_date,
                   x1=snapshot_end_date,
                   y0=line_chart_orders['Total_price'].min(),
                   y1=line_chart_orders['Total_price'].max(),
                   fillcolor="lightblue",
                   opacity=0.5,
                   layer="below",
                   line_width=0)
    fig2.update_xaxes(range=[min_date, max_date])

    st.plotly_chart(fig2, use_container_width=True)

    #####################################

    st.subheader(f"Customer type distribution for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]", divider='grey')
    fig = px.histogram(customers, x='Customer_type')
    st.plotly_chart(fig, use_container_width=True)

    invoices_reset = invoices.reset_index(drop=True)
    orders_reset = orders.reset_index(drop=True)

    st.subheader(f"Minimum/Maximum invoices and orders value for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]", divider='grey')

    fig = make_subplots(rows=1, cols=1)

    fig.add_trace(go.Box(x=invoices_reset['Total_price'], pointpos=0, name='Invoices'))
    fig.add_trace(go.Box(x=orders_reset['Total_price'], pointpos=0, name='Orders'))

    fig.update_layout(showlegend=True)

    st.plotly_chart(fig, use_container_width=True)

    return
