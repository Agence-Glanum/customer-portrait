import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


@st.cache_data
def show_plots(invoices, orders):
    data = {
        'Orders': orders['Order_ID'].nunique(),
        'Invoices': invoices['Invoice_ID'].nunique()
    }
    fig_1 = px.bar(x=list(data.keys()), y=list(data.values()),
                   title='Proportion of Invoices and Orders')
    fig_1.update_layout(xaxis_title='Sales', yaxis_title='Count')
    st.write(fig_1)

    fig_2 = make_subplots(rows=1, cols=1)
    fig_2.add_trace(go.Box(x=invoices['Total_price'], name='Invoices'))
    fig_2.add_trace(go.Box(x=orders['Total_price'], name='Orders'))
    fig_2.update_layout(title='Order vs. Invoice: Monetary Comparison', xaxis_title='Monetary value', showlegend=True)
    st.write(fig_2)

    data = orders['Status'].value_counts()
    fig_3 = px.bar(data, y=data.values, x=data.index,
                   title='Proportion of Orders status')
    fig_3.update_layout(yaxis_title='Count')
    st.write(fig_3)

    invoices['Paid'] = invoices['Paid'].replace({0: 'Unpaid', 1: 'Paid'})
    data = invoices['Paid'].value_counts()
    fig_4 = px.pie(data, values=data.values, names=data.index,
                   title='Proportion of Paid Invoices')
    st.write(fig_4)

    data = invoices['Invoice_type'].value_counts()
    fig_5 = px.pie(data, values=data.values, names=data.index,
                   title='Proportion of Invoice types')
    st.write(fig_5)

    return fig_1, fig_2, fig_3, fig_4, fig_5


@st.cache_data
def show_timelines(directory, snapshot_start_date, snapshot_end_date, customer_id=None):
    path = './data/' + directory
    invoices = pd.read_csv(f'{path}/Invoices.csv')
    orders = pd.read_csv(f'{path}/Orders.csv')

    if customer_id:
        invoices = invoices[(invoices['Customer_ID'] == customer_id)]
        orders = orders[(orders['Customer_ID'] == customer_id)]

    invoices['Invoice_date'] = pd.to_datetime(invoices['Invoice_date']).dt.normalize()
    orders['Order_date'] = pd.to_datetime(orders['Order_date']).dt.normalize()

    min_date = min(invoices['Invoice_date'].min(), orders['Order_date'].min())
    max_date = max(invoices['Invoice_date'].max(), orders['Order_date'].max())

    min_value = min(invoices['Total_price'].min(), orders['Total_price'].min())
    max_value = max(invoices['Total_price'].max(), orders['Total_price'].max())

    paid_invoices = invoices[(invoices['Paid'] == 1)]
    unpaid_invoices = invoices[(invoices['Paid'] == 0)]
    valid_orders = orders[(orders['Status'] != 'draft') & (orders['Status'] != 'cancelled')]
    draft_orders = orders[(orders['Status'] == 'draft')]
    cancelled_orders = orders[(orders['Status'] == 'cancelled')]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=paid_invoices['Invoice_date'], y=paid_invoices['Total_price'], name='Paid Invoices',
                             line=dict(color='blue')))
    fig.add_trace(
        go.Scatter(x=unpaid_invoices['Invoice_date'], y=unpaid_invoices['Total_price'], name='Unpaid Invoices',
                   line=dict(color='purple')))

    fig.add_trace(go.Scatter(x=valid_orders['Order_date'], y=valid_orders['Total_price'], name='Valid Orders',
                             line=dict(color='green')))
    fig.add_trace(go.Scatter(x=draft_orders['Order_date'], y=draft_orders['Total_price'], name='Draft Orders',
                             line=dict(color='yellow')))
    fig.add_trace(
        go.Scatter(x=cancelled_orders['Order_date'], y=cancelled_orders['Total_price'], name='Cancelled Orders',
                   line=dict(color='grey')))

    traces_to_hide = ['Draft Orders', 'Cancelled Orders']
    fig.for_each_trace(lambda trace: trace.update(visible='legendonly') if trace.name in traces_to_hide else ())

    fig.update_layout(title='Timeline of Sales and Orders', xaxis_title='Date', yaxis_title='Monetary value')

    fig.add_shape(type='rect',
                  x0=snapshot_start_date,
                  x1=snapshot_end_date,
                  y0=min_value,
                  y1=max_value,
                  fillcolor='lightblue',
                  opacity=0.5,
                  layer='below',
                  line_width=0)
    fig.update_xaxes(range=[min_date, max_date])

    st.plotly_chart(fig, use_container_width=True)
    return fig
