import pandas as pd
from scipy import stats
import numpy as np
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler


def compute_rfm_segments(df, snapshot_end_date, transformed_sales_filter):
    snapshot_end_date = pd.to_datetime(snapshot_end_date)

    rfm = df.groupby('Customer_ID').agg(
        {transformed_sales_filter + '_date': lambda x: (snapshot_end_date - x.max()).days,
         transformed_sales_filter + '_ID': lambda x: len(x),
         'Total_price': lambda x: x.sum()}).reset_index()

    rfm[transformed_sales_filter + '_date'] = rfm[transformed_sales_filter + '_date'].astype(int)

    rfm.rename(columns={transformed_sales_filter + '_date': 'Recency',
                        transformed_sales_filter + '_ID': 'Frequency',
                        'Total_price': 'Monetary'}, inplace=True)
    quintiles = rfm[['Recency', 'Frequency', 'Monetary']].quantile([.2, .4, .6, .8]).to_dict()

    def r_score(x):
        if x <= quintiles['Recency'][.2]:
            return 5
        elif x <= quintiles['Recency'][.4]:
            return 4
        elif x <= quintiles['Recency'][.6]:
            return 3
        elif x <= quintiles['Recency'][.8]:
            return 2
        else:
            return 1

    def fm_score(x, c):
        if x <= quintiles[c][.2]:
            return 1
        elif x <= quintiles[c][.4]:
            return 2
        elif x <= quintiles[c][.6]:
            return 3
        elif x <= quintiles[c][.8]:
            return 4
        else:
            return 5

    rfm['R'] = rfm['Recency'].apply(lambda x: r_score(x))
    rfm['F'] = rfm['Frequency'].apply(lambda x: fm_score(x, 'Frequency'))
    rfm['M'] = rfm['Monetary'].apply(lambda x: fm_score(x, 'Monetary'))

    return rfm


def show_rfm_distribution(rfm):
    fig = make_subplots(rows=3, cols=1, subplot_titles=('Recency', 'Frequency', 'Monetary'))
    for i, j in enumerate(['Recency', 'Frequency', 'Monetary']):
        fig.add_box(x=rfm[str(j)], row=i + 1, col=1, name=str(j))
    fig.update_layout(bargap=0.2, title='Boxplot for RFM Values')
    st.write(fig)

    return fig


def show_rfm_scatter_3d(rfm):
    fig = px.scatter_3d(rfm, x='Recency', y='Frequency', z='Monetary', color='Monetary')
    fig.update_layout(scene=dict(
        xaxis_title='Recency',
        yaxis_title='Frequency',
        zaxis_title='Monetary'), title='3D scatter of RFM Values')
    st.write(fig)

    return fig


def clean_data(rfm):
    new_df = rfm[['Recency', 'Frequency', 'Monetary']]
    z_scores = stats.zscore(new_df)
    abs_z_scores = np.abs(z_scores)
    filtered_entries = (abs_z_scores < 3).all(axis=1)
    new_df = new_df[filtered_entries]

    new_df = new_df.drop_duplicates()
    col_names = ['Recency', 'Frequency', 'Monetary']
    features = new_df[col_names]
    scaler = StandardScaler().fit(features.values)
    features = scaler.transform(features.values)
    scaled_features = pd.DataFrame(features, columns=col_names)

    return scaled_features, scaler


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


def customer_segmentation_model(scaled_features, nb_clusters):
    kmeans = KMeans(n_clusters=nb_clusters, init='k-means++', n_init='auto')
    scaled_features = pd.DataFrame(scaled_features, columns=['Recency', 'Frequency', 'Monetary'])
    kmeans.fit(scaled_features.values)
    st.success(
        'Silhouette score : ' + str(round(silhouette_score(scaled_features, kmeans.labels_, metric='euclidean'), 2)))

    pred = kmeans.predict(scaled_features)
    scaled_features['Cluster RFM'] = ['Cluster ' + str(i) for i in pred]

    avg_df = scaled_features.groupby(['Cluster RFM'], as_index=False).mean()

    scaler = MinMaxScaler()
    avg_df[['Recency', 'Frequency', 'Monetary']] = scaler.fit_transform(avg_df[['Recency', 'Frequency', 'Monetary']])

    return kmeans, avg_df, scaled_features


