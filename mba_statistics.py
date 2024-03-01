import streamlit as st
import plotly.express as px


@st.cache_data
def show_eda(df_sales, df_lines, products, categories, sales_filter):
    df = df_sales.merge(df_lines, on=sales_filter + '_ID')
    new_df = df.groupby(sales_filter + '_ID').agg(
        {'Product_ID': lambda x: len(x)}).reset_index().sort_values(['Product_ID'])
    fig = px.box(new_df, x="Product_ID").update_layout(xaxis_title='Number of items', title='Basket Size')
    st.write(fig)

    quantity_data = df_lines.groupby('Product_ID')['Quantity'].sum().reset_index().merge(products, on='Product_ID').groupby(
        'Product_name')['Quantity'].sum().reset_index()[['Product_name', 'Quantity']]
    quantity_data.sort_values('Quantity', ascending=False, inplace=True)
    price_data = df_lines.groupby('Product_ID')['Total_price'].sum().reset_index().merge(products, on='Product_ID').groupby(
        'Product_name')['Total_price'].sum().reset_index()[['Product_name', 'Total_price']]
    price_data.sort_values('Total_price', ascending=False, inplace=True)

    fig = px.bar(quantity_data.head(10), x='Quantity', y='Product_name',
                 orientation='h').update_layout(title='10 Top Products by Quantity',
                                                xaxis_title='Quantity', yaxis_title='Products')
    st.write(fig)
    fig = px.bar(price_data.head(10), x='Total_price', y='Product_name',
                 orientation='h').update_layout(title='10 Top Products by Price',
                                                xaxis_title='Price', yaxis_title='Products')
    st.write(fig)

    fig = px.bar(quantity_data.tail(10), x='Quantity', y='Product_name',
                 orientation='h').update_layout(title='10 Flop Products by Quantity',
                                                xaxis_title='Quantity', yaxis_title='Products')
    st.write(fig)
    fig = px.bar(price_data.tail(10), x='Total_price', y='Product_name',
                 orientation='h').update_layout(title='10 Flop Products by Price',
                                                xaxis_title='Price', yaxis_title='Products')
    st.write(fig)

    quantity_data = df_lines.groupby('Product_ID')['Quantity'].sum().reset_index().merge(
        products, on='Product_ID').merge(categories, on='Category_ID').groupby(
        'Category_name')['Quantity'].sum().reset_index()[['Category_name', 'Quantity']]
    quantity_data.sort_values('Quantity', ascending=False, inplace=True)
    price_data = df_lines.groupby('Product_ID')['Total_price'].sum().reset_index().merge(
        products, on='Product_ID').merge(categories, on='Category_ID').groupby(
        'Category_name')['Total_price'].sum().reset_index()[['Category_name', 'Total_price']]
    price_data.sort_values('Total_price', ascending=False, inplace=True)

    fig = px.bar(quantity_data.head(10), x='Quantity', y='Category_name',
                 orientation='h').update_layout(title='10 Top Categories by Quantity',
                                                xaxis_title='Quantity', yaxis_title='Products')
    st.write(fig)
    fig = px.bar(price_data.head(10), x='Total_price', y='Category_name',
                 orientation='h').update_layout(title='10 Top Categories by Price',
                                                xaxis_title='Price', yaxis_title='Categories')
    st.write(fig)

    fig = px.bar(quantity_data.tail(10), x='Quantity', y='Category_name',
                 orientation='h').update_layout(title='10 Flop Categories by Quantity',
                                                xaxis_title='Quantity', yaxis_title='Products')
    st.write(fig)
    fig = px.bar(price_data.tail(10), x='Total_price', y='Category_name',
                 orientation='h').update_layout(title='10 Flop Categories by Price',
                                                xaxis_title='Price', yaxis_title='Categories')
    st.write(fig)

    return


def mba_statistics_main_function(df_sales, df_lines, products, categories, snapshot_start_date,
                                 snapshot_end_date, directory, sales_filter, customer_type):
    st.header(f'MBA KPIs', divider='grey')
    st.info(f'Company: :blue[{directory}]' +
            f'\n\nData type: :blue[{sales_filter}]' +
            f'\n\nCustomer type: :blue[{customer_type}]' +
            f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
    show_eda(df_sales, df_lines, products, categories, sales_filter)
