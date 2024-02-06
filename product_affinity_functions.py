import hdbscan
import numpy as np
import pandas as pd
import streamlit as st
import umap.umap_ as umap
import plotly.graph_objects as go
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import dendrogram, linkage
from matplotlib import pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import make_scorer


def clean_data(categories, products, df_sales, df_lines, transformed_sales_filter):
    df = df_sales.merge(df_lines, on=transformed_sales_filter + '_ID')
    df = df[['Product_ID', 'Customer_ID', 'Total_price_y']]
    df = df.groupby(['Customer_ID', 'Product_ID'])['Total_price_y'].sum().reset_index()
    df = df.pivot(index='Customer_ID', columns='Product_ID', values='Total_price_y').fillna(0.0)
    df.columns = [str(col) for col in df.columns]

    df_cat = df_sales.merge(df_lines, on=transformed_sales_filter + '_ID').merge(products, on='Product_ID').merge(
        categories, on='Category_ID')
    df_cat = df_cat[['Product_ID', 'Category_name', 'Customer_ID', 'Total_price_y']]
    df_cat = df_cat.groupby(['Customer_ID', 'Category_name'])['Total_price_y'].sum().reset_index()
    df_cat = df_cat.pivot(index='Customer_ID', columns='Category_name', values='Total_price_y').fillna(0.0)
    df_cat.columns = [str(col) for col in df_cat.columns]

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


def show_umap(product_features):
    ump_2d = umap.UMAP(n_components=2, init='random', random_state=0)
    umap_2d_data = ump_2d.fit_transform(product_features)
    fig = px.scatter(x=umap_2d_data[:, 0], y=umap_2d_data[:, 1],
                     title="2D UMAP Basket Clusters", color=product_features.cluster.astype(str))
    st.write(fig)

    ump_3d = umap.UMAP(n_components=3, init='random', random_state=0)
    umap_3d_data = ump_3d.fit_transform(product_features)
    fig = px.scatter_3d(x=umap_3d_data[:, 0], y=umap_3d_data[:, 1], z=umap_3d_data[:, 2],
                        title="3D UMAP Basket Clusters", color=product_features.cluster.astype(str))
    st.write(fig)
    return


def show_radar_plot(categorie_features):
    avg_df = categorie_features.groupby(['cluster']).mean()
    fig = go.Figure()
    for i in range(len(avg_df)):
        fig.add_trace(go.Scatterpolar(
            r=[avg_df[j][i] for j in avg_df.columns],
            theta=avg_df.columns,
            fill='toself',
            name='Cluster ' + str(i)
        ))
    st.write(fig)
    return fig


def kmeans_model(features, mode, nb_clusters):
    elbow_method(features)
    model = KMeans(n_clusters=nb_clusters, init='k-means++')
    model.fit(features)
    st.write("Silhouette score : ", round(silhouette_score(features, model.labels_, metric='euclidean'), 2))
    pred = model.predict(features)
    features['cluster'] = pred
    if mode == 'umap':
        show_umap(features)
    elif mode == 'radar':
        show_radar_plot(features)
    return features


def hdbscan_model(features, mode):
    hdb = hdbscan.HDBSCAN(gen_min_span_tree=True).fit(features)
    param_dist = {'min_cluster_size': [10, 25, 50, 75, 100, 150, 200]}
    validity_scorer = make_scorer(hdbscan.validity.validity_index, greater_is_better=True)
    n_iter_search = 20
    random_search = RandomizedSearchCV(hdb, param_distributions=param_dist,
                                       n_iter=n_iter_search,
                                       scoring=validity_scorer,
                                       random_state=42)
    random_search.fit(features)
    st.write('Hyperparameter Tuning (Best Parameters) : ')
    st.write(f"Min cluster size : {random_search.best_params_['min_cluster_size']}")
    st.write(f"DBCV score : {round(random_search.best_estimator_.relative_validity_, 2)}")

    model = hdbscan.HDBSCAN(min_cluster_size=random_search.best_params_['min_cluster_size'])
    pred = model.fit_predict(features)
    st.write(f"=> Number of optimal clusters : {len(np.unique(model.labels_))}")
    if mode == 'umap':
        features['cluster'] = pred
        show_umap(features)
    elif mode == 'radar':
        features['cluster'] = pred + 1
        show_radar_plot(features)
    return features


def agglomerative_model(features, mode, nb_clusters):
    Z = linkage(features, 'ward')
    fig, ax = plt.subplots()
    plt.title('Hierarchical Clustering Dendrogram')
    dendrogram(Z, truncate_mode='lastp', leaf_rotation=90., show_contracted=True)
    st.pyplot(fig)

    model = AgglomerativeClustering(n_clusters=nb_clusters, compute_distances=True)
    pred = model.fit_predict(features)
    features['cluster'] = pred
    if mode == 'umap':
        show_umap(features)
    elif mode == 'radar':
        show_radar_plot(features)
    return features


def prod_aff_main_function(df_sales, df_lines, categories, products, directory, snapshot_start_date, snapshot_end_date,
                           transformed_sales_filter):
    st.header(f'Basket Clusters for company :blue[{directory}], from :blue[{snapshot_start_date}] '
              f'to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]')
    product_features, category_features = clean_data(categories, products, df_sales, df_lines,
                                                     transformed_sales_filter)

    st.subheader('Product Clusters')
    product_model_name = st.radio('Choose the model for product clustering',
                                  ['Kmeans', 'HDBScan', 'Agglomerative Clustering'])

    if product_model_name == 'Kmeans':
        nb_clusters_product = st.slider('Number of product clusters', 2, 11, 4)
        kmeans_model(product_features, 'umap', nb_clusters_product)
    elif product_model_name == 'HDBScan':
        hdbscan_model(product_features, 'umap')
    else:
        nb_clusters_product = st.slider('How many product clusters do you want ?', 2, 11, 4)
        agglomerative_model(product_features, 'umap', nb_clusters_product)

    st.subheader('Category Clusters')
    category_model_name = st.radio('Choose the model for category clustering',
                                   ['Kmeans', 'HDBScan', 'Agglomerative Clustering'])

    if category_model_name == 'Kmeans':
        nb_clusters_category = st.slider('Number of category clusters', 2, 11, 4)
        kmeans_model(category_features, 'radar', nb_clusters_category)
    elif category_model_name == 'HDBScan':
        hdbscan_model(category_features, 'radar')
    else:
        nb_clusters_category = st.slider('How many category clusters do you want ?', 2, 11, 4)
        agglomerative_model(category_features, 'radar', nb_clusters_category)

    return
