from collections import OrderedDict
import pandas as pd
import streamlit as st
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity


@st.cache_data
def associative_rule_learning(df, item):
    df.sort_values('lift', ascending=False, inplace=True)
    recommendation_list = []
    for index, row in df.iterrows():
        if item in row['antecedents_']:
            recommendation_list.append(row["consequents_"])
    try:
        return st.write(recommendation_list[0])
    except IndexError:
        return st.write('No recommendation available')


@st.cache_data
def user_based_collaborative_filtering(products, df_sales, df_lines, customer_id, num_recommendations=3):
    data_filter = 'Quantity'
    sales_filter = 'Invoice'

    df_all = df_sales.merge(df_lines, on=sales_filter + '_ID').merge(products, on='Product_ID')
    df_all = df_all[['Product_name', 'Customer_ID', data_filter]]
    df_all = df_all.groupby(['Customer_ID', 'Product_name'])[data_filter].sum().reset_index()
    df = df_all.pivot(index='Customer_ID', columns='Product_name', values=data_filter).fillna(0.0)
    df.columns = [str(col) for col in df.columns]
    normalized_df = pd.DataFrame(MinMaxScaler().fit_transform(df), columns=df.columns, index=df.index)

    random_customer_df = normalized_df[(normalized_df.index == customer_id)]
    mask = random_customer_df.iloc[0] > 0
    products_bought = mask.index[mask].tolist()

    products_bought_df = normalized_df[normalized_df[products_bought].sum(axis=1) > 0]

    similarity_matrix = cosine_similarity(products_bought_df)
    similarity_matrix_df = pd.DataFrame(similarity_matrix, index=products_bought_df.index,
                                        columns=products_bought_df.index.astype(int))
    similarity_scores = similarity_matrix_df.loc[customer_id].sort_values(ascending=False)[1:]

    products_bought_df.loc[:, 'corr'] = similarity_scores
    products_bought_df.loc[:, 'weighted_corr'] = 0
    for product_bought in products_bought:
        products_bought_df.loc[:, 'weighted_corr'] += products_bought_df.loc[:, 'corr'] * products_bought_df.loc[:,
                                                                                          product_bought]

    products_bought_df = products_bought_df.loc[:, 'weighted_corr'].sort_values(ascending=False)

    recommended_products = OrderedDict()
    for similar_customer_id, score in products_bought_df.items():
        similar_customer_products = normalized_df.loc[similar_customer_id]
        for product, quantity in similar_customer_products.items():
            if product not in products_bought and quantity > 0:
                if product not in recommended_products:
                    recommended_products[product] = score
                else:
                    recommended_products[product] += score
                if len(recommended_products) >= num_recommendations:
                    break
        if len(recommended_products) >= num_recommendations:
            break

    return recommended_products


@st.cache_data
def user_based_collaborative_filtering_for_category(products, categories, df_sales, df_lines, customer_id,
                                                    num_recommendations=3):
    data_filter = 'Quantity'
    sales_filter = 'Invoice'

    df_all = df_sales.merge(df_lines, on=sales_filter + '_ID').merge(products, on='Product_ID')
    df_all = df_all.merge(categories, on='Category_ID')
    df_all = df_all[['Category_name', 'Customer_ID', data_filter]]
    df_all = df_all.groupby(['Customer_ID', 'Category_name'])[data_filter].sum().reset_index()
    df = df_all.pivot(index='Customer_ID', columns='Category_name', values=data_filter).fillna(0.0)
    df.columns = [str(col) for col in df.columns]
    normalized_df = pd.DataFrame(MinMaxScaler().fit_transform(df), columns=df.columns, index=df.index)

    random_customer_df = normalized_df[(normalized_df.index == customer_id)]
    try:
        mask = random_customer_df.iloc[0] > 0
        bought_categories = mask.index[mask].tolist()

        bought_categories_df = normalized_df[normalized_df[bought_categories].sum(axis=1) > 0]

        similarity_matrix = cosine_similarity(bought_categories_df)
        similarity_matrix_df = pd.DataFrame(similarity_matrix, index=bought_categories_df.index,
                                            columns=bought_categories_df.index.astype(int))
        similarity_scores = similarity_matrix_df.loc[customer_id].sort_values(ascending=False)[1:]

        bought_categories_df.loc[:, 'corr'] = similarity_scores
        bought_categories_df.loc[:, 'weighted_corr'] = 0
        for bought_category in bought_categories:
            bought_categories_df.loc[:, 'weighted_corr'] += bought_categories_df.loc[:, 'corr'] * bought_categories_df.loc[
                                                                      :, bought_category]

        bought_categories_df = bought_categories_df.loc[:, 'weighted_corr'].sort_values(ascending=False)

        recommended_categories = OrderedDict()
        for similar_customer_id, score in bought_categories_df.items():
            similar_customer_categories = normalized_df.loc[similar_customer_id]
            for category, quantity in similar_customer_categories.items():
                if category not in bought_categories and quantity > 0:
                    if category not in recommended_categories:
                        recommended_categories[category] = score
                    else:
                        recommended_categories[category] += score
                    if len(recommended_categories) >= num_recommendations:
                        break
            if len(recommended_categories) >= num_recommendations:
                break

        return recommended_categories
    except IndexError:
        return OrderedDict()


