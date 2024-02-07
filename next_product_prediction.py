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


def next_prod_pred_main_function(apriori_rules, fpgrowth_rules, products):
    product = st.selectbox('Choose a product', products['Product_name'])

    st.header('Product recommendation', divider='grey')
    st.subheader('First approach - Apriori')
    st.write(recommend_product(apriori_rules, product))

    st.subheader('Second approach - FP growth')
    st.write(recommend_product(fpgrowth_rules, product))

    return
