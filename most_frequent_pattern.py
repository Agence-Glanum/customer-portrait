import pandas as pd
import plotly.express as px
import streamlit as st
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth


def clean_data(df_lines, products, transformed_sales_filter):
    data = df_lines.merge(products, on='Product_ID').groupby(transformed_sales_filter + '_ID')['Product_name'].apply(
        lambda x: list(set(x))).to_frame()
    data = list(data['Product_name'])

    te = TransactionEncoder()
    te_ary = te.fit(data).transform(data)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    return df


def apriori_approach(df, min_support=0.001, metric="confidence", min_threshold=0.01):
    st.subheader('Most Frequent Items')
    apriori_res = apriori(df, min_support=min_support, use_colnames=True).sort_values(by="support", ascending=False)
    bar_data = apriori_res[:5]
    bar_data['itemsets'] = bar_data['itemsets'].apply(list).astype(str)
    st.write(px.bar(x=bar_data['itemsets'], y=bar_data['support'], labels={'x': 'Product', 'y': 'Support value'}))

    # apriori_res['length'] = apriori_res['itemsets'].apply(lambda x: len(x))
    # heatmap_data = apriori_res[apriori_res['length'] == 2].drop(['length'], axis=1)
    # heatmap_data['Item1'] = heatmap_data['itemsets'].apply(lambda x: list(x)[0])
    # heatmap_data['Item2'] = heatmap_data['itemsets'].apply(lambda x: list(x)[1])
    # heatmap_data = heatmap_data.pivot(index='Item1', columns='Item2', values='support').fillna(0)
    # st.write(px.imshow(heatmap_data))

    st.subheader('Association rules')
    rules = association_rules(apriori_res, metric=metric, min_threshold=min_threshold).sort_values(by='confidence',
                                                                                                   ascending=False)
    rules['antecedents items'] = rules['antecedents'].apply(lambda x: len(x))
    rules['consequents items'] = rules['consequents'].apply(lambda x: len(x))
    rules['antecedents_'] = rules['antecedents'].apply(lambda a: ','.join(list(a)))
    rules['consequents_'] = rules['consequents'].apply(lambda a: ','.join(list(a)))

    pivot = rules.pivot(index='antecedents_', columns='consequents_', values=metric)
    st.write(px.imshow(pivot[:5]))
    return apriori_res, rules


def fpgrowth_approach(df, min_support=0.001, metric='lift', min_threshold=0.01):
    st.subheader('Most Frequent Items')
    fpgrowth_res = fpgrowth(df, min_support=min_support, use_colnames=True).sort_values(by="support", ascending=False)
    bar_data = fpgrowth_res[:5]
    bar_data['itemsets'] = bar_data['itemsets'].apply(list).astype(str)
    st.write(px.bar(x=bar_data['itemsets'], y=bar_data['support'], labels={'x': 'Product', 'y': 'Support value'}))

    st.subheader('Association rules')
    rules = association_rules(fpgrowth_res, metric=metric, min_threshold=min_threshold)
    rules['antecedents items'] = rules['antecedents'].apply(lambda x: len(x))
    rules['consequents items'] = rules['consequents'].apply(lambda x: len(x))
    rules['antecedents_'] = rules['antecedents'].apply(lambda a: ','.join(list(a)))
    rules['consequents_'] = rules['consequents'].apply(lambda a: ','.join(list(a)))

    pivot = rules.pivot(index='antecedents_', columns='consequents_', values=metric)
    st.write(px.imshow(pivot[:5]))
    return fpgrowth_res, rules


def most_frequent_pattern_main_function(df_lines, products, transformed_sales_filter):
    df = clean_data(df_lines, products, transformed_sales_filter)

    col1, col2, col3 = st.columns(3)
    min_support = col1.number_input('Insert min support', value=0.001, format='%f')
    metric = col2.selectbox('Which metric do you choose ?',
                          ('confidence', 'lift'))
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

    st.header('First approach - Apriori')
    apriori_mfp, apriori_rules = apriori_approach(df, min_support, metric, min_threshold)

    st.header('Second approach - FP growth')
    fpgrowth_mfp, fpgrowth_rules = fpgrowth_approach(df, min_support, metric, min_threshold)

    return apriori_rules, fpgrowth_rules
