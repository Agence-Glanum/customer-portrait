import pandas as pd
import streamlit as st
from mba_statistics import mba_statistics_main_function
from most_frequent_pattern import most_frequent_pattern_main_function
from next_product_prediction import next_prod_pred_main_function, get_all_recommendations
from product_affinity_functions import prod_aff_main_function


@st.cache_data
def show_mba(product_clusters, category_clusters, apriori_rules_products, apriori_rules_categories,
             recommendations_ubcf, recommendations_ubcfc, recommendations_ibcf, recommendations_ibcfc):
    st.info('The product and category clusters are not the same !')

    def format_proportion(row, mode):
        formatted_values = [f"{item} ({proportion})" for item, proportion in
                            zip(row[mode], row['proportion'])]
        return ', '.join(formatted_values)

    product_melted_df = pd.melt(product_clusters.reset_index(), id_vars=['Customer_ID', 'Cluster MBA'],
                                var_name='product', value_name='spending')
    product_melted_df = product_melted_df[product_melted_df['spending'] > 0]
    cluster_total_spending = product_melted_df.groupby('Cluster MBA')['spending'].transform('sum')
    product_melted_df['proportion'] = product_melted_df['spending'] / cluster_total_spending
    product_grouped_df = product_melted_df.groupby(['Cluster MBA', 'product'])['proportion'].sum()
    product_grouped_df = product_grouped_df.reset_index()
    product_grouped_df['proportion'] = product_grouped_df['proportion'].map(lambda x: f"{x:.2%}")
    product_grouped_df.set_index('Cluster MBA', inplace=True)
    product_grouped_df = product_grouped_df.groupby('Cluster MBA').agg(lambda x: list(x))

    product_grouped_df['Product'] = product_grouped_df.apply(format_proportion, axis=1, mode='product')

    product_grouped_df = product_grouped_df.groupby('Cluster MBA')['Product'].apply(
        lambda x: ', '.join(x)).reset_index()
    product_grouped_df.set_index('Cluster MBA', inplace=True)

    category_melted_df = pd.melt(category_clusters.reset_index(), id_vars=['Customer_ID', 'Cluster MBA'],
                                 var_name='category', value_name='spending')
    category_melted_df = category_melted_df[category_melted_df['spending'] > 0]
    category_melted_df = category_melted_df[category_melted_df['spending'] > 0]
    cluster_total_spending = category_melted_df.groupby('Cluster MBA')['spending'].transform('sum')
    category_melted_df['proportion'] = category_melted_df['spending'] / cluster_total_spending
    category_grouped_df = category_melted_df.groupby(['Cluster MBA', 'category'])['proportion'].sum()
    category_grouped_df = category_grouped_df.reset_index()
    category_grouped_df['proportion'] = category_grouped_df['proportion'].map(lambda x: f"{x:.2%}")
    category_grouped_df.set_index('Cluster MBA', inplace=True)
    category_grouped_df = category_grouped_df.groupby('Cluster MBA').agg(lambda x: list(x))

    category_grouped_df['Category'] = category_grouped_df.apply(format_proportion, axis=1, mode='category')

    category_grouped_df = category_grouped_df.groupby('Cluster MBA')['Category'].apply(
        lambda x: ', '.join(x)).reset_index()
    category_grouped_df.set_index('Cluster MBA', inplace=True)

    with st.expander('Product Clusters'):
        st.dataframe(product_clusters)
        st.dataframe(product_grouped_df)

    with st.expander('Category Clusters'):
        st.dataframe(category_clusters)
        st.dataframe(category_grouped_df)

    with st.expander('Recommendations'):
        product_recommendation = apriori_rules_products[['antecedents_', 'consequents_']]
        product_recommendation = product_recommendation.rename(columns={'antecedents_': 'Bought Product',
                                                                        'consequents_': 'Recommended Product'})
        product_recommendation.set_index('Bought Product', inplace=True)
        st.dataframe(product_recommendation)

        category_recommendation = apriori_rules_categories[['antecedents_', 'consequents_']]
        category_recommendation = category_recommendation.rename(columns={'antecedents_': 'Bought Category',
                                                                          'consequents_': 'Recommended Category'})
        category_recommendation.set_index('Bought Category', inplace=True)
        st.dataframe(category_recommendation)

        st.dataframe(recommendations_ubcf)
        st.dataframe(recommendations_ubcfc)
        st.dataframe(recommendations_ibcf)
        st.dataframe(recommendations_ibcfc)

    return product_grouped_df, category_grouped_df, product_recommendation, category_recommendation


def mba_main_function(df_sales, df_lines, products, categories, customers, directory, sales_filter, customer_type):
    mba_statistics, prod_aff_tab, most_freq_tab, product_pred_tab, data_tab = st.tabs(
        ['Statistics', 'Product affinity', 'Most Frequent Pattern', 'Recommendations', 'Download data'])
    with mba_statistics:
        st.header(f'MBA KPIs', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: All data were used' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: All data were used', icon='ℹ️')
        mba_statistics_main_function(df_sales, df_lines, products, categories, sales_filter)
    with prod_aff_tab:
        st.header(f'Basket Clusters', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: All data were used' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: All data were used', icon='ℹ️')
        data_filter = st.radio('Analyze the Data based on', ['Quantity', 'Total_price'], horizontal=True)
        product_clusters, category_clusters = prod_aff_main_function(df_sales, df_lines, categories, products,
                                                                     sales_filter, data_filter)
    with most_freq_tab:
        st.header(f'Most Frequent Pattern', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: All data were used' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: All data were used', icon='ℹ️')
        apriori_rules_products, apriori_rules_categories = most_frequent_pattern_main_function(df_lines, products,
                                                                                               categories,
                                                                                               sales_filter)
    with product_pred_tab:
        st.header(f'Recommendations', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: Invoice data' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: All data were used', icon='ℹ️')
        next_prod_pred_main_function(apriori_rules_products, apriori_rules_categories, products, categories,
                                     customers, df_sales, df_lines)
    with data_tab:
        recommendations_ubcf, recommendations_ubcfc, recommendations_ibcf, recommendations_ibcfc = get_all_recommendations(
            customers, products, categories, df_sales, df_lines)
        product_grouped_df, category_grouped_df, product_recommendation, category_recommendation = show_mba(
            product_clusters, category_clusters, apriori_rules_products, apriori_rules_categories, recommendations_ubcf, recommendations_ubcfc, recommendations_ibcf, recommendations_ibcfc)

    return product_clusters, category_clusters, product_grouped_df, category_grouped_df, product_recommendation, category_recommendation, recommendations_ubcf, recommendations_ubcfc, recommendations_ibcf, recommendations_ibcfc
