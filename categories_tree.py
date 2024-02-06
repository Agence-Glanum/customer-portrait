import pandas as pd
import streamlit as st


def agg_product_ids(product_ids):
    return [pid for pid in product_ids if pd.notna(pid) and pid != '']


def show_data(categories, products):
    result_df = pd.merge(categories, products, on='Category_ID', how='left')
    result_df['Parent_ID'] = result_df['Parent_ID'].apply(lambda x: x if pd.notna(x) else None)

    result_df = pd.merge(result_df, categories[['Category_ID', 'Category_name']], left_on='Parent_ID',
                         right_on='Category_ID', how='left')

    result_df = result_df.rename(columns={'Category_name_x': 'Category_name',
                                          'Category_name_y': 'Parent_name'}).drop(columns=["Category_ID_x", "Category_ID_y"])

    result_df = result_df[['Category_name', 'Parent_name', 'Product_name']].fillna('')

    result_df = result_df.groupby(['Category_name', 'Parent_name']).agg({'Product_name': agg_product_ids}).reset_index()

    st.dataframe(result_df, use_container_width=True)
    return result_df
