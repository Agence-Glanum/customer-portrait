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


def show_mba(directory, products, product_clusters, category_clusters, apriori_rules_products, fpgrowth_rules_products,
             apriori_rules_categories, fpgrowth_rules_categories):
    if directory == 'Ici store':
        product_ids = [int(col) for col in product_clusters.columns if col != 'Cluster MBA']
        product_dic = {str(col): products.loc[products['Product_ID'] == col, 'Product_name'].values[0] for col in
                       product_ids}

        product_clusters = product_clusters.rename(columns=product_dic)

        st.info('The product and category clusters not the same !')

        with st.expander('Product Clusters'):
            st.dataframe(product_clusters)
            melted_df = pd.melt(product_clusters.reset_index(), id_vars=['Customer_ID', 'Cluster MBA'], var_name='product', value_name='spending')
            melted_df = melted_df[melted_df['spending'] > 0]
            product_grouped_df = melted_df.groupby('Cluster MBA')['product'].apply(lambda x: list(set(x)))
            st.write(product_grouped_df)

        with st.expander('Category Clusters'):
            st.dataframe(category_clusters)
            melted_df = pd.melt(category_clusters.reset_index(), id_vars=['Customer_ID', 'Cluster MBA'], var_name='category',
                                value_name='spending')
            melted_df = melted_df[melted_df['spending'] > 0]
            category_grouped_df = melted_df.groupby('Cluster MBA')['category'].apply(lambda x: list(set(x)))
            st.write(category_grouped_df)

        with st.expander('Recommendations'):
            st.subheader('Product recommendation')
            st.dataframe(apriori_rules_products[['antecedents_', 'consequents_']])
            # st.dataframe(fpgrowth_rules_products[['antecedents_', 'consequents_']])
            st.subheader('Category recommendation')
            st.dataframe(apriori_rules_categories[['antecedents_', 'consequents_']])
            # st.dataframe(fpgrowth_rules_categories[['antecedents_', 'consequents_']])
    else:
        st.info('This feature is not ready yet.')
    return product_grouped_df, category_grouped_df
