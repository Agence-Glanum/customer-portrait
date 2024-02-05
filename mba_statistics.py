import streamlit as st
import plotly.express as px


def show_eda(invoices, invoices_lines, products, categories, transformed_sales_filter):
    st.subheader('Basket Size')
    df = invoices.merge(invoices_lines, on=transformed_sales_filter + '_ID')
    new_df = df.groupby(transformed_sales_filter + '_ID').agg(
        {'Product_ID': lambda x: len(x)}).reset_index().sort_values(['Product_ID'])
    st.write(px.box(new_df, x="Product_ID").update_layout(xaxis_title='Number of items'))

    st.subheader('10 trending Products')
    bar_data = invoices_lines.groupby('Product_ID')['Quantity'].sum().reset_index().merge(products, on='Product_ID').groupby('Product_name')['Quantity'].sum().reset_index()[['Product_name', 'Quantity']]
    bar_data.sort_values('Quantity', ascending=False, inplace=True)
    st.write(px.bar(bar_data.head(10), x='Quantity', y='Product_name', orientation='h'))

    st.subheader('10 trending Product\'s Categories')
    bar_data = invoices_lines.groupby('Product_ID')['Quantity'].sum().reset_index().merge(
        products, on='Product_ID').merge(categories, on='Category_ID').groupby(
        'Category_name')['Quantity'].sum().reset_index()[['Category_name', 'Quantity']]
    bar_data.sort_values('Quantity', ascending=False, inplace=True)
    st.write(px.bar(bar_data.head(10), x='Quantity', y='Category_name', orientation='h'))

    return


def mba_statistics_main_function(invoices, invoices_lines, products, categories, directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter):
    st.header(f'General statistics for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]')
    show_eda(invoices, invoices_lines, products, categories, transformed_sales_filter)
