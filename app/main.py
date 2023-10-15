import folium
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
from folium.plugins import HeatMap
from streamlit_folium import st_folium

st.set_page_config(page_title="Влияние городской инфраструктуры на здоровье'",
                   page_icon="❤️", layout="wide", initial_sidebar_state="expanded",
                   menu_items={'Get Help': None, 'Report a bug': None, 'About': None})

hide_streamlit_style = """<style>#MainMenu {visibility: hidden;}footer {visibility: hidden;}</style>"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

#=======================================================================================================================
# Загрузка данных
@st.cache_data
def load_data(filenames):
    data = pd.concat([pd.read_csv(f) for f in filenames], ignore_index=True)
    return data

# Вспомогательная функция: выводим центроиды полигонов
def get_lat_lon(geometry):
    lon = geometry.apply(lambda x: x.x if x.geom_type == 'Point' else x.centroid.x)
    lat = geometry.apply(lambda x: x.y if x.geom_type == 'Point' else x.centroid.y)

    return lat, lon

# Вспомогательная функция: создание слоя тепловой карты
def create_heatmap_layer(data, lat_lon_feature):
    heatmap_layer = HeatMap(data[lat_lon_feature].groupby(lat_lon_feature[0:2]).sum().reset_index().values.tolist(),
                            radius=70, min_opacity=0.05, blur=30)
    return heatmap_layer

# Основная функция: создание карты хороплет
def create_choropleth(data, json, columns, legend_name, feature, bins, loc_def, table_people, colors):
    lat, lon = get_lat_lon(data['geometry'])

    if len(lat) > 0 and len(lon) > 0:  # Проверяем, что есть данные
        m = folium.Map(location=loc_def, zoom_start=11, tiles='cartodbpositron')

        style_function = lambda x: {'fillColor': '#ffffff', 'color': '#000000', 'fillOpacity': 0.1, 'weight': 0.2}
        highlight_function = lambda x: {'fillColor': '#0000ff', 'color': '#0000ff', 'fillOpacity': 0.5, 'weight': 0.2}

        g = folium.GeoJson(json, style_function=style_function, control=False, highlight_function=highlight_function,
                           tooltip=folium.GeoJsonTooltip(fields=['id','counts'], aliases=['ID','Counts'], localize=True))

        g.add_child(folium.GeoJsonTooltip(['id','counts'], aliases=['ID','Counts'],localize=True))

        folium.Choropleth(geo_data=json, name="choropleth", data=data, columns=columns, key_on="feature.properties.id",
            fill_color=colors, fill_opacity=0.7, line_opacity=0.2, legend_name=legend_name, nan_fill_color='black',
            bins=bins).add_to(m)

        # Используем create_heatmap_layer, чтобы получить тепловую карту в виде слоя
        heatmap_layer = create_heatmap_layer(table_people, ['lat', 'lon', 'count_people'])
        heatmap_layer.add_to(m)  # Добавить тепловую карту как слой на карту m

        m.add_child(g)

        folium.LayerControl().add_to(m)
    else:
        # Создать пустую карту без слоев, если нет данных
        m = folium.Map(location=loc_def, zoom_start=11, tiles='cartodbpositron')
        st.warning("Нет данных для отображения на карте")

    return m

#=======================================================================================================================

choice_dict = {"Спорт": ['swimming_pool', 'stadium','horse_riding', 'fitness_centre', 'sports_hall', 'ice_rink', 'park', 'pitch','sports_centre', 'stadium', 'track' ] , "Дорожки": ['cycleway', 'footway'], "Здоровая пища": ['marketplace', 'greengrocer', 'farm'], "Алкоголь": ['bar', 'biergarten', 'pub', 'wine', 'alcohol', 'beverages'], "Табак": ['e-cigarette', 'tobacco'], "Нездоровая пища": ['fast_food', 'food_court']}

# Загрузка данных
data_table = load_data(['app/data/ekb.csv', "app/data/tula.csv", "app/data/cochi.csv"])
data_people = load_data(['app/data/ekb_people.csv', "app/data/tula_people.csv", "app/data/cochi_people.csv"])

data_table['geometry'] = data_table['geometry'].astype(str) # для groupby
data_table['id'] = data_table['id'].astype(str) # для Choropleth

#=======================================================================================================================

tab = st.radio("Выберите", ("Положительные объекты", "Отрицательные объекты"), horizontal=True)

if tab == "Положительные объекты":
    choice = st.selectbox('Объекты', ['Спорт', 'Дорожки', 'Здоровая пища'])
    colors = "YlGn"

elif tab == "Отрицательные объекты":
    choice = st.selectbox('Объекты', ['Алкоголь', 'Табак', 'Нездоровая пища'])
    colors = "YlOrRd"

col1, col2 = st.columns(2)

with col1:
    city1 = st.selectbox('Город1', ['Екатеринбург', 'Сочи', 'Тула'])
    if city1 == 'Екатеринбург':
        itog_table1 = data_table[data_table["city"]=="Екатеринбург"]
        table_people1 = data_people[data_people["city"]=="Екатеринбург"]
        loc_def1 = [56.8519 , 60.6122]
    elif city1 == 'Сочи':
        itog_table1 = data_table[data_table["city"]=="Сочи"]
        table_people1 = data_people[data_people["city"]=="Сочи"]
        loc_def1 = [43.5992 , 39.7257]
    elif city1 == 'Тула':
        itog_table1 = data_table[data_table["city"]=="Тула"]
        table_people1 = data_people[data_people["city"]=="Тула"]
        loc_def1 = [54.1961 , 37.6182]

    # Карта
    agg_all1 = itog_table1[itog_table1['type'].isin(choice_dict[choice])]
    agg_all_1 = agg_all1.groupby(['geometry','id'], as_index=False).agg(counts=('lat','count'))
    agg_all_1['geometry'] = agg_all_1['geometry'].apply(wkt.loads) # возвращаем формат геометрий
    agg_all_1['id'] = agg_all_1['id'].astype(str)
    data_geo_1 = gpd.GeoDataFrame(agg_all_1, geometry='geometry').to_json()

    m1 = create_choropleth(agg_all_1, data_geo_1, ["id","counts"], 'Object counts', 'counts', 5, loc_def1, table_people1, colors)
    # вызов для отображения карты Folium в Streamlit
    st_data1 = st_folium(m1, width=725)

with col2:
    city2 = st.selectbox('Город2', ['Сочи', 'Тула', 'Екатеринбург'])
    if city2 == 'Екатеринбург':
        itog_table2 = data_table[data_table["city"]=="Екатеринбург"]
        table_people2 = data_people[data_people["city"]=="Екатеринбург"]
        loc_def2 = [56.8519 , 60.6122]
    elif city2 == 'Сочи':
        itog_table2 = data_table[data_table["city"]=="Сочи"]
        table_people2 = data_people[data_people["city"]=="Сочи"]
        loc_def2 = [43.5992 , 39.7257]
    elif city2 == 'Тула':
        itog_table2 = data_table[data_table["city"]=="Тула"]
        table_people2 = data_people[data_people["city"]=="Тула"]
        loc_def2 = [54.1961 , 37.6182]

    # Карта
    agg_all2 = itog_table2[itog_table2['type'].isin(choice_dict[choice])]
    agg_all_2 = agg_all2.groupby(['geometry','id'], as_index=False).agg(counts=('lat','count'))
    agg_all_2['geometry'] = agg_all_2['geometry'].apply(wkt.loads) # возвращаем формат геометрий
    agg_all_2['id'] = agg_all_2['id'].astype(str)
    data_geo_2 = gpd.GeoDataFrame(agg_all_2, geometry='geometry').to_json()

    m2 = create_choropleth(agg_all_2, data_geo_2, ["id","counts"], 'Object counts', 'counts', 5, loc_def2, table_people2, colors)
    # вызов для отображения карты Folium в Streamlit
    st_data2 = st_folium(m2, width=725)