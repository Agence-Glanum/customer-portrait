import pandas as pd
from scipy import stats
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
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


def show_rfm_distribution(rfm, directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter):
    st.subheader(
        f'Recency, Frequency, Monetary Distribution for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]',
        divider='grey')
    fig = make_subplots(rows=3, cols=1, subplot_titles=("Recency", "Frequency", "Monetary"))
    for i, j in enumerate(['Recency', 'Frequency', 'Monetary']):
        fig.add_box(x=rfm[str(j)], row=i + 1, col=1, name=str(j))
    fig.update_layout(bargap=0.2)
    st.write(fig)

    return


def show_rfm_scatter_3d(rfm):
    fig = px.scatter_3d(rfm, x='Recency', y='Frequency', z='Monetary', color='Monetary')
    fig.update_layout(scene=dict(
        xaxis_title='Recency',
        yaxis_title='Frequency',
        zaxis_title='Monetary'))
    st.write(fig)

    return


def clean_data(rfm):
    print("Before cleaning the data, we have ", rfm.shape)

    new_df = rfm[['Recency', 'Frequency', 'Monetary']]
    z_scores = stats.zscore(new_df)
    abs_z_scores = np.abs(z_scores)
    filtered_entries = (abs_z_scores < 3).all(axis=1)
    new_df = new_df[filtered_entries]

    print("After cleaning the data, we have ", new_df.shape)

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
        kmeans = KMeans(n_clusters=cluster, init='k-means++')
        kmeans.fit(scaled_features)
        SSE.append(kmeans.inertia_)

    frame = pd.DataFrame({'Cluster': range(1, 12), 'SSE': SSE})
    st.write(px.line(x=frame['Cluster'], y=frame['SSE']))
    return


def customer_segmentation_model(scaled_features, nb_clusters, directory, snapshot_start_date, snapshot_end_date,
                                transformed_sales_filter):
    kmeans = KMeans(n_clusters=nb_clusters, init='k-means++')
    kmeans.fit(scaled_features)

    st.write("Silhouette score : ", round(silhouette_score(scaled_features, kmeans.labels_, metric='euclidean'), 2))

    pred = kmeans.predict(scaled_features)
    scaled_features['Cluster RFM'] = ['Cluster ' + str(i) for i in pred]

    avg_df = scaled_features.groupby(['Cluster RFM'], as_index=False).mean()

    scaler = MinMaxScaler()
    avg_df[['Recency', 'Frequency', 'Monetary']] = scaler.fit_transform(avg_df[['Recency', 'Frequency', 'Monetary']])

    st.subheader(
        f'RFM Clusters for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]',
        divider='grey')
    fig = go.Figure()
    for i in range(len(avg_df['Cluster RFM'])):
        fig.add_trace(go.Scatterpolar(
            r=[avg_df['Recency'][i], avg_df['Frequency'][i], avg_df['Monetary'][i]],
            theta=['Recency', 'Frequency', 'Monetary'],
            fill='toself',
            name='Cluster ' + str(i)
        ))
    st.write(fig)

    bar_data = scaled_features['Cluster RFM'].value_counts()
    fig = px.bar(x=bar_data.index, y=bar_data.values, color=bar_data.values, title='Number of Customer in each Cluster')
    st.write(fig)

    return kmeans, avg_df


def show_customer_segment_distribution(rfm):
    st.info(
        'This RFM Segmentation is based on this PhD thesis (2021): https://dergipark.org.tr/tr/download/article-file/2343280',
        icon="ℹ️")

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

    st.subheader('Customer clustering based on R, F and M')

    colors_palette = {
        'Risky': '#29b09d',
        'Hold and improve': '#ff2b2b',
        'Potential loyal': '#904cd9',
        'Loyal': '#0068c9',
        'Star': '#ffd16a',
        'Other': 'gray'
    }

    fig = px.scatter_3d(rfm, x='R', y='F', z='M', color='Segment 1', size='RFM_count',
                        color_discrete_map=colors_palette, opacity=1, size_max=40)

    fig.update_layout(scene=dict(
        xaxis_title='Recency',
        yaxis_title='Frequency',
        zaxis_title='Monetary'))

    st.write(fig)

    segments_counts = rfm['Segment 1'].value_counts().sort_values(ascending=False)
    fig_pie = px.pie(segments_counts, values=segments_counts.values, names=segments_counts.index,
                     color=segments_counts.index, color_discrete_map=colors_palette)
    st.write(fig_pie)



    return


