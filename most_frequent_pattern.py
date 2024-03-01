import pandas as pd
import plotly.express as px
import streamlit as st
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth


@st.cache_data
def clean_data(df_lines, products, categories, sales_filter, mode):
    data = df_lines.merge(products, on='Product_ID').merge(categories, on='Category_ID').groupby(
        sales_filter + '_ID')[mode + '_name'].apply(lambda x: list(set(x))).to_frame()
    data = list(data[mode + '_name'])

    te = TransactionEncoder()
    te_ary = te.fit(data).transform(data)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    return df


@st.cache_resource
def apriori_approach(df, min_support=0.001, metric="confidence", min_threshold=0.01):
    apriori_res = apriori(df, min_support=min_support, use_colnames=True).sort_values(by="support", ascending=False)
    bar_data = apriori_res[:5].copy()
    bar_data.loc[:, 'itemsets'] = bar_data['itemsets'].apply(list).astype(str)
    fig = px.bar(x=bar_data['itemsets'], y=bar_data['support'],
                 labels={'x': 'Product', 'y': 'Support value'}).update_layout(
        title='Top 5 Association Rules by Support Value')
    st.write(fig)

    rules = association_rules(apriori_res, metric=metric, min_threshold=min_threshold).sort_values(by='confidence',
                                                                                                   ascending=False)
    rules['antecedents items'] = rules['antecedents'].apply(lambda x: len(x))
    rules['consequents items'] = rules['consequents'].apply(lambda x: len(x))
    rules['antecedents_'] = rules['antecedents'].apply(lambda a: ','.join(list(a)))
    rules['consequents_'] = rules['consequents'].apply(lambda a: ','.join(list(a)))

    pivot = rules[(rules['antecedents items'] == 1) & (rules['consequents items'] == 1)].pivot(index='antecedents_',
                                                                                               columns='consequents_',
                                                                                               values=metric)
    fig = px.imshow(pivot).update_layout(title='Association Rules with Single Antecedents and Consequents')
    st.write(fig)
    return apriori_res, rules


@st.cache_resource
def fpgrowth_approach(df, min_support=0.001, metric='lift', min_threshold=0.01):
    fpgrowth_res = fpgrowth(df, min_support=min_support, use_colnames=True).sort_values(by="support", ascending=False)
    bar_data = fpgrowth_res[:5].copy()
    bar_data.loc[:, 'itemsets'] = bar_data['itemsets'].apply(list).astype(str)
    fig = px.bar(x=bar_data['itemsets'], y=bar_data['support'],
                 labels={'x': 'Product', 'y': 'Support value'}).update_layout(
        title='Top 5 Association Rules by Support Value')
    st.write(fig)

    rules = association_rules(fpgrowth_res, metric=metric, min_threshold=min_threshold).sort_values(by='confidence',
                                                                                                    ascending=False)
    rules['antecedents items'] = rules['antecedents'].apply(lambda x: len(x))
    rules['consequents items'] = rules['consequents'].apply(lambda x: len(x))
    rules['antecedents_'] = rules['antecedents'].apply(lambda a: ','.join(list(a)))
    rules['consequents_'] = rules['consequents'].apply(lambda a: ','.join(list(a)))

    pivot = rules[(rules['antecedents items'] == 1) & (rules['consequents items'] == 1)].pivot(index='antecedents_',
                                                                                               columns='consequents_',
                                                                                               values=metric)
    fig = px.imshow(pivot).update_layout(title='Association Rules with Single Antecedents and Consequents')
    st.write(fig)
    return fpgrowth_res, rules


def most_frequent_pattern_main_function(df_lines, products, categories, transformed_sales_filter):
    df_products = clean_data(df_lines, products, categories, transformed_sales_filter, 'Product')
    df_categories = clean_data(df_lines, products, categories, transformed_sales_filter, 'Category')

    st.subheader('Fine-tuning Models: Hyperparameter Optimization', divider='grey')
    col1, col2, col3 = st.columns(3)
    min_support = col1.number_input('Insert min support', value=0.001, format='%f')
    metric = col2.selectbox('Which metric do you choose ?',
                            ('confidence', 'lift', 'support', 'leverage', 'conviction', 'zhangs_metric'))
    min_threshold = col3.number_input('Insert min threshold', value=0.01, format='%f')

    with st.expander("See explanation"):
        st.write(
            "***Support Value ->*** indicates the rate of seeing antecedent and consequent together in all purchases.")
        st.write("***Confidence Value ->*** shows the percentage of customers who buy antecedent also buy consequent.")
        st.write(
            "***Lift Value ->*** shows by how much the sales of consequent increase for purchases with antecedent.")
        st.write(
            "***Leverage Value ->*** quantifies how much the occurrence of antecedent and consequent together deviates from what would be expected by chance.")
        st.write(
            "***Conviction Value ->*** quantifies how much the presence of antecedent implies the absence of consequent.")
        st.write(
            "***Zhang's metric ->*** measure designed to assess the strength of association (positive or negative) between two items, taking into account both their co-occurrence and their non-co-occurrence.")

    st.subheader('Results: Most Frequent Pattern', divider='grey')
    with st.expander('For Products'):
        apriori_mfp_products, apriori_rules_products = apriori_approach(df_products, min_support, metric, min_threshold)

    with st.expander('For Categories'):
        apriori_mfp_categories, apriori_rules_categories = apriori_approach(df_categories, min_support, metric,
                                                                            min_threshold)

    return apriori_rules_products, apriori_rules_categories
