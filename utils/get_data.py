import datetime
import pandas as pd
import streamlit as st


@st.cache_data
def get_data_from_csv(directory):
    path = './data/' + directory
    address = pd.read_csv(f'{path}/Addresses.csv')
    categories = pd.read_csv(f'{path}/Categories.csv')
    customer = pd.read_csv(f'{path}/Customers.csv')
    invoices = pd.read_csv(f'{path}/Invoices.csv')
    invoices_lines = pd.read_csv(f'{path}/Invoice_lines.csv')
    orders = pd.read_csv(f'{path}/Orders.csv')
    orders_lines = pd.read_csv(f'{path}/Order_lines.csv')
    products = pd.read_csv(f'{path}/Products.csv')
    return address, categories, customer, invoices, invoices_lines, orders, orders_lines, products


@st.cache_data
def transform_data(directory):
    address, categories, customer, invoices, invoices_lines, orders, orders_lines, products = get_data_from_csv(
        directory)

    invoices['Invoice_date'] = pd.to_datetime(invoices['Invoice_date'])
    orders['Order_date'] = pd.to_datetime(orders['Order_date'])

    return address, categories, customer, invoices, invoices_lines, orders, orders_lines, products


@st.cache_data
def get_dates(directory):
    address, categories, customer, invoices, invoices_lines, orders, orders_lines, products = transform_data(directory)

    DATE_MIN = min(invoices['Invoice_date'].min(), orders['Order_date'].min())
    DATE_MAX = max(invoices['Invoice_date'].max(), orders['Order_date'].max())

    return DATE_MIN, DATE_MAX


@st.cache_data
def filter_data(client_type, sales_filter, snapshot_start_date, snapshot_end_date, directory, date_flag, client_flag):
    addresses, categories, customers, invoices, invoices_lines, orders, orders_lines, products = transform_data(
        directory)

    # Get Customers based on the filter
    if client_flag:
        customers = customers[(customers['Customer_type'] == client_type)]

    # Get Invoices and Orders within the Date Range
    start_date = datetime.datetime(snapshot_start_date.year, snapshot_start_date.month, snapshot_start_date.day)
    end_date = datetime.datetime(snapshot_end_date.year, snapshot_end_date.month, snapshot_end_date.day)

    if date_flag:
        invoices = invoices[(invoices['Invoice_date'] >= start_date) &
                            (invoices['Invoice_date'] <= end_date) &
                            (invoices['Customer_ID'].isin(customers['Customer_ID']))]
        orders = orders[(orders['Order_date'] >= start_date) &
                        (orders['Order_date'] <= end_date) &
                        (orders['Customer_ID'].isin(customers['Customer_ID']))]
    else:
        invoices = invoices[(invoices['Customer_ID'].isin(customers['Customer_ID']))]
        orders = orders[(orders['Customer_ID'].isin(customers['Customer_ID']))]

    # Get All Data based on filters
    if sales_filter == 'Invoice':
        customers = customers[customers['Customer_ID'].isin(invoices['Customer_ID'])]
        products = products[products['Product_ID'].isin(invoices_lines['Product_ID'])]
    else:
        customers = customers[customers['Customer_ID'].isin(orders['Customer_ID'])]
        products = products[products['Product_ID'].isin(orders_lines['Product_ID'])]

    invoices_lines = invoices_lines[invoices_lines['Invoice_ID'].isin(invoices['Invoice_ID'])]
    orders_lines = orders_lines[orders_lines['Order_ID'].isin(orders['Order_ID'])]
    categories = categories[categories['Category_ID'].isin(products['Category_ID'])]
    addresses = addresses[addresses['Customer_ID'].isin(customers['Customer_ID'])]

    addresses.dropna(subset=['Address_type'], inplace=True)
    addresses.loc[:, 'Address_1':] = addresses.loc[:, 'Address_1':].apply(lambda x: x.astype(str).str.upper())
    addresses = addresses.drop_duplicates(
        subset=['Customer_ID', 'Address_1', 'Address_2', 'Zip_code', 'City', 'Country', 'Address_type'])

    invoice_addresses = pd.merge(invoices[['Invoice_address_ID', 'Invoice_date']],
                                 addresses[addresses['Address_type'] == 'INVOICE'],
                                 left_on='Invoice_address_ID',
                                 right_on='Address_ID', how='right')
    invoice_addresses['Rank'] = invoice_addresses.groupby('Customer_ID')['Invoice_date'].transform(
        lambda x: x.rank(method='first', ascending=False))
    invoice_addresses = invoice_addresses[invoice_addresses['Rank'] == 1].drop(columns=['Rank'])

    other_addresses = addresses[addresses['Address_type'] != 'INVOICE']

    addresses = pd.concat([invoice_addresses, other_addresses])
    addresses.drop(['Invoice_address_ID', 'Invoice_date'], axis=1)

    return addresses, categories, customers, invoices, invoices_lines, orders, orders_lines, products