def show_customer_segment_distribution_rfm(rfm):
    colors = {
        'Hibernating': '#83c9ff',
        'At risk': '#29b09d',
        "Can't loose": '#ff8700',
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
        r'[1-2]5': "Can't loose",
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

    fig = px.pie(
        segments_counts,
        values=segments_counts.values,
        names=segments_counts.index,
        color=segments_counts.index,
        color_discrete_map=colors
    )

    st.subheader('Customer clustering based on R and F')
    st.write(fig)

    fig2, axes = plt.subplots(nrows=5, ncols=5, sharex=False, sharey=True, figsize=(15, 15))
    r_range = range(1, 6)
    f_range = range(1, 6)

    for f in f_range:
        for r in r_range:
            y = rfm[(rfm['R'] == r) & (rfm['F'] == f)]['M'].value_counts().sort_index()
            x = y.index
            ax = axes[5 - f, r - 1]
            bars = ax.bar(x, y, color='white')
            ax.set_xticks(x)
            if f == 1:
                if r == 3:
                    ax.set_xlabel('{}\nR'.format(r), va='top', color='black')
                else:
                    ax.set_xlabel('{}\n'.format(r), va='top', color='black')
            if r == 1:
                if f == 3:
                    ax.set_ylabel('F\n{}'.format(f), color='black')
                else:
                    ax.set_ylabel(f, color='black')
            ax.set_frame_on(False)
            ax.tick_params(left=False, labelleft=False, bottom=False)
            ax.tick_params(axis='x', colors='black')

            for bar in bars:
                value = bar.get_height()
                if value == y.max():
                    bar.set_color('firebrick')
                ax.text(bar.get_x() + bar.get_width() / 2,
                        value,
                        int(value),
                        ha='center',
                        va='bottom',
                        color='black')

    st.subheader(f'Monetary value distribution for each R and F value')

    def legend_function(list_, color_):
        for element in list_:
            axes[element].set_frame_on(True)
            axes[element].set_facecolor(color_)
            axes[element].grid(visible=False)

    legend_function([(3, 0), (3, 1), (4, 0), (4, 1)], "#83c9ff")
    legend_function([(1, 0), (1, 1), (2, 0), (2, 1)], "#29b09d")
    legend_function([(0, 0), (0, 1)], "#ff8700")
    legend_function([(4, 2), (3, 2)], "#7defa1")
    legend_function([(2, 2)], "#757d79")
    legend_function([(0, 2), (0, 3), (1, 2), (1, 3)], "#0068c9")
    legend_function([(4, 3)], "#ff2b2b")
    legend_function([(2, 3), (3, 3), (2, 4), (3, 4)], "#904cd9")
    legend_function([(4, 4)], "#ffabab")
    legend_function([(0, 4), (1, 4)], "#ffd16a")

    legend_handles = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=label)
        for color, label in [("#83c9ff", "Hibernating"), ("#29b09d", "At risk"), ("#ff8700", "Can't lose them"),
                             ("#7defa1", "About to sleep"), ("#757d79", "Need attention"),
                             ("#0068c9", "Loyal customers"),
                             ("#ff2b2b", "Promising"), ("#904cd9", "Potential loyalists"), ("#ffabab", "New customers"),
                             ("#ffd16a", "Champions")]]

    fig2.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.1, 1.05))
    st.write(fig2)

    return


def segment_1_details(df):
    data = [["Star",
             "It is the customer group that makes purchases most frequently, most up-to-date and in the highest amounts. It is the customer group with the highest score in terms of purchase frequency and currency, and purchase amounts"],
            ["Loyal", "It is a group of customers who buy frequently, recently, with high amounts."],
            ["Potential loyal",
             "This is the customer group with lower purchase relevance compared to the loyal customer segment."],
            ["Hold and improve",
             "This is the customer group with low frequency and up-to-dateness. The purchasing stability of this group is low."],
            ["Risky", "It is the customer group with the lowest purchase frequency and up-to-dateness."]]
    data = pd.DataFrame(data, columns=['Segment 1', 'Description'])
    data = pd.merge(data, df, on='Segment 1')
    st.table(data)
    return


def segment_2_details(df):
    data = [["Champions",
             "They are your best customers. These customers recently made a purchase, buy often and that too the most expensive / high-priced items from your store.",
             "Give rewards, build credibility, promote new products"],
            ["Loyal customers",
             "This category of customers may not have purchased very recently but they surely buy often and that too expensive / high-priced products.",
             "Take feedbacks and surveys, upsell your products, present bonuses"],
            ["Potential loyalist",
             "Potential loyalist customers, though don't buy on regular basis, they are recent buyers and spend a good amount on product purchases.",
             "Offer loyalty program, run contests, make them feel special"],
            ["New customers",
             "As the name suggests, they are the most recent buyers, purchased the lowest priced items and that too once or twice.",
             "Provide onboarding support, gift them discounts, build relationship"],
            ["Promising customers",
             "Those segment of customers are those that bought recently and purchased lowest priced items.",
             "Provide a free trial, create brand awareness, offer store credit"],
            ["Lost",
             "As the name suggests, you have almost lost these customers. They never came back. Also, their earlier purchases were the low-end products that too once or twice.",
             "Reconnect with them, do one last promotion, take feedback"],
            ["Need attention",
             "These customers may not have bought recently, but they spent a decent amount of money quite a few times.",
             "Offer combo products, get on call, introduce them to your new offerings"],
            ["About to sleep",
             "This type of customers did shop for your products but not very recently. Also, they don't purchase often and don't spend much.",
             "Share valuable resource, conduct a competitive analysis, update your products"],
            ["At risk",
             "These customers bought your products frequently, purchased high-priced products. But haven't made any purchase since a long time.",
             "Offer store credit, provide a wishlist, upgrade offers"],
            ["Can't lose them",
             "These customers were frequent buyers and purchased the most expensive/high-priced products but over the time they never came back.",
             "Tailor services, make a phone call, connect on social media"],
            ["Hibernating",
             "These customers purchased only low-end items, that too hardly once or twice and never came back.",
             "Decide if you want them back, review your product, send personalized campaign"],
            ]
    data = pd.DataFrame(data, columns=['Segment 2', 'Description', 'Strategies'])
    data = pd.merge(data, df, on='Segment 2')
    st.table(data)
    return


