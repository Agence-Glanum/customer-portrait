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

    st.write('Total of categories : ', categories['Category_ID'].nunique())
    st.write('In the catalog :')
    st.write('We have ', products['Product_ID'].nunique(), ' products which makes it ', len(products['Category_ID'].value_counts()), 'categories.')
    st.write('Sales : ')
    st.write('We have ', invoices_lines['Product_ID'].nunique(), ' products which makes it ',
             invoices_lines.merge(products, on='Product_ID')['Category_ID'].nunique(), 'categories.')


    # Code for products with a list of Category_ID
    # products['Category_ID'] = [x.replace('[', '').replace(']', '').split(',') for x in products['Category_ID']]
    # products = products.explode('Category_ID')
    # column_type = categories['Category_ID'].dtypes
    # products['Category_ID'] = products['Category_ID'].astype(column_type)
    # df = products.merge(categories, left_on='Category_ID', right_on='Category_ID')
    # a = df['Parent_ID'].value_counts().rename_axis('Category_ID').reset_index(name='counts').sort_values('Category_ID')
    # b = categories[categories['Category_ID'].isin(a['Category_ID'])][['Category_ID', 'Category_name']]
    # bar_data = a.merge(b, on='Category_ID').sort_values('counts')
    # st.write(px.bar(bar_data, x='counts', y='Category_name', orientation='h'))

    return


def mba_statistics_main_function(invoices, invoices_lines, products, categories, directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter):
    st.header(f'General statistics for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]')
    show_eda(invoices, invoices_lines, products, categories, transformed_sales_filter)
