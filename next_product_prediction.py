import pandas as pd
import streamlit as st


def recommend_product(df, product):  # num_of_products
    df.sort_values('lift', ascending=False, inplace=True)
    recommendation_list = []
    for index, row in df.iterrows():
        if product in row["antecedents_"]:
            recommendation_list.append(row["consequents_"])
    try:
        return recommendation_list[0]  # recommendation_list[0:num_of_products]
    except IndexError:
        return 'No recommendation available'


def collaborative_filtering_rs(df_sales, df_lines, products, categories):
    df_merged = pd.merge(df_sales, df_lines, on='Invoice_ID', how='left')
    df_merged = pd.merge(df_merged, products, on='Product_ID', how='left')
    df_merged = pd.merge(df_merged, categories, on='Category_ID', how='left')
    features = df_merged[['Customer_ID', 'Invoice_date', 'Product_name',
                          'Quantity', 'Unit_price', 'Category_name']]
    # count_values = features.groupby('Product_name')['Quantity'].sum().reset_index().sort_values(by='Quantity', ascending=False)
    # rare_products = count_values[count_values['Quantity'] <= 10]['Product_name']  # Change the threshold
    # features = features[~features['Product_name'].isin(rare_products)]

    features = features.groupby(["Customer_ID", "Product_name"])["Quantity"].sum().unstack()
    features.fillna(0, inplace=True)
    normalized_features = features.div(features.sum(), axis=1)
    st.write(normalized_features)

    return


def next_prod_pred_main_function(df_sales, df_lines, apriori_rules, fpgrowth_rules, products, categories):
    product = st.selectbox('Choose a product', products['Product_name'])

    st.header('Product recommendation', divider='grey')
    with st.expander('Apriori and FP growth approaches'):
        st.subheader('First approach - Apriori')
        st.write(recommend_product(apriori_rules, product))

        st.subheader('Second approach - FP growth')
        st.write(recommend_product(fpgrowth_rules, product))
    with st.expander('Collaborative filtering'):
        collaborative_filtering_rs(df_sales, df_lines, products, categories)

    return
