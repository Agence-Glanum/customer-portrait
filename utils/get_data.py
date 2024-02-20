import datetime
import pandas as pd


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


def transform_data(directory):
    (address, categories, customer, invoices, invoices_lines, orders,
     orders_lines, products) = get_data_from_csv(directory)

    invoices['Invoice_date'] = pd.to_datetime(invoices['Invoice_date'])
    orders['Order_date'] = pd.to_datetime(orders['Order_date'])

    return address, categories, customer, invoices, invoices_lines, orders, orders_lines, products


def get_dates(directory):
    address, categories, customer, invoices, invoices_lines, orders, orders_lines, products = transform_data(directory)

    DATE_MIN = min(invoices['Invoice_date'].min(), orders['Order_date'].min())
    DATE_MAX = max(invoices['Invoice_date'].max(), orders['Order_date'].max())

    return DATE_MIN, DATE_MAX


def filter_data(client_type, sales_filter, snapshot_start_date, snapshot_end_date, directory):
    addresses, categories, customers, invoices, invoices_lines, orders, orders_lines, products = transform_data(directory)

    start_date = datetime.datetime(snapshot_start_date.year, snapshot_start_date.month, snapshot_start_date.day)
    end_date = datetime.datetime(snapshot_end_date.year, snapshot_end_date.month, snapshot_end_date.day)

    invoices = invoices[(invoices['Invoice_date'] >= start_date) & (invoices['Invoice_date'] <= end_date)]
    orders = orders[(orders['Order_date'] >= start_date) & (orders['Order_date'] <= end_date)]

    invoices_lines = invoices_lines[invoices_lines['Invoice_ID'].isin(invoices['Invoice_ID'])]
    orders_lines = orders_lines[orders_lines['Order_ID'].isin(orders['Order_ID'])]

    if sales_filter == 'Invoice':
        products = products[products['Product_ID'].isin(invoices_lines['Product_ID'])]
        categories = categories[categories['Category_ID'].isin(products['Category_ID'])]

        customers = customers[(customers['Customer_type'] == client_type)
                              & (customers['Customer_ID'].isin(invoices['Customer_ID']))]
        addresses = addresses[addresses['Customer_ID'].isin(customers['Customer_ID'])]

    else:
        products = products[products['Product_ID'].isin(orders_lines['Product_ID'])]
        categories = categories[categories['Category_ID'].isin(products['Category_ID'])]

        customers = customers[(customers['Customer_type'] == client_type)
                              & (customers['Customer_ID'].isin(orders['Customer_ID']))]
        addresses = addresses[addresses['Customer_ID'].isin(customers['Customer_ID'])]

    return addresses, categories, customers, invoices, invoices_lines, orders, orders_lines, products
