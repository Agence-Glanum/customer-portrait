import datetime
import pandas as pd


def get_data_from_csv(directory):
    path = './data/Glanum/' if directory == 'Glanum' else './data/IciStore/'
    csv_files = ['Addresses', 'Categories', 'Customers', 'Invoices', 'Invoice_lines', 'Orders', 'Order_lines',
                 'Products']
    return tuple(pd.read_csv(f'{path}/{file}.csv') for file in csv_files)


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


def filter_data(client_type, snapshot_start_date, snapshot_end_date, directory):
    (addresses, categories, customers, invoices, invoices_lines, orders,
     orders_lines, products) = transform_data(directory)

    customers = customers[customers['Customer_type'] == client_type]
    addresses = addresses[addresses['Customer_ID'].isin(customers['Customer_ID'])]
    invoices = invoices[invoices['Customer_ID'].isin(customers['Customer_ID'])]
    orders = orders[orders['Customer_ID'].isin(customers['Customer_ID'])]

    start_date = datetime.datetime(snapshot_start_date.year, snapshot_start_date.month, snapshot_start_date.day)
    end_date = datetime.datetime(snapshot_end_date.year, snapshot_end_date.month, snapshot_end_date.day)

    invoices = invoices[invoices['Invoice_date'].between(start_date, end_date)]
    orders = orders[orders['Order_date'].between(start_date, end_date)]

    return addresses, categories, customers, invoices, invoices_lines, orders, orders_lines, products