def show_rfm_clusters(avg_df, scaled_features):
    fig = go.Figure()
    for i in range(len(avg_df['Cluster RFM'])):
        fig.add_trace(go.Scatterpolar(
            r=[avg_df['Recency'][i], avg_df['Frequency'][i], avg_df['Monetary'][i]],
            theta=['Recency', 'Frequency', 'Monetary'],
            fill='toself',
            name='Cluster ' + str(i)
        ))
    fig.update_layout(title='Customer RFM Insights Radar')
    st.write(fig)

    bar_data = scaled_features['Cluster RFM'].value_counts()
    fig = px.bar(x=bar_data.index, y=bar_data.values, color=bar_data.values, title='Number of Customer in each Cluster')
    fig.update_layout(xaxis_title='Clusters', yaxis_title='Count')
    st.write(fig)
    return fig


def show_customer_segment_distribution(rfm):
    st.info('This RFM Segmentation is based on this PhD thesis (2021): '
            'https://dergipark.org.tr/tr/download/article-file/2343280', icon='ℹ️')

    rfm['RFM score'] = rfm['R'].map(str) + rfm['F'].map(str) + rfm['M'].map(str)
    rfm['RFM_count'] = rfm.groupby(['R', 'F', 'M'])['R'].transform('count')

    def label_rfm_segments(rfm_score):
        rfm_score = int(rfm_score)
        if (rfm_score >= 111) & (rfm_score <= 155):
            return 'Risky'

        elif (rfm_score >= 211) & (rfm_score <= 255):
            return 'Hold and improve'

        elif (rfm_score >= 311) & (rfm_score <= 353):
            return 'Potential loyal'

        elif ((rfm_score >= 354) & (rfm_score <= 454)) or ((rfm_score >= 511) & (rfm_score <= 535)) or (
                rfm_score == 541):
            return 'Loyal'

        elif (rfm_score == 455) or (rfm_score >= 542) & (rfm_score <= 555):
            return 'Star'

        else:
            return 'Other'

    rfm['Segment 1'] = rfm.apply(lambda x: label_rfm_segments(x['RFM score']), axis=1)
    rfm['size'] = np.ceil(rfm['RFM_count'] / 10) * 10

    colors_palette = {
        'Risky': '#29b09d',
        'Hold and improve': '#ff2b2b',
        'Potential loyal': '#904cd9',
        'Loyal': '#0068c9',
        'Star': '#ffd16a',
        'Other': 'gray'
    }

    fig_scatter = px.scatter_3d(rfm, x='R', y='F', z='M', color='Segment 1', size='RFM_count',
                                color_discrete_map=colors_palette, opacity=1, size_max=40)

    fig_scatter.update_layout(scene=dict(
        xaxis_title='Recency',
        yaxis_title='Frequency',
        zaxis_title='Monetary'), title='3D scatter of RFM Segments')
    st.write(fig_scatter)

    segments_counts = rfm['Segment 1'].value_counts().sort_values(ascending=False)
    fig_pie = px.pie(segments_counts, values=segments_counts.values, names=segments_counts.index,
                     color=segments_counts.index, color_discrete_map=colors_palette)
    fig_pie.update_layout(title='Proportion of RFM Segments')
    st.write(fig_pie)

    return fig_scatter, fig_pie


