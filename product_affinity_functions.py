import pandas as pd
import streamlit as st
from sklearn.manifold import TSNE
import plotly.graph_objects as go
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from yellowbrick.cluster import SilhouetteVisualizer


def compute_values(x, y, df_sales):
    fx_ = len(df_sales[df_sales['Product_ID'] == x])
    fy_ = len(df_sales[df_sales['Product_ID'] == y])

    df = df_sales.groupby('Invoice_ID')['Product_ID'].apply(list).reset_index(name='new')

    def is_subset_present(row, subset):
        return all(elem in row for elem in subset)

    fxy_ = df['new'].apply(lambda row: is_subset_present(row, [x, y])).sum()

    try:
        support = fxy_ / len(df_sales)
        confidence = support / (fx_ / len(df_sales))
        lift = confidence / (fy_ / len(df_sales))
    except ZeroDivisionError:
        support = None
        confidence = None
        lift = None

    return round(support * 100, 2), round(confidence * 100, 2), round(lift * 100, 2)


def clean_data(products, df_sales, df_lines, transformed_sales_filter):
    df = df_sales.merge(df_lines, on=transformed_sales_filter + '_ID')
    df = df[['Product_ID', 'Customer_ID', 'Total_price_x']]
    df = df.groupby(['Customer_ID', 'Product_ID'])['Total_price_x'].sum().reset_index()

    df = df.pivot(index='Customer_ID', columns='Product_ID', values='Total_price_x').fillna(0.0)
    df.columns = ['Prod_' + str(col) for col in df.columns]

    df_cat = df_sales.merge(df_lines, on=transformed_sales_filter + '_ID').merge(products, on='Product_ID')
    df_cat = df_cat[['Product_ID', 'Category_ID', 'Customer_ID', 'Total_price_x']]
    df_cat = df_cat.groupby(['Customer_ID', 'Category_ID'])['Total_price_x'].sum().reset_index()
    df_cat = df_cat.pivot(index='Customer_ID', columns='Category_ID', values='Total_price_x').fillna(0.0)
    df_cat.columns = ['Cat_' + str(col) for col in df_cat.columns]

    # To have the name of the products
    # df = df.groupby(['Customer_ID', 'Product_ID'])['Total_price_x'].sum()
    # df = pd.DataFrame(df).unstack().fillna(0.0)
    # column_names = [products.loc[products['Product_ID'] == col[1], 'Product_name'].values[0] for col in df.columns]
    # df.columns = column_names

    # To get the categories, but some products have 2 or more categories
    # Therefore, the sum of "total price" is not correct !
    # categories_list = categories[['Category_ID', 'Category_name']].to_dict(orient='records')
    # df_cat = pd.DataFrame(index=df.index)
    #
    # for category in categories_list:
    #     category_id = category['Category_ID']
    #     category_name = category['Category_name']
    #
    #     matching_columns = [col for col in df.columns if col.startswith(str(category_id))]
    #     df_cat[category_name] = df[matching_columns].sum(axis=1)

    # To get the parent_ID of the categories
    # df_products = products[['Product_ID', 'Category_ID']]
    # df_categories = categories[['Category_ID', 'Parent_ID']]
    #
    # parent_list = []
    #
    # for i in range(len(df_products)):
    #     categories_list = df_products.loc[i, 'Category_ID']
    #     current_parent_list = []
    #
    #     for cat in categories_list:
    #         parent = df_categories.loc[df_categories['Category_ID'] == int(cat), 'Parent_ID'].values
    #
    #         current_parent_list.extend(parent)
    #
    #     parent_list.append(list(set(current_parent_list)))
    #
    # df_products['Parent_ID'] = parent_list

    # df_exploded = df_products.explode('Parent_ID')
    # value_counts = df_exploded['Parent_ID'].value_counts()
    # st.write(value_counts)
    # st.write(value_counts.shape)

    return df, df_cat