def rfm_main_function(df, snapshot_end_date, customers, directory, snapshot_start_date, transformed_sales_filter):
    rfm = compute_rfm_segments(df, snapshot_end_date, transformed_sales_filter)

    col1, col2, col3, col4 = st.tabs(
        ["RFM Distribution", "Customer Clusters using ML", "Customer Segments using RFM scores", "Data"])

    with col1:
        show_rfm_distribution(rfm, directory, snapshot_start_date, snapshot_end_date, transformed_sales_filter)
        show_rfm_scatter_3d(rfm)
    with col2:
        scaled_features, scaler = clean_data(rfm)
        st.subheader(
            f"Elbow method for optimal number of Clusters for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]",
            divider='grey')
        elbow_method(scaled_features)
        nb_clusters = st.slider('Number of Clusters', 2, 12, 4)
        kmeans, average_clusters = customer_segmentation_model(scaled_features, nb_clusters, directory,
                                                               snapshot_start_date, snapshot_end_date,
                                                               transformed_sales_filter)
    with col3:
        st.subheader(
            f'Customer Segment Distribution - First approach for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]',
            divider='grey')
        show_customer_segment_distribution(rfm)
        st.subheader(
            f'Customer Segment Distribution - Second approach for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]',
            divider='grey')
        show_customer_segment_distribution_rfm(rfm)
    with col4:
        col_names = ['Recency', 'Frequency', 'Monetary']
        customer_cluster_list = []
        for customer_id in rfm['Customer_ID']:
            features = rfm[rfm['Customer_ID'] == customer_id][col_names]
            scaled_features = scaler.transform(features.values)
            customer_cluster = kmeans.predict(scaled_features)
            customer_cluster_list.append(customer_cluster[0])
        rfm['Cluster RFM'] = customer_cluster_list
        rfm = rfm.merge(customers[['Customer_ID', 'Customer_name']], on='Customer_ID')
        rfm['Customer_ID'] = rfm['Customer_ID'].astype(int)
        # customer_id_rfm = st.selectbox('Select a customer',
        #                                (rfm['Customer_ID'].astype(str) + ' - ' + rfm['Customer_name']))
        # customer_id_rfm = int(customer_id_rfm.split(' - ')[0])
        # st.subheader(
        #             f"All the details for each Customer for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]",
        #             divider='grey')
        # st.dataframe(rfm[rfm['Customer_ID'] == customer_id_rfm], use_container_width=True)
        st.subheader(
            f"Details for all customers for company :blue[{directory}], from :blue[{snapshot_start_date}] to :blue[{snapshot_end_date}], based on :blue[{transformed_sales_filter}]",
            divider='grey')
        rfm = rfm[['Customer_ID', 'Customer_name', 'Recency', 'Frequency', 'Monetary', 'R', 'F', 'M', 'Cluster RFM', 'Segment 1', 'Segment 2']]
        st.dataframe(rfm, use_container_width=True)

        with st.expander("ML Clusters details"):
            st.write('The average of the Recency, Frequency, Monetary values for each cluster')
            ml_clusters = rfm.groupby(['Cluster RFM'], as_index=True)[['Recency', 'Frequency', 'Monetary']].mean()
            st.dataframe(ml_clusters)

        with st.expander("RFM Segments using approach 1 details"):
            segment_1_cluters = rfm.groupby(['Segment 1'], as_index=True)[['Recency', 'Frequency', 'Monetary']].mean()
            segment_1_details(segment_1_cluters)

        with st.expander("RFM Segments using approach 2 details"):
            segment_2_cluters = rfm.groupby(['Segment 2'], as_index=True)[['Recency', 'Frequency', 'Monetary']].mean()
            segment_2_details(segment_2_cluters)

    return rfm, ml_clusters, segment_1_cluters, segment_2_cluters