def show_customer_segment_distribution_rfm(rfm):
    legend = [
        ('#83c9ff', 'Hibernating'), ('#29b09d', 'At risk'), ('#ff8700', 'Can\'t lose them'),
        ('#7defa1', 'About to sleep'), ('#757d79', 'Need attention'), ('#0068c9', 'Loyal customers'),
        ('#ff2b2b', 'Promising'), ('#904cd9', 'Potential loyalists'), ('#ffabab', 'New customers'),
        ('#ffd16a', 'Champions')
    ]

    color_mapping = {
        '#83c9ff': [(1, 0), (1, 1), (0, 0), (0, 1)],
        '#29b09d': [(3, 0), (3, 1), (2, 0), (2, 1)],
        '#ff8700': [(4, 0), (4, 1)],
        '#7defa1': [(0, 2), (1, 2)],
        '#757d79': [(2, 2)],
        '#0068c9': [(4, 2), (4, 3), (3, 2), (3, 3)],
        '#ff2b2b': [(0, 3)],
        '#904cd9': [(2, 3), (1, 3), (2, 4), (1, 4)],
        '#ffabab': [(0, 4)],
        '#ffd16a': [(4, 4), (3, 4)]
    }

    fig_treemap = make_subplots(rows=5, cols=5, shared_yaxes=True,
                                subplot_titles=[f"F{i}, R{j}" for i in range(5, 0, -1) for j in range(1, 6)])

    for f in range(5):
        for r in range(5):
            filtered_data = rfm[(rfm['R'] == r + 1) & (rfm['F'] == f + 1)]['M']
            if not filtered_data.empty:
                y = filtered_data.value_counts().sort_index()
                x = y.index
                color = None
                for c, coords in color_mapping.items():
                    if (f, r) in coords:
                        color = c
                        break
                fig_treemap.add_trace(go.Bar(x=x, y=y, marker_color=color, showlegend=False),
                                      row=5 - f, col=r + 1)

    for color, name in legend:
        fig_treemap.add_trace(go.Bar(x=[None], y=[None], marker_color=color, showlegend=True, name=name))

    fig_treemap.update_layout(title="RFM Treemap")
    st.write(fig_treemap)

    colors = {
        'Hibernating': '#83c9ff',
        'At risk': '#29b09d',
        'Can\'t loose': '#ff8700',
        'About to sleep': '#7defa1',
        'Need attention': '#757d79',
        'Loyal customers': '#0068c9',
        'Promising': '#ff2b2b',
        'New customers': '#ffabab',
        'Potential loyalists': '#904cd9',
        'Champions': '#ffd16a'
    }

    segt_map = {
        r'[1-2][1-2]': 'Hibernating',
        r'[1-2][3-4]': 'At risk',
        r'[1-2]5': 'Can\'t loose',
        r'3[1-2]': 'About to sleep',
        r'33': 'Need attention',
        r'[3-4][4-5]': 'Loyal customers',
        r'41': 'Promising',
        r'51': 'New customers',
        r'[4-5][2-3]': 'Potential loyalists',
        r'5[4-5]': 'Champions'
    }

    rfm['Segment 2'] = rfm['R'].map(str) + rfm['F'].map(str)
    rfm['Segment 2'] = rfm['Segment 2'].replace(segt_map, regex=True)

    segments_counts = rfm['Segment 2'].value_counts().sort_values(ascending=False)

    fig_pie = px.pie(
        segments_counts,
        values=segments_counts.values,
        names=segments_counts.index,
        color=segments_counts.index,
        color_discrete_map=colors
    )
    fig_pie.update_layout(title='Proportion of RFM Segments')
    st.write(fig_pie)

    return fig_treemap, fig_pie


def segment_1_details(df):
    data = [['Star',
             'It is the customer group that makes purchases most frequently, most up-to-date and in the highest amounts. It is the customer group with the highest score in terms of purchase frequency and currency, and purchase amounts'],
            ['Loyal', 'It is a group of customers who buy frequently, recently, with high amounts.'],
            ['Potential loyal',
             'This is the customer group with lower purchase relevance compared to the loyal customer segment.'],
            ['Hold and improve',
             'This is the customer group with low frequency and up-to-dateness. The purchasing stability of this group is low.'],
            ['Risky', 'It is the customer group with the lowest purchase frequency and up-to-dateness.']]
    data = pd.DataFrame(data, columns=['Segment 1', 'Description'])
    data = pd.merge(data, df, on='Segment 1').set_index('Segment 1')
    st.dataframe(data)
    return data