def elbow_method(scaled_features):
    SSE = []
    for cluster in range(1, 12):
        kmeans = KMeans(n_clusters=cluster, init='k-means++')
        kmeans.fit(scaled_features)
        SSE.append(kmeans.inertia_)

    frame = pd.DataFrame({'Cluster': range(1, 12), 'SSE': SSE})
    st.write(px.line(x=frame['Cluster'], y=frame['SSE']))
    return


def basket_clusters(scaled_features, nb_clusters):
    kmeans = KMeans(n_clusters=nb_clusters, init='k-means++')
    kmeans.fit(scaled_features)

    visualizer = SilhouetteVisualizer(kmeans, colors='yellowbrick')

    visualizer.fit(scaled_features)

    st.write("Silhouette score : ", round(silhouette_score(scaled_features, kmeans.labels_, metric='euclidean'), 2))

    pred = kmeans.predict(scaled_features)
    scaled_features['cluster'] = pred

    return scaled_features


def compute_affinity_values(products, invoices_lines):
    col1, col2 = st.columns(2)
    products_dict = dict(zip(products['Product_ID'], products['Product_name']))
    item1 = col1.selectbox('Products 1', products_dict.values())
    item1_ID = list(products_dict.keys())[list(products_dict.values()).index(item1)]
    item2 = col2.selectbox('Products 2', products_dict.values())
    item2_ID = list(products_dict.keys())[list(products_dict.values()).index(item2)]
    support, confidence, lift = compute_values(item1_ID, item2_ID, invoices_lines)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Support', str(support) + "%")
        st.expander("See explanation")
        st.write('Support assess the overall popularity of a given product.')
        st.write('This metric shows the percentage of invoices that contain both products.')
    with col2:
        st.metric('Confidence', str(confidence) + "%")
        st.expander("See explanation")
        st.write('Confidence tells us the likelihood of different purchase combinations.')
        st.write('This metric indicates how often the second product is purchased when the first one is purchased.')
    with col3:
        st.metric("Lift", str(lift) + "%")
        st.expander("See explanation")
        st.write('Lift refers to the increase in the ratio of the sale of product 2 when you sell product 1.')
        st.write('Generally speaking, bigger the lift number, higher is the association.')


def prod_aff_main_function(df_sales, df_lines, products, directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter):
    # st.header(f'Product affinities for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]')
    # compute_affinity_values(products, df_lines)

    st.header(f'Basket Clusters for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]')
    product_features, categorie_features = clean_data(products, df_sales, df_lines, transformed_sales_filter)
    choice = st.radio('Based on ?', ['Products', 'Categories'])
    if choice == 'Products':
        elbow_method(product_features)
        nb_clusters_product = st.slider('Number of Clusters', 2, 11, 4)
        avg_df = basket_clusters(product_features, nb_clusters_product)

        tsne = TSNE(n_components=2, random_state=0)
        projections = tsne.fit_transform(avg_df)
        fig = px.scatter(projections, x=0, y=1, color=avg_df.cluster)
        st.write(fig)

        tsne = TSNE(n_components=3, random_state=0)
        projections = tsne.fit_transform(avg_df)
        fig = px.scatter_3d(projections, x=0, y=1, z=2, color=avg_df.cluster)
        st.write(fig)

        # umap_2d = UMAP(n_components=2, init='random', random_state=0)
        # proj_2d = umap_2d.fit_transform(avg_df)
        # fig_2d = px.scatter(
        #     proj_2d, x=0, y=1
        # )
        # st.write(fig_2d)

    else:
        elbow_method(categorie_features)
        nb_clusters_product = st.slider('Number of Clusters', 2, 11, 4)
        avg_df = basket_clusters(categorie_features, nb_clusters_product)
        avg_df = avg_df.groupby(['cluster'], as_index=False).mean().set_index('cluster')

        fig = go.Figure()
        for i in range(len(avg_df)):
            fig.add_trace(go.Scatterpolar(
                r=[avg_df[j][i] for j in avg_df.columns],
                theta=avg_df.columns,
                fill='toself',
                name='Cluster ' + str(i)
            ))
        st.write(fig)

    return

