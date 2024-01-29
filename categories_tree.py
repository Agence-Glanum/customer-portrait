import pandas as pd


def agg_product_ids(product_ids):
    return [pid for pid in product_ids if pd.notna(pid) and pid != '']


def categories_tree(categories, products, directory):
    result_df = pd.merge(categories, products, on='Category_ID', how='left')
    result_df['Parent_ID'] = result_df['Parent_ID'].apply(lambda x: x if pd.notna(x) else None)

    result_df = pd.merge(result_df, categories[['Category_ID', 'Category_name']], left_on='Parent_ID',
                         right_on='Category_ID', how='left')

    result_df = result_df.rename(columns={'Category_name_x': 'Category_name', 'Category_name_y': 'Parent_name',
                                          'Category_ID_x': 'Category_ID'}).drop(columns=["Category_ID_y"])

    result_df = result_df[['Category_ID', 'Category_name', 'Parent_ID', 'Parent_name', 'Product_ID']]

    result_df = result_df.fillna('')

    result_df = result_df.groupby(['Category_ID', 'Category_name', 'Parent_ID', 'Parent_name']).agg({
        'Product_ID': agg_product_ids
    }).reset_index()
    return result_df
