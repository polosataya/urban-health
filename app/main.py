import folium
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
from streamlit_folium import st_folium


# выводим центроиды полигонов
def get_lat_lon(geometry):
    lon = geometry.apply(lambda x: x.x if x.geom_type == 'Point' else x.centroid.x)
    lat = geometry.apply(lambda x: x.y if x.geom_type == 'Point' else x.centroid.y)
    return lat, lon

def create_choropleth(data, json, columns, legend_name, feature, bins):
    lat, lon = get_lat_lon(data['geometry'])
    m = folium.Map(location=[sum(lat)/len(lat), sum(lon)/len(lon)], zoom_start=11, tiles='cartodbpositron')
    
    folium.Choropleth(
        geo_data=json,
        name="choropleth",
        data=data,
        columns=columns,
        key_on="feature.id",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_name,
        nan_fill_color = 'black',
        bins = bins
    ).add_to(m)
    folium.LayerControl().add_to(m)

    return m

#=======================================================================================

itog_table = pd.read_csv('data/ekb.csv')

negative = st.selectbox('Отрицательные объекты', ('e-cigarette', 'tobacco', 'bar', 'biergarten', 'wine', 'alcohol', 'beverages', 'fast_food', 'food_court'))

# подготовим данные 
itog_table['geometry'] = itog_table['geometry'].astype(str) #для groupby
itog_table['id'] = itog_table['id'].astype(str) #для Choropleth
agg_all = itog_table.groupby(['geometry','type','id'], as_index=False).agg({'lat':'count'}).rename(columns={'lat':'counts'})
agg_all['geometry']=agg_all['geometry'].apply(wkt.loads) #возвращаем формат геометрий

agg_all_cafe = agg_all[agg_all['type']==negative][["geometry","counts",'id']]
agg_all_cafe['id'] = agg_all_cafe['id'].astype(str)
data_geo_1 = gpd.GeoSeries(agg_all_cafe.set_index('id')["geometry"]).to_json()

m = create_choropleth(agg_all_cafe, data_geo_1, ["id","counts"], 'Object counts', 'counts', 5)

# call to render Folium map in Streamlit
st_data = st_folium(m, width=725)
