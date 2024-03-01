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


@st.cache_data
def clean_data(categories, products, df_sales, df_lines, data_filter, sales_filter):
    df_sales.rename(columns={'Total_price': 'Final_price'}, inplace=True)
    df = df_sales.merge(df_lines, on=sales_filter + '_ID').merge(products, on='Product_ID')
    df = df[['Product_name', 'Customer_ID', data_filter]]
    df = df.groupby(['Customer_ID', 'Product_name'])[data_filter].sum().reset_index()
    df = df.pivot(index='Customer_ID', columns='Product_name', values=data_filter).fillna(0.0)
    df.columns = [str(col) for col in df.columns]

    df_cat = df_sales.merge(df_lines, on=sales_filter + '_ID').merge(products, on='Product_ID').merge(
        categories, on='Category_ID')
    df_cat = df_cat[['Product_name', 'Category_name', 'Customer_ID', data_filter]]
    df_cat = df_cat.groupby(['Customer_ID', 'Category_name'])[data_filter].sum().reset_index()
    df_cat = df_cat.pivot(index='Customer_ID', columns='Category_name', values=data_filter).fillna(0.0)
    df_cat.columns = [str(col) for col in df_cat.columns]

    return df, df_cat


@st.cache_resource
def elbow_method(scaled_features):
    SSE = []
    for cluster in range(1, 12):
        kmeans = KMeans(n_clusters=cluster, init='k-means++', n_init='auto')
        kmeans.fit(scaled_features.values)
        SSE.append(kmeans.inertia_)

    frame = pd.DataFrame({'Cluster': range(1, 12), 'SSE': SSE})
    fig = px.line(x=frame['Cluster'], y=frame['SSE'])
    st.write(fig)
    return fig


@st.cache_data
def show_umap(umap_2d_data, umap_3d_data, product_clusters):
    fig_2d = px.scatter(x=umap_2d_data[:, 0], y=umap_2d_data[:, 1],
                        title='2D UMAP Basket Clusters', color=product_clusters['Cluster MBA'].astype(str))
    st.write(fig_2d)

    fig_3d = px.scatter_3d(x=umap_3d_data[:, 0], y=umap_3d_data[:, 1], z=umap_3d_data[:, 2],
                           title='3D UMAP Basket Clusters', color=product_clusters['Cluster MBA'].astype(str))
    st.write(fig_3d)
    return fig_2d, fig_3d


@st.cache_data
def show_radar_plot(categorie_clusters):
    avg_df = categorie_clusters.groupby(['Cluster MBA']).mean()
    fig = go.Figure()
    for i in range(len(avg_df)):
        fig.add_trace(go.Scatterpolar(
            r=[avg_df[j][i] for j in avg_df.columns],
            theta=avg_df.columns,
            fill='toself',
            name='Cluster ' + str(i)
        ))
    fig.update_layout(title='Basket Clusters Radar plot')
    st.write(fig)
    return fig


@st.cache_resource
def kmeans_model(features, nb_clusters):
    elbow_method(features)
    model = KMeans(n_clusters=nb_clusters, init='k-means++', n_init='auto')
    model.fit(features.values)
    st.success('Silhouette score : ' + str(round(silhouette_score(features, model.labels_, metric='euclidean'), 2)))
    predictions = model.predict(features)
    features['Cluster MBA'] = ['Cluster ' + str(pred) for pred in predictions]
    return features


@st.cache_resource
def agglomerative_model(features, nb_clusters):
    Z = linkage(features, 'ward')
    fig, ax = plt.subplots()
    plt.title('Hierarchical Clustering Dendrogram')
    dendrogram(Z, truncate_mode='lastp', leaf_rotation=90., show_contracted=True)
    st.pyplot(fig)

    model = AgglomerativeClustering(n_clusters=nb_clusters, compute_distances=True)
    predictions = model.fit_predict(features)
    features['Cluster MBA'] = ['Cluster ' + str(pred) for pred in predictions]
    return features


def prod_aff_main_function(df_sales, df_lines, categories, products, sales_filter, data_filter):
    product_features, category_features = clean_data(categories, products, df_sales, df_lines, data_filter,
                                                     sales_filter)
    ump_2d = umap.UMAP(n_components=2, init='random')
    umap_2d_data = ump_2d.fit_transform(product_features)
    ump_3d = umap.UMAP(n_components=3, init='random')
    umap_3d_data = ump_3d.fit_transform(product_features)

    with st.expander('Product Clusters'):
        product_model_name = st.radio('Choose the model for Product Clustering',
                                      ['Kmeans', 'Agglomerative Clustering'])
        if product_model_name == 'Kmeans':
            nb_clusters_product = st.slider('Number of Product Clusters', 2, 11, 4)
            product_clusters = kmeans_model(product_features, nb_clusters_product)
        else:
            nb_clusters_product = st.slider('How many Product Clusters do you want ?', 2, 11, 4)
            product_clusters = agglomerative_model(product_features, nb_clusters_product)

        show_umap(umap_2d_data, umap_3d_data, product_clusters)

    with st.expander('Category Clusters'):
        category_model_name = st.radio('Choose the model for Category Clustering',
                                       ['Kmeans', 'Agglomerative Clustering'])
        if category_model_name == 'Kmeans':
            nb_clusters_category = st.slider('Number of Category Clusters', 2, 11, 4)
            category_clusters = kmeans_model(category_features, nb_clusters_category)
        else:
            nb_clusters_category = st.slider('How many Category Clusters do you want ?', 2, 11, 4)
            category_clusters = agglomerative_model(category_features, nb_clusters_category)

        show_radar_plot(category_clusters)

    return product_clusters, category_clusters
