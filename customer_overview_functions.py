import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd


def get_info(rfm, customer_id, scaler, kmeans):
    col_names = ['Recency', 'Frequency', 'Monetary']
    features = rfm[rfm['Customer_ID'] == customer_id][col_names]
    scaled_features = scaler.transform(features.values)
    customer_cluster = kmeans.predict(scaled_features)

    customer_segment_1 = rfm[rfm['Customer_ID'] == customer_id]['Segment 1']
    customer_segment_2 = rfm[rfm['Customer_ID'] == customer_id]['Segment 2']

    return customer_cluster, customer_segment_1, customer_segment_2


def compute_lifetime_value(df, df_lines):
    df_final = df.merge(df_lines, left_on='Invoice_ID', right_on='Invoice_ID')

    cltv_df = df_final.groupby("Customer_ID").agg(
        {
            "Invoice_date": lambda x: (x.max() - x.min()).days,
            "Invoice_ID": lambda x: len(x),
            "Quantity": lambda x: x.sum(),
            "Total_price_y": lambda x: x.sum(),
        }
    )
    cltv_df.columns = ["Age", "Num_transactions", "Quantity", "Total_revenue"]
    cltv_df = cltv_df[cltv_df["Quantity"] > 0]

    cltv_df['AOV'] = cltv_df['Total_revenue'] / cltv_df['Num_transactions']
    purchase_freq = sum(cltv_df['Num_transactions']) / len(cltv_df)
    repeat_rate = cltv_df[cltv_df['Num_transactions'] > 1].shape[0] / cltv_df.shape[0]
    churn_rate = 1 - repeat_rate
    cltv_df['profit_margin'] = cltv_df['Total_revenue'] * .10  # to change
    cltv_df['CLTV'] = ((cltv_df['AOV'] * purchase_freq) / churn_rate) * .10

    return cltv_df


def customer_overview_main_function(rfm, scaler, kmeans, average_clusters, invoices, invoices_lines, customers, orders,
                                    directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter, address):

    cltv_df = compute_lifetime_value(invoices, invoices_lines)
    customer_id = st.selectbox('Customers', (rfm['Customer_ID'].astype(str) + ' - ' + rfm['Customer_name']))
    customer_id = int(customer_id.split(' - ')[0])

    customer_zip = address[address['Customer_ID'] == customer_id]
    print(customer_zip)
    customer_zip["Zip_code"] = customer_zip["Zip_code"].str[:2]
    geojson_path = './data/contour-des-departements.geojson'
    geojson_world = './data/world.json'
    gdf_departements = gpd.read_file(geojson_path)
    customer_zip["Zip_code"] = customer_zip["Zip_code"].astype(str)
    gdf_occurrences = gdf_departements.merge(customer_zip["Zip_code"], how='left', left_on='code', right_on='Zip_code')
    gdf_occurrences['Zip_code'] = gdf_occurrences['Zip_code'].fillna(0)
    fig2 = px.choropleth_mapbox(customer_zip, geojson=gdf_departements, locations='Zip_code', color='Zip_code',
                                width=1000,
                                height=400,
                                color_continuous_scale="Viridis",
                                range_color=(0, 12),
                                mapbox_style="carto-positron",
                                zoom=3.5, center={"lat": 46.6031, "lon": 1.8883},
                                opacity=0.8,
                                )
    fig2.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    col1, col2, col3 = st.columns(3)

    customer_cluster, customer_segment_1, customer_segment_2 = get_info(rfm, customer_id, scaler, kmeans)

    col1.metric('Customer cluster using ML', 'Cluster ' + str(customer_cluster[0]))
    fig = px.line_polar(r=[average_clusters['Recency'][customer_cluster[0]],
                           average_clusters['Frequency'][customer_cluster[0]],
                           average_clusters['Monetary'][customer_cluster[0]]],
                        theta=['Recency', 'Frequency', 'Monetary'], line_close=True, width=300, height=300)

    col1.write(fig)
    col2.write('Customer segment using RFM score')
    col2.metric('First approach', str(customer_segment_1.iloc[0]))
    col2.metric('Second approach', str(customer_segment_2.iloc[0]))
    col3.metric("Lifetime value", round(cltv_df[cltv_df.index == customer_id]['CLTV'], 2))
    col3.metric("Median CLTV", round(cltv_df['CLTV'].median(), 2))
    col3.metric("Average CLTV", round(cltv_df['CLTV'].mean(), 2))

    st.write(fig2)
    filtered_invoices = invoices[invoices['Customer_ID'] == customer_id].copy()
    filtered_orders = orders[orders['Customer_ID'] == customer_id].copy()

    filtered_invoices['Invoice_date'] = pd.to_datetime(filtered_invoices['Invoice_date']).dt.normalize()
    filtered_orders['Order_date'] = pd.to_datetime(filtered_orders['Order_date']).dt.normalize()
    layout = go.Layout(
        width=400,
        height=400,
    )

    line_chart_invoice_data = filtered_invoices.groupby(['Invoice_date', 'Total_price']).size().reset_index(
        name='count')
    line_chart_order_data = filtered_orders.groupby(['Order_date', 'Total_price']).size().reset_index(name='count')

    st.subheader(
        f'Sales and Orders evolution through time for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]',
        divider='grey')
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=line_chart_invoice_data['Invoice_date'].explode(),
                   y=line_chart_invoice_data['Total_price'].explode(),
                   name='Invoices'))
    fig.add_trace(
        go.Scatter(x=line_chart_order_data['Order_date'].explode(), y=line_chart_order_data['Total_price'].explode(),
                   name='Orders'))
    st.plotly_chart(fig, use_container_width=True)

    return


def merge_cltv_rfm(cltv_df, rfm):
    return pd.merge(cltv_df, rfm[['Customer_ID', 'Segment 1', 'Segment 2', 'Customer_name']],
                    left_on='Customer_ID', right_on='Customer_ID', how='inner')


def customer_overview_data_function(rfm, invoices, invoices_lines, show_full_dataframe=False):
    cltv_df = compute_lifetime_value(invoices, invoices_lines)

    merged_df = merge_cltv_rfm(cltv_df, rfm)

    if show_full_dataframe:
        st.dataframe(merged_df, use_container_width=True, )
    else:
        customer_id = st.selectbox('Customer', (
                    (merged_df['Customer_ID'].astype(int)).astype(str) + ' - ' + merged_df['Customer_name']))
        customer_id = int(customer_id.split(' - ')[0])
        st.dataframe(merged_df[merged_df['Customer_ID'] == customer_id], use_container_width=True)

    return
