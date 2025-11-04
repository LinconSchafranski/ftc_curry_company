# Libraries
import pandas as pd
import plotly.express as px
import plotly.io as pio
from haversine import haversine
import streamlit as st
import datetime
from PIL import Image
import folium
from streamlit_folium import folium_static

# Import dataset
df = pd.read_csv('train.csv')

# Limpeza dos dados
df1 = df.copy()

# Retirada de espaços em branco
colunas_texto = ['ID', 'Road_traffic_density', 'Type_of_order', 'Type_of_vehicle', 'City', 'multiple_deliveries', 'Delivery_person_Age', 'Festival']

for coluna in colunas_texto:
    df1[coluna] = df1[coluna].str.strip()

# Removendo linhas com valores inválidos ('NaN' como string) nas colunas
# 'Delivery_person_Age', 'Road_traffic_density' e 'City'
df1 = df1[df1['Road_traffic_density'] != 'NaN']
df1 = df1[df1['City'] != 'NaN']
df1 = df1[df1['Delivery_person_Age'] != 'NaN']
df1 = df1[df1['multiple_deliveries'] != 'NaN']
df1 = df1[df1['Festival'] != 'NaN']

# Convertendo multiple_deliveries e Delivery_person_Age de texto para numero inteiro (int)
df1['Delivery_person_Age'] = pd.to_numeric(df1['Delivery_person_Age'])
df1['multiple_deliveries'] = pd.to_numeric(df1['multiple_deliveries'])


#Converter Lat/Long para numérico e tratar strings inválidas como nulo (NaN)
df1['Delivery_location_latitude'] = pd.to_numeric(df1['Delivery_location_latitude'], errors="coerce")
df1['Delivery_location_longitude'] = pd.to_numeric(df1['Delivery_location_longitude'], errors="coerce")

#Remover linhas onde Lat/Long são nulas (NaN) após a conversão
df1.dropna(subset=['Delivery_location_latitude', 'Delivery_location_longitude'], inplace=True)

# Convertendo para tipo data
df1['Order_Date'] = pd.to_datetime(df1['Order_Date'], format="%d-%m-%Y")

# Convertendo para tipo numérico
df1['Delivery_person_Age'] = pd.to_numeric(df1['Delivery_person_Age'], errors="coerce")
df1['Delivery_person_Ratings'] = pd.to_numeric(df1['Delivery_person_Ratings'], errors="coerce")

# 7. Limpando a coluna de time taken
df1['Time_taken(min)'] = df1['Time_taken(min)'].apply(lambda x: x.split('(min) ')[1])
df1['Time_taken(min)'] = df1['Time_taken(min)'].astype(int)


#===================================================================
#Barra Lateral
#===================================================================


st.header('Marketplace - Visão Cliente')

image_path = '/home/lincon/repos/ftc_analisando_dados_com_python/logo.png'
image = Image.open(image_path)
st.sidebar.image(image, width=230)

st.sidebar.markdown('# Cury Company')
st.sidebar.markdown('## Fastest Delivery in Town')
st.sidebar.markdown("""___""")

st.sidebar.markdown('## Selecione uma data limite')
date_slider = st.sidebar.slider('Até qual valor?', value=datetime.datetime(2022, 3, 13), min_value=datetime.datetime(2022, 2, 11), max_value=datetime.datetime(2022, 4, 6), format='DD-MM-YYYY')

st.sidebar.markdown("""___""")

traffic_options = st.sidebar.multiselect('Quais as condições do trânsito' , ['Low', 'Medium', 'High', 'Jam'], default=['Low', 'Medium', 'High', 'Jam'])

st.sidebar.markdown("""___""")
st.sidebar.markdown('### Powered by Lincon Schafranski')

#Filtro de data
linhas_selecionadas = df1['Order_Date'] < date_slider
df1 = df1.loc[linhas_selecionadas, :]

#Filtro de transito
linhas_selecionadas = df1['Road_traffic_density'].isin(traffic_options)
df1 = df1.loc[linhas_selecionadas, :]
st.dataframe(df1)


#===================================================================
#Layout no Streamlit
#===================================================================

tab1, tab2, tab3 = st.tabs(['Visão Gerencial', 'Visão Tática', 'Visão Geográfica'])

with tab1:
    with st.container():
        # Order Metric
        st.markdown('## Orders by day')
        coluns = ['ID', 'Order_Date']
        df_aux = df1.loc[: , coluns].groupby('Order_Date').count().reset_index()
        fig = px.bar(df_aux, x='Order_Date', y='ID')
        st.plotly_chart(fig , use_container_width=True)
        
    with st.container():
        col1 , col2 = st.columns(2)
        with col1:
            
            st.header('Traffic Order Share')
            columns = ['ID', 'Road_traffic_density']
            df_aux = df1.loc[:, columns].groupby( 'Road_traffic_density').count().reset_index()
            df_aux['perc_ID'] = 100 * ( df_aux['ID'] / df_aux['ID'].sum() )
            fig = px.pie( df_aux, values='perc_ID', names='Road_traffic_density')
            st.plotly_chart(fig , use_container_width=True)
            
        
        with col2:
            st.header('Traffic Order City')
            coluns = ['ID', 'City' , 'Road_traffic_density']
            df_aux = df1.loc[: , coluns].groupby(['City' , 'Road_traffic_density']).count().reset_index()
            fig = px.scatter(df_aux, x='Road_traffic_density', y='City', size='ID')
            st.plotly_chart(fig , use_container_width=True)


    
with tab2:
    with st.container():
        st.markdown('# Order by Week')
        df1['Week_of_year'] = df1['Order_Date'].dt.strftime("%U")
        coluns = ['Week_of_year' , 'ID']
        df_aux = df1.loc[: , coluns].groupby('Week_of_year').count().reset_index()
    
        fig = px.line(df_aux , x='Week_of_year', y='ID')
        st.plotly_chart( fig, use_container_width=True)
    
    with st.container():
        st.markdown('# Order Share by Week')
        df1['Week_of_year'] = df1['Order_Date'].dt.strftime("%U")
        df_aux1 = df1.loc[: , ['Week_of_year' ,'ID']].groupby('Week_of_year').count().reset_index()
        df_aux2 = df1.loc[: , ['Week_of_year', 'Delivery_person_ID']].groupby('Week_of_year').nunique().reset_index()
        df_aux =  pd.merge(df_aux1 , df_aux2, how='inner')
        df_aux['order_by_delivery'] = df_aux['ID'] /df_aux['Delivery_person_ID']

        # Gerando o gráfico
        fig = px.line(
            df_aux,     # DataFrame com os dados
            x="Week_of_year",   # eixo X
            y="order_by_delivery",   # eixo Y
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown('# Country Map')
    columns = ['City', 'Road_traffic_density', 'Delivery_location_latitude', 'Delivery_location_longitude']
    columns_groupby = ['City', 'Road_traffic_density']
    data_plot = df1.loc[:, columns].groupby( columns_groupby ).median().reset_index()
    data_plot = data_plot[data_plot['City'] != 'NaN']
    data_plot = data_plot[data_plot['Road_traffic_density'] != 'NaN']
    # Desenhar o mapa
    map = folium.Map( zoom_start=11 )
    for index, location_info in data_plot.iterrows():
        folium.Marker( [location_info['Delivery_location_latitude'], location_info['Delivery_location_longitude']], popup=location_info[['City', 'Road_traffic_density']] ).add_to( map )
    folium_static(map , width=1024 , height=600)









