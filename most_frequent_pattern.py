import pandas as pd
import streamlit as st
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules


def most_frequent_pattern_main_function(invoices_lines, products):
    data = invoices_lines.merge(products, on='Product_ID').groupby('Invoice_ID')['Product_name'].apply(lambda x: list(set(x))).to_frame()
    data = list(data['Product_name'])

    te = TransactionEncoder()
    te_ary = te.fit(data).transform(data)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    st.subheader('Sales')
    st.dataframe(df)

    st.header('First approach - Apriori')
    st.subheader('Most Frequent Items')
    apriori_res = apriori(df, min_support=0.01, use_colnames=True).sort_values(by="support", ascending=False)
    st.dataframe(apriori_res)

    st.subheader('Association rules')
    rules = association_rules(apriori_res, metric="confidence", min_threshold=0.01).sort_values(
        ['confidence', 'lift'], ascending=[False, False])
    st.dataframe(rules)

    with st.expander("See explanation"):
        st.write("We can interpret our resulting table as follows.")
        st.write("***Support Value ->*** indicates the rate of seeing antecedent and consequent together in all purchases.")
        st.write("***Confidence Value ->*** shows the percentage of customers who buy antecedent also buy consequent.")
        st.write("***Lift Value ->*** shows by how much the sales of consequent increase for purchases with antecedent.")
        st.write("***Leverage Value ->*** quantifies how much the occurrence of antecedent and consequent together deviates from what would be expected by chance.")
        st.write("***Conviction Value ->*** quantifies how much the presence of antecedent implies the absence of consequent.")
        st.write("***Zhang's metric ->*** measure designed to assess the strength of association (positive or negative) between two items, taking into account both their co-occurrence and their non-co-occurrence.")

    return