def segment_2_details(df):
    data = [['Champions',
             'They are your best customers. These customers recently made a purchase, buy often and that too the most expensive / high-priced items from your store.',
             'Give rewards, build credibility, promote new products'],
            ['Loyal customers',
             'This category of customers may not have purchased very recently but they surely buy often and that too expensive / high-priced products.',
             'Take feedbacks and surveys, upsell your products, present bonuses'],
            ['Potential loyalist',
             'Potential loyalist customers, though don\'t buy on regular basis, they are recent buyers and spend a good amount on product purchases.',
             'Offer loyalty program, run contests, make them feel special'],
            ['New customers',
             'As the name suggests, they are the most recent buyers, purchased the lowest priced items and that too once or twice.',
             'Provide onboarding support, gift them discounts, build relationship'],
            ['Promising customers',
             'Those segment of customers are those that bought recently and purchased lowest priced items.',
             'Provide a free trial, create brand awareness, offer store credit'],
            ['Lost',
             'As the name suggests, you have almost lost these customers. They never came back. Also, their earlier purchases were the low-end products that too once or twice.',
             'Reconnect with them, do one last promotion, take feedback'],
            ['Need attention',
             'These customers may not have bought recently, but they spent a decent amount of money quite a few times.',
             'Offer combo products, get on call, introduce them to your new offerings'],
            ['About to sleep',
             'This type of customers did shop for your products but not very recently. Also, they don\'t purchase often and don\'t spend much.',
             'Share valuable resource, conduct a competitive analysis, update your products'],
            ['At risk',
             'These customers bought your products frequently, purchased high-priced products. But haven\'t made any purchase since a long time.',
             'Offer store credit, provide a wishlist, upgrade offers'],
            ['Can\'t lose them',
             'These customers were frequent buyers and purchased the most expensive/high-priced products but over the time they never came back.',
             'Tailor services, make a phone call, connect on social media'],
            ['Hibernating',
             'These customers purchased only low-end items, that too hardly once or twice and never came back.',
             'Decide if you want them back, review your product, send personalized campaign'],
            ]
    data = pd.DataFrame(data, columns=['Segment 2', 'Description', 'Strategies'])
    data = pd.merge(data, df, on='Segment 2').set_index('Segment 2')
    st.dataframe(data)
    return data


def rfm_main_function(df, snapshot_end_date, customers, directory, snapshot_start_date, sales_filter, customer_type):
    rfm = compute_rfm_segments(df, snapshot_end_date, sales_filter)

    col1, col2, col3, col4 = st.tabs(
        ['RFM Distribution', 'Customer Clusters using ML', 'Customer Segments using RFM scores', 'Download data'])

    with col1:
        st.subheader(f'Recency, Frequency, Monetary Distribution', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        show_rfm_distribution(rfm)
        show_rfm_scatter_3d(rfm)
    with col2:
        scaled_features, scaler = clean_data(rfm)
        st.subheader(f'Fine-tuning Models: Hyperparameter Optimization', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        elbow_method(scaled_features)
        nb_clusters = st.slider('Number of Clusters', 2, 12, 4)
        kmeans, average_clusters, scaled_features = customer_segmentation_model(scaled_features, nb_clusters)
        st.subheader(f'Results: RFM Clusters', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        show_rfm_clusters(average_clusters, scaled_features)
    with col3:
        st.subheader(f'Customer Segment Distribution - First approach', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        show_customer_segment_distribution(rfm)
        st.subheader(f'Customer Segment Distribution - Second approach', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        show_customer_segment_distribution_rfm(rfm)
    with col4:
        col_names = ['Recency', 'Frequency', 'Monetary']
        customer_cluster_list = []
        for customer_id in rfm['Customer_ID']:
            features = rfm[rfm['Customer_ID'] == customer_id][col_names]
            scaled_features = scaler.transform(features.values)
            customer_cluster = kmeans.predict(scaled_features)
            customer_cluster_list.append('Cluster ' + str(customer_cluster[0]))
        rfm['Cluster RFM'] = customer_cluster_list
        rfm = rfm.merge(customers[['Customer_ID', 'Customer_name']], on='Customer_ID')
        rfm['Customer_ID'] = rfm['Customer_ID'].astype(int)
        st.subheader(f'Details for all customers', divider='grey')
        st.info(f'Company: :blue[{directory}]' +
                f'\n\nData type: :blue[{sales_filter}]' +
                f'\n\nCustomer type: :blue[{customer_type}]' +
                f'\n\nDate range: :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}]', icon='ℹ️')
        rfm = rfm[['Customer_ID', 'Customer_name', 'Recency', 'Frequency', 'Monetary', 'R', 'F', 'M', 'Cluster RFM',
                   'Segment 1', 'Segment 2']].set_index('Customer_ID')
        st.dataframe(rfm, use_container_width=True)

        with st.expander('Details about the clusters'):
            st.info('The RFM values represent the average value within each cluster.')
            ml_clusters = rfm.groupby(['Cluster RFM'], as_index=True)[['Recency', 'Frequency', 'Monetary']].mean()
            st.dataframe(ml_clusters)

            segment_1_clusters = rfm.groupby(['Segment 1'])[['Recency', 'Frequency', 'Monetary']].mean()
            segment_1_details(segment_1_clusters)

            segment_2_clusters = rfm.groupby(['Segment 2'])[['Recency', 'Frequency', 'Monetary']].mean()
            segment_2_details(segment_2_clusters)

    return rfm, ml_clusters, segment_1_clusters, segment_2_clusters