@st.cache_data
def item_based_collaborative_filtering(products, df_sales, df_lines, product_name, num_recommendations=3):
    data_filter = 'Quantity'
    sales_filter = 'Invoice'

    df_all = df_sales.merge(df_lines, on=sales_filter + '_ID').merge(products, on='Product_ID')
    df_all = df_all[['Product_name', 'Customer_ID', data_filter]]
    df_all = df_all.groupby(['Customer_ID', 'Product_name'])[data_filter].sum().reset_index()
    df = df_all.pivot(index='Customer_ID', columns='Product_name', values=data_filter).fillna(0.0)
    df.columns = [str(col) for col in df.columns]
    normalized_df = pd.DataFrame(MinMaxScaler().fit_transform(df), columns=df.columns, index=df.index)

    try:
        random_product_df = normalized_df[product_name]
        other_products_df = normalized_df.drop([product_name], axis=1)

        products_similarity = other_products_df.corrwith(random_product_df).sort_values(ascending=False)

        return products_similarity[:num_recommendations]
    except KeyError:
        return {'No recommendation available': None}


@st.cache_data
def item_based_collaborative_filtering_for_category(products, categories, df_sales, df_lines, category_name,
                                                    num_recommendations=3):
    data_filter = 'Quantity'
    sales_filter = 'Invoice'

    df_all = df_sales.merge(df_lines, on=sales_filter + '_ID').merge(products, on='Product_ID')
    df_all = df_all.merge(categories, on='Category_ID')
    df_all = df_all[['Category_name', 'Customer_ID', data_filter]]
    df_all = df_all.groupby(['Customer_ID', 'Category_name'])[data_filter].sum().reset_index()
    df = df_all.pivot(index='Customer_ID', columns='Category_name', values=data_filter).fillna(0.0)
    df.columns = [str(col) for col in df.columns]
    normalized_df = pd.DataFrame(MinMaxScaler().fit_transform(df), columns=df.columns, index=df.index)

    try:
        random_category_df = normalized_df[category_name]
        other_categories_df = normalized_df.drop([category_name], axis=1)

        categories_similarity = other_categories_df.corrwith(random_category_df).sort_values(ascending=False)

        return categories_similarity[:num_recommendations]
    except KeyError:
        return {'No recommendation available': None}


