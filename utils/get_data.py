# import os
import datetime
import pandas as pd
# import sqlalchemy as db

# DB_USERNAME = os.getenv("DB_USERNAME")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_HOST = os.getenv("DB_HOST")
# DB_NAME = os.getenv("DB_NAME")
#
# connection_string = f"mssql+pyodbc://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/
# {DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"
#
# engine = db.create_engine(connection_string)
#
#
# def get_data_from_db(query):
#     return pd.read_sql_query(query, engine)


def get_data_from_csv(directory):
    path = './data/Glanum/' if directory == 'Glanum' else './data/IciStore/'
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


def filter_data(snapshot_start_date, snapshot_end_date, directory):
    address, categories, customer, invoices, invoices_lines, orders, orders_lines, products = transform_data(directory)

    start_date = datetime.datetime(snapshot_start_date.year, snapshot_start_date.month, snapshot_start_date.day)
    end_date = datetime.datetime(snapshot_end_date.year, snapshot_end_date.month, snapshot_end_date.day)

    invoices = invoices[(invoices['Invoice_date'] >= start_date) & (invoices['Invoice_date'] <= end_date)]
    orders = orders[(orders['Order_date'] >= start_date) & (orders['Order_date'] <= end_date)]

    return address, categories, customer, invoices, invoices_lines, orders, orders_lines, products
