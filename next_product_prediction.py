import streamlit as st


def recommend_product(df, product):
    df.sort_values('lift', ascending=False, inplace=True)
    recommendation_list = []
    for index, row in df.iterrows():
        if product in row["antecedents_"]:
            recommendation_list.append(row["consequents_"])
    try:
        return recommendation_list[0]
    except IndexError:
        return 'No recommendation available'


def recommend_category(df, category):
    df.sort_values('lift', ascending=False, inplace=True)
    recommendation_list = []
    for index, row in df.iterrows():
        if category in row["antecedents_"]:
            recommendation_list.append(row["consequents_"])
    try:
        return recommendation_list[0]
    except IndexError:
        return 'No recommendation available'


def next_prod_pred_main_function(apriori_rules_products, apriori_rules_categories, products, categories):
    st.subheader('Next Product')
    product = st.selectbox('Choose a product', products['Product_name'])
    st.write(recommend_product(apriori_rules_products, product))

    st.divider()

    st.subheader('Next Category')
    category = st.selectbox('Choose a category', categories['Category_name'])
    st.write(recommend_category(apriori_rules_categories, category))

    return
