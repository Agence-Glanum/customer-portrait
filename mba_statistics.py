import streamlit as st
import plotly.express as px


def show_eda(df_sales, df_lines, products, categories, sales_filter):
    st.subheader('Basket Size')
    df = df_sales.merge(df_lines, on=sales_filter + '_ID')
    new_df = df.groupby(sales_filter + '_ID').agg(
        {'Product_ID': lambda x: len(x)}).reset_index().sort_values(['Product_ID'])
    st.write(px.box(new_df, x="Product_ID").update_layout(xaxis_title='Number of items'))

    st.subheader('10 Top Products')
    bar_data = df_lines.groupby('Product_ID')['Quantity'].sum().reset_index().merge(products, on='Product_ID').groupby(
        'Product_name')['Quantity'].sum().reset_index()[['Product_name', 'Quantity']]
    bar_data.sort_values('Quantity', ascending=True, inplace=True)
    st.write(px.bar(bar_data.tail(10), x='Quantity', y='Product_name', orientation='h'))

    bar_value_data = df_lines.groupby('Product_ID')['Total_price'].sum().reset_index().merge(products, on='Product_ID').groupby(
        'Product_name')['Total_price'].sum().reset_index()[['Product_name', 'Total_price']]
    bar_value_data.sort_values('Total_price', ascending=True, inplace=True)
    st.write(px.bar(bar_value_data.tail(10), x='Total_price', y='Product_name', orientation='h'))

    st.subheader('10 Flop Products')
    st.write(px.bar(bar_data.head(10), x='Quantity', y='Product_name', orientation='h'))
    st.write(px.bar(bar_value_data.head(10), x='Total_price', y='Product_name', orientation='h'))

    st.subheader('Product\'s Categories ranking')
    bar_data = df_lines.groupby('Product_ID')['Quantity'].sum().reset_index().merge(
        products, on='Product_ID').merge(categories, on='Category_ID').groupby(
        'Category_name')['Quantity'].sum().reset_index()[['Category_name', 'Quantity']]
    bar_data.sort_values('Quantity', ascending=True, inplace=True)
    bar_value_data = df_lines.groupby('Product_ID')['Total_price'].sum().reset_index().merge(
        products, on='Product_ID').merge(categories, on='Category_ID').groupby(
        'Category_name')['Total_price'].sum().reset_index()[['Category_name', 'Total_price']]
    bar_value_data.sort_values('Total_price', ascending=True, inplace=True)

    st.write(px.bar(bar_data.tail(10), x='Quantity', y='Category_name', orientation='h'))
    st.write(px.bar(bar_value_data.tail(10), x='Total_price', y='Category_name', orientation='h'))

    return


def mba_statistics_main_function(df_sales, df_lines, products, categories, snapshot_start_date,
                                 snapshot_end_date, directory, sales_filter, customer_type):
    st.header(f'MBA KPIs', divider='grey')
    st.info(f'Company: :blue[{directory}]' +
            f'\n\nData type: :blue[{sales_filter}]' +
            f'\n\nCustomer type: :blue[{customer_type}]' +
            f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
    show_eda(df_sales, df_lines, products, categories, sales_filter)
