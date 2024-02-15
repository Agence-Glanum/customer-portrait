import streamlit as st
import plotly.express as px
import json
import pandas as pd


def map_function(address, customers):
    with open('./utils/Geo/GlobalMap/countries.json') as c:
        countries_data = json.load(c)
    with open('./utils/Geo/GlobalMap/dpts.json', 'r') as f:
        data = json.load(f)

    corsica = pd.read_csv("utils/Geo/base-officielle-codes-postaux.csv")
    zip_codes = address.drop_duplicates()

    mask = (zip_codes['Country'] != 'FR') & (~zip_codes['Country'].isnull())
    zip_codes.loc[mask, 'Zip_code'] = zip_codes.loc[mask, 'Country']
    zip_codes = zip_codes.dropna(subset=['Zip_code', 'City', 'Country'])

    selected_entries = corsica[corsica['code_commune_insee'].str.startswith(('2A', '2B'))]
    selected_entries["nom_de_la_commune"] = selected_entries["nom_de_la_commune"].str.replace(" ", "-").str.capitalize()
    selected_entries["code_commune_insee"] = selected_entries["code_commune_insee"].str[:2]
    zip_codes['Zip_code'] = zip_codes['Zip_code'].astype(str)
    selected_entries['code_postal'] = selected_entries['code_postal'].astype(str)
    zip_codes['Zip_code'] = zip_codes.apply(
        lambda row: selected_entries.loc[
            (selected_entries['code_postal'] == row['Zip_code']), 'code_commune_insee'].values[0]
        if any(selected_entries['code_postal'] == row['Zip_code'])
        else row['Zip_code'],
        axis=1
    )

    zip_codes["Zip_code"] = zip_codes["Zip_code"].str[:2]
    result = zip_codes.groupby('Zip_code').size().reset_index(name='Count')
    result['Zip_code'] = result['Zip_code'].apply(lambda x: x[1:] if len(x) == 2 and x.startswith('0') else x)

    country_json_copie = list(countries_data.copy())
    gps_json_copie = list(data.copy())

    zip_coder = result['Zip_code'].unique()
    gps_json_copie = [item for item in gps_json_copie if item['numero'] in zip_coder]
    country_json_copie = [item for item in country_json_copie if item['alpha2'] in zip_coder]

    df_gps = pd.json_normalize(gps_json_copie)
    df_countries = pd.json_normalize(country_json_copie)
    df_countries_renamed = df_countries.rename(columns={"latitude": "lat", "longitude": "lng", "alpha2": "numero"})

    result['Zip_code'] = result['Zip_code'].astype(str)

    merged_df_dpts = pd.merge(df_gps, result, how='left', left_on='numero', right_on='Zip_code')
    merged_df_dpts_dropped = merged_df_dpts.drop("nomLong", axis=1)

    merged_df_countries = pd.merge(df_countries_renamed, result, how='left', left_on='numero', right_on='Zip_code')
    merged_df_countries_dropped = merged_df_countries.drop(columns=["numeric", "alpha3"])
    merged_df_countries_dropped = merged_df_countries_dropped.rename(columns={"country": "nomShort"})
    result = pd.concat([merged_df_countries_dropped, merged_df_dpts_dropped], ignore_index=True)

    fig = px.density_mapbox(result,
                            height=600,
                            lat='lat',
                            lon='lng',
                            z='Count',
                            color_continuous_scale="viridis",
                            range_color=[0, 12],
                            radius=10,
                            center={"lat": 46.6031, "lon": 1.7394}, zoom=2,
                            mapbox_style="carto-positron")
    fig.update_layout(coloraxis_showscale=False)
    st.write(fig)

    return
