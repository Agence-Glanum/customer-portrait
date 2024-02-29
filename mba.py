import pandas as pd
import streamlit as st
from mba_statistics import mba_statistics_main_function
from most_frequent_pattern import most_frequent_pattern_main_function
from next_product_prediction import next_prod_pred_main_function
from product_affinity_functions import prod_aff_main_function


def show_mba(product_clusters, category_clusters, apriori_rules_products, apriori_rules_categories):
    st.info('The product and category clusters are not the same !')

    product_melted_df = pd.melt(product_clusters.reset_index(), id_vars=['Customer_ID', 'Cluster MBA'],
                                var_name='product', value_name='spending')
    product_melted_df = product_melted_df[product_melted_df['spending'] > 0]
    cluster_total_spending = product_melted_df.groupby('Cluster MBA')['spending'].transform('sum')
    product_melted_df['proportion'] = product_melted_df['spending'] / cluster_total_spending
    product_grouped_df = product_melted_df.groupby(['Cluster MBA', 'product'])['proportion'].sum()
    product_grouped_df = product_grouped_df.reset_index()
    product_grouped_df['proportion'] = product_grouped_df['proportion'].map(lambda x: f"{x:.2%}")
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

    with st.expander('Product Clusters'):
        st.dataframe(product_clusters)
        st.dataframe(product_grouped_df)

    with st.expander('Category Clusters'):
        st.dataframe(category_clusters)
        st.dataframe(category_grouped_df)

    with st.expander('Recommendations'):
        product_recommendation = apriori_rules_products[['antecedents_', 'consequents_']]
        product_recommendation.rename(columns={'antecedents_': 'Bought Product',
                                               'consequents_': 'Recommended Product'},
                                      inplace=True)
        product_recommendation.set_index('Bought Product', inplace=True)
        st.dataframe(product_recommendation)

        category_recommendation = apriori_rules_categories[['antecedents_', 'consequents_']]
        category_recommendation.rename(columns={'antecedents_': 'Bought Category',
                                                'consequents_': 'Recommended Category'},
                                       inplace=True)
        category_recommendation.set_index('Bought Category', inplace=True)
        st.dataframe(category_recommendation)
    return product_grouped_df, category_grouped_df, product_recommendation, category_recommendation


def mba_main_function(df_sales, df_lines, products, categories, snapshot_start_date,
                      snapshot_end_date, directory, sales_filter, customer_type):
    mba_statistics, prod_aff_tab, most_freq_tab, product_pred_tab, data_tab = st.tabs(
        ['Statistics', 'Product affinity', 'Most Frequent Pattern', 'Recommendations', 'Download data'])
    with mba_statistics:
        mba_statistics_main_function(df_sales, df_lines, products, categories, snapshot_start_date,
                                     snapshot_end_date, directory, sales_filter, customer_type)
    with prod_aff_tab:
        st.header(f'Basket Clusters', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        product_clusters, category_clusters = prod_aff_main_function(df_sales, df_lines, categories, products,
                                                                     sales_filter)
    with most_freq_tab:
        st.header(f'Most Frequent Pattern', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        apriori_rules_products, apriori_rules_categories = most_frequent_pattern_main_function(
            df_lines, products, categories,
            sales_filter)
    with product_pred_tab:
        st.header(f'Recommendations', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        next_prod_pred_main_function(apriori_rules_products, apriori_rules_categories, products, categories)
    with data_tab:
        product_grouped_df, category_grouped_df, product_recommendation, category_recommendation = show_mba(
            product_clusters, category_clusters, apriori_rules_products, apriori_rules_categories)
    return product_clusters, category_clusters, product_grouped_df, category_grouped_df, product_recommendation, category_recommendation
