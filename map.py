import geopandas as gpd
import pandas as pd
import json
import folium
import os

def clean_data(address):
    df = address.loc[address['Address_type'] == 'delivery']
    df = df.groupby('City')['Customer_ID'].count().reset_index()
    df.rename(columns={'Customer_ID': 'Customer_Count'}, inplace=True)
    return df

def map_geodataframe(address):
    geojson_path = os.path.abspath('data/Geo/arrondissements.geojson')
    with open(geojson_path, 'r') as jsonFile:
        data = json.load(jsonFile)
        geozips = []
        df = clean_data(address)
        for i in range(len(data['features'])):
            if data['features'][i]['properties']['nom'] in list(df['City'].unique()):
                geozips.append(data['features'][i])

        new_json = {'type': 'FeatureCollection', 'features': geozips}

        with open("data/Geo/updated-file.geojson", "w") as outfile:
            json.dump(new_json, outfile, indent=4)

        # Create and return a GeoDataFrame
        return gpd.GeoDataFrame.from_features(new_json['features'])

def create_map(address, city, mapped_feature, add_text=''):
    df = clean_data(address)
    la_geo = map_geodataframe(address)  # Get the GeoDataFrame directly
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=11)

    folium.Choropleth(
        geo_data=la_geo.to_json(),  # Convert GeoDataFrame to JSON
        fill_opacity=0.7,
        line_opacity=0.2,
        data=df,
        key_on='feature.properties.nom',
        columns=[city, mapped_feature],
        fill_color='RdYlGn',
        legend_name=add_text
    ).add_to(m)

    folium.LayerControl().add_to(m)
    m.save(outfile='data/Geo/' + mapped_feature + '_map.html')

# Assuming 'addresses' is defined somewhere in your code
# create_map(addresses, 'Zip_code', 'Customer_Count', 'Customer')
