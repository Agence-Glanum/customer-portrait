import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show_boxplot(invoices, orders):
    fig = make_subplots(rows=1, cols=1)

    fig.add_trace(go.Box(x=invoices['Total_price'], name='Invoices'))
    fig.add_trace(go.Box(x=orders['Total_price'], name='Orders'))
    fig.update_layout(xaxis_title='Monetary value')
    fig.update_layout(showlegend=True)

    st.plotly_chart(fig, use_container_width=True)

    return


def show_timelines(invoices, orders, snapshot_start_date, snapshot_end_date):
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

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=paid_invoices['Invoice_date'], y=paid_invoices['Total_price'], name='Paid Invoices',
                              line=dict(color='blue')))
    fig2.add_trace(
        go.Scatter(x=unpaid_invoices['Invoice_date'], y=unpaid_invoices['Total_price'], name='Unpaid Invoices',
                   line=dict(color='purple')))

    fig2.add_trace(go.Scatter(x=valid_orders['Order_date'], y=valid_orders['Total_price'], name='Valid Orders',
                              line=dict(color='green')))
    fig2.add_trace(go.Scatter(x=draft_orders['Order_date'], y=draft_orders['Total_price'], name='Draft Orders',
                              line=dict(color='yellow')))
    fig2.add_trace(
        go.Scatter(x=cancelled_orders['Order_date'], y=cancelled_orders['Total_price'], name='Cancelled Orders',
                   line=dict(color='grey')))

    traces_to_hide = ['Draft Orders', 'Cancelled Orders']
    fig2.for_each_trace(lambda trace: trace.update(visible='legendonly') if trace.name in traces_to_hide else ())

    fig2.update_layout(xaxis_title='Date', yaxis_title='Monetary value')

    fig2.add_shape(type='rect',
                   x0=snapshot_start_date,
                   x1=snapshot_end_date,
                   y0=min_value,
                   y1=max_value,
                   fillcolor='lightblue',
                   opacity=0.5,
                   layer='below',
                   line_width=0)
    fig2.update_xaxes(range=[min_date, max_date])

    st.plotly_chart(fig2, use_container_width=True)
    return
