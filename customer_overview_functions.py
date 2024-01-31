import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


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
    cltv_df['profit_margin'] = cltv_df['Total_revenue']*.10 # to change
    cltv_df['CLTV'] = ((cltv_df['AOV']*purchase_freq)/churn_rate)*.10

    return cltv_df


def customer_overview_main_function(rfm, scaler, kmeans, average_clusters, df_sales, df_lines, directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter):
    cltv_df = compute_lifetime_value(df_sales, df_lines)
    customer_id = st.selectbox('Customers', (rfm['Customer_ID'].astype(str) + ' - ' + rfm['Customer_name']))
    customer_id = int(customer_id.split(' - ')[0])

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

    # filtered_df = df_sales[df_sales['Customer_ID'] == customer_id].copy()
    #
    # filtered_df[transformed_sales_filter + '_date'] = pd.to_datetime(filtered_df[transformed_sales_filter + '_date']).dt.normalize()
    #
    # line_chart_data = filtered_df.groupby([transformed_sales_filter + '_date', 'Total_price']).size().reset_index(name='count')
    #
    # st.subheader(
    #     f'Sales and Orders evolution through time for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]',
    #     divider='grey')
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=line_chart_data[transformed_sales_filter + '_date'].explode(),
    #                          y=line_chart_data['Total_price'].explode()))
    # st.plotly_chart(fig, use_container_width=True)

    return


def customer_overview_data_function(rfm, df_sales, df_lines):
    cltv_df = compute_lifetime_value(df_sales, df_lines)

    merged_df = pd.merge(cltv_df, rfm[['Customer_ID', 'Segment 1', 'Segment 2', 'Customer_name']],
                         left_on='Customer_ID', right_on='Customer_ID', how='inner')

    customer_id = st.selectbox('', ((merged_df['Customer_ID'].astype(int)).astype(str) + ' - ' + merged_df['Customer_name']))
    customer_id = int(customer_id.split(' - ')[0])
    st.dataframe(merged_df[merged_df['Customer_ID'] == customer_id], use_container_width=True)
    return


def customers_overview_data_function(rfm, df_sales, df_lines):
    cltv_df = compute_lifetime_value(df_sales, df_lines)

    merged_df = pd.merge(cltv_df, rfm[['Customer_ID', 'Segment 1', 'Segment 2', 'Customer_name']],
                         left_on='Customer_ID', right_on='Customer_ID', how='inner')

    st.dataframe(merged_df, use_container_width=True)
    return