def get_all_recommendations(customers, products, categories, df_sales, df_lines):
    ubcf_df = {}
    for customer_id in customers['Customer_ID']:
        ubcf_df[customer_id] = user_based_collaborative_filtering(products, df_sales, df_lines, customer_id)
    recommendations_ubcf = pd.DataFrame(index=ubcf_df.keys(),
                                        columns=['Recommendation 1', 'Recommendation 2', 'Recommendation 3'])
    for customer in ubcf_df.keys():
        keys = list(ubcf_df[customer].keys())
        for i in range(3):
            try:
                recommendations_ubcf.loc[customer, 'Recommendation ' + str(i + 1)] = keys[i]
            except IndexError:
                recommendations_ubcf.loc[customer, 'Recommendation ' + str(i + 1)] = None
    recommendations_ubcf.index.name = 'Customers'

    ubcfc_df = {}
    for customer_id in customers['Customer_ID']:
        ubcfc_df[customer_id] = user_based_collaborative_filtering_for_category(products, categories, df_sales,
                                                                                df_lines,
                                                                                customer_id)
    recommendations_ubcfc = pd.DataFrame(index=ubcfc_df.keys(),
                                         columns=['Recommendation 1', 'Recommendation 2', 'Recommendation 3'])
    for customer in ubcfc_df.keys():
        keys = list(ubcfc_df[customer].keys())
        for i in range(3):
            try:
                recommendations_ubcfc.loc[customer, 'Recommendation ' + str(i + 1)] = keys[i]
            except IndexError:
                recommendations_ubcfc.loc[customer, 'Recommendation ' + str(i + 1)] = None
    recommendations_ubcfc.index.name = 'Customers'

    ibcf_df = {}
    for product_name in products['Product_name']:
        ibcf_df[product_name] = item_based_collaborative_filtering(products, df_sales, df_lines, product_name)
    recommendations_ibcf = pd.DataFrame(index=ibcf_df.keys(),
                                        columns=['Recommendation 1', 'Recommendation 2', 'Recommendation 3'])
    for product in ibcf_df.keys():
        keys = list(ibcf_df[product].keys())
        for i in range(3):
            try:
                recommendations_ibcf.loc[product, 'Recommendation ' + str(i + 1)] = keys[i]
            except IndexError:
                recommendations_ibcf.loc[product, 'Recommendation ' + str(i + 1)] = None
    recommendations_ibcf.index.name = 'Products'

    ibcfc_df = {}
    for category_name in categories['Category_name']:
        ibcfc_df[category_name] = item_based_collaborative_filtering_for_category(products, categories, df_sales,
                                                                                  df_lines, category_name)
    recommendations_ibcfc = pd.DataFrame(index=ibcfc_df.keys(),
                                         columns=['Recommendation 1', 'Recommendation 2', 'Recommendation 3'])
    for product in ibcfc_df.keys():
        keys = list(ibcfc_df[product].keys())
        for i in range(3):
            try:
                recommendations_ibcfc.loc[product, 'Recommendation ' + str(i + 1)] = keys[i]
            except IndexError:
                recommendations_ibcfc.loc[product, 'Recommendation ' + str(i + 1)] = None
    recommendations_ibcfc.index.name = 'Categories'

    return recommendations_ubcf, recommendations_ubcfc, recommendations_ibcf, recommendations_ibcfc


def next_prod_pred_main_function(apriori_rules_products, apriori_rules_categories, products, categories, customers,
                                 df_sales, df_lines):
    st.subheader('Associative Rule Learning')
    st.caption('Recommended products')
    product = st.selectbox('Choose a product', products['Product_name'])
    associative_rule_learning(apriori_rules_products, product)

    st.caption('Recommended categories')
    category = st.selectbox('Choose a category', categories['Category_name'])
    associative_rule_learning(apriori_rules_categories, category)

    st.divider()

    st.subheader('Collaborative Filtering - Customer based')
    customer_id = st.selectbox('Customers',
                               (customers['Customer_ID'].astype(str) + ' -- ' + customers['Customer_name']))
    customer_id = int(customer_id.split(' -- ')[0])

    st.caption('Recommended products')
    recommended_products = user_based_collaborative_filtering(products, df_sales, df_lines, customer_id)
    for product, score in recommended_products.items():
        st.markdown(f"- {product}")

    st.caption('Recommended categories')
    recommended_categories = user_based_collaborative_filtering_for_category(products, categories, df_sales, df_lines,
                                                                             customer_id)
    for category, score in recommended_categories.items():
        st.markdown(f"- {category}")

    st.divider()

    st.subheader('Collaborative Filtering - Item based')
    product = st.selectbox('Products',
                           (products['Product_ID'].astype(str) + ' -- ' + products['Product_name']))
    product_name = product.split(' -- ')[1]
    st.caption('Recommended products')
    recommended_products = item_based_collaborative_filtering(products, df_sales, df_lines, product_name)
    for product, score in recommended_products.items():
        st.markdown(f"- {product}")

    category = st.selectbox('Categories',
                            (categories['Category_ID'].astype(str) + ' -- ' + categories['Category_name']))
    category_name = category.split(' -- ')[1]
    st.caption('Recommended categories')
    recommended_categories = item_based_collaborative_filtering_for_category(products, categories, df_sales, df_lines,
                                                                             category_name)
    for category, score in recommended_categories.items():
        st.markdown(f"- {category}")

    return
