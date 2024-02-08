import pandas as pd
import streamlit as st


def agg_product_ids(product_ids):
    return [pid for pid in product_ids if pd.notna(pid) and pid != '']


def show_data(categories, products, directory, snapshot_start_date, snapshot_end_date):
    result_df = pd.merge(categories, products, on='Category_ID', how='left')
    result_df['Parent_ID'] = result_df['Parent_ID'].apply(lambda x: x if pd.notna(x) else None)

    result_df = pd.merge(result_df, categories[['Category_ID', 'Category_name']], left_on='Parent_ID',
                         right_on='Category_ID', how='left')

    result_df = result_df.rename(columns={'Category_name_x': 'Category_name',
                                          'Category_name_y': 'Parent_name'}).drop(columns=["Category_ID_x", "Category_ID_y"])

    result_df = result_df[['Category_name', 'Parent_name', 'Product_name']].fillna('')

    result_df = result_df.groupby(['Category_name', 'Parent_name']).agg({'Product_name': agg_product_ids}).reset_index()
    st.subheader(
        f"Categories details for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]",
        divider='grey')
    st.dataframe(result_df, use_container_width=True)
    return result_df


def show_mba(directory, products, product_clusters, category_clusters):
    if directory == 'Ici store':
        st.info('The clusters for these tables are not the same !')
        product_ids = [int(col) for col in product_clusters.columns if col != 'cluster']
        product_dic = {str(col): products.loc[products['Product_ID'] == col, 'Product_name'].values[0] for col in
                       product_ids}

        product_clusters = product_clusters.rename(columns=product_dic)
        st.dataframe(product_clusters)

        st.dataframe(category_clusters)
    else:
        st.info('This feature is not ready yet.')
    return
