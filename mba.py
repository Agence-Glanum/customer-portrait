import pandas as pd
import streamlit as st

from mba_statistics import mba_statistics_main_function
from most_frequent_pattern import most_frequent_pattern_main_function
from next_product_prediction import next_prod_pred_main_function
from product_affinity_functions import prod_aff_main_function


def agg_product_ids(product_ids):
    return [pid for pid in product_ids if pd.notna(pid) and pid != '']


def show_data(categories, products, directory, snapshot_start_date, snapshot_end_date):
    result_df = pd.merge(categories, products, on='Category_ID', how='left')
    result_df['Parent_ID'] = result_df['Parent_ID'].apply(lambda x: x if pd.notna(x) else None)

    result_df = pd.merge(result_df, categories[['Category_ID', 'Category_name']], left_on='Parent_ID',
                         right_on='Category_ID', how='left')

    result_df = result_df.rename(columns={'Category_name_x': 'Category_name',
                                          'Category_name_y': 'Parent_name'}).drop(
        columns=["Category_ID_x", "Category_ID_y"])

    result_df = result_df[['Category_name', 'Parent_name', 'Product_name']].fillna('')

    result_df = result_df.groupby(['Category_name', 'Parent_name']).agg({'Product_name': agg_product_ids}).reset_index()
    st.subheader(
        f"Categories details for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]",
        divider='grey')
    st.dataframe(result_df, use_container_width=True)
    return result_df


def show_mba(product_clusters, category_clusters, apriori_rules_products, fpgrowth_rules_products,
             apriori_rules_categories, fpgrowth_rules_categories):
    st.info('The product and category clusters are not the same !')

    product_melted_df = pd.melt(product_clusters.reset_index(), id_vars=['Customer_ID', 'Cluster MBA'],
                                var_name='product', value_name='spending')
    product_melted_df = product_melted_df[product_melted_df['spending'] > 0]
    product_grouped_df = product_melted_df.groupby('Cluster MBA')['product'].apply(lambda x: list(set(x)))

    category_melted_df = pd.melt(category_clusters.reset_index(), id_vars=['Customer_ID', 'Cluster MBA'],
                                 var_name='category', value_name='spending')
    category_melted_df = category_melted_df[category_melted_df['spending'] > 0]
    category_grouped_df = category_melted_df.groupby('Cluster MBA')['category'].apply(lambda x: list(set(x)))

    with st.expander('Product Clusters'):
        st.dataframe(product_clusters)
        st.dataframe(product_grouped_df)

    with st.expander('Category Clusters'):
        st.dataframe(category_clusters)
        st.dataframe(category_grouped_df)

    with st.expander('Recommendations'):
        st.subheader('Product recommendation')
        product_recommendation = apriori_rules_products[['antecedents_', 'consequents_']]
        st.dataframe(product_recommendation)
        # st.dataframe(fpgrowth_rules_products[['antecedents_', 'consequents_']])
        st.subheader('Category recommendation')
        category_recommendation = apriori_rules_categories[['antecedents_', 'consequents_']]
        st.dataframe(category_recommendation)
        # st.dataframe(fpgrowth_rules_categories[['antecedents_', 'consequents_']])
    return product_grouped_df, category_grouped_df, product_recommendation, category_recommendation


def mba_main_function(df_sales, df_lines, products, categories, snapshot_start_date,
                      snapshot_end_date, directory, sales_filter, customer_type):
    mba_statistics, prod_aff_tab, most_freq_tab, product_pred_tab, data_tab = st.tabs(
        ['Statistics', 'Product affinity', 'Most Frequent Pattern', 'Next product prediction', 'Download data'])
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
        apriori_rules_products, fpgrowth_rules_products, apriori_rules_categories, fpgrowth_rules_categories = most_frequent_pattern_main_function(
            df_lines, products, categories,
            sales_filter)
    with product_pred_tab:
        next_prod_pred_main_function(df_sales, df_lines, apriori_rules_products, fpgrowth_rules_products, products, categories)
    with data_tab:
        product_grouped_df, category_grouped_df, product_recommendation, category_recommendation = show_mba(
            product_clusters, category_clusters,
            apriori_rules_products, fpgrowth_rules_products,
            apriori_rules_categories, fpgrowth_rules_categories)
    return product_clusters, category_clusters, product_grouped_df, category_grouped_df, product_recommendation, category_recommendation
