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


st.header('Marketplace - Visão Entregadores')

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

climate_conditions = st.sidebar.multiselect('Quais as condições de clima' , ['conditions Sunny', 'conditions Stormy', 'conditions Sandstorms', 'conditions Cloudy', 'conditions Fog', 'conditions Windy'], default=['conditions Sunny', 'conditions Stormy', 'conditions Sandstorms', 'conditions Cloudy', 'conditions Fog', 'conditions Windy'])


st.sidebar.markdown("""___""")
st.sidebar.markdown('### Powered by Lincon Schafranski')

#Filtro de data
linhas_selecionadas = df1['Order_Date'] < date_slider
df1 = df1.loc[linhas_selecionadas, :]

#Filtro de transito
linhas_selecionadas = df1['Road_traffic_density'].isin(traffic_options)
df1 = df1.loc[linhas_selecionadas, :]

#Filtro de transito
linhas_selecionadas = df1['Weatherconditions'].isin(climate_conditions)
df1 = df1.loc[linhas_selecionadas, :]


#===================================================================
#Layout no Streamlit
#===================================================================

tab1, tab2, tab3 = st.tabs(['Visão Gerencial', '', ''])

with tab1:
    with st.container():
        st.title('Overall Metrics')

        col1, col2, col3, col4 = st.columns( 4 , gap='large')
        with col1:
            maior_idade = df1['Delivery_person_Age'].max()
            col1.metric('Maior idade', maior_idade)
            
        with col2:
            menor_idade = df1['Delivery_person_Age'].min()
            col2.metric('Menor idade', menor_idade)
            
        with col3:
            melhor_condicao = df1['Vehicle_condition'].max()
            col3.metric('Melhor condição', melhor_condicao)

            
        with col4:
            pior_condicao = df1['Vehicle_condition'].min()
            col4.metric('Pior condição', pior_condicao )
            
            
    with st.container():
        st.markdown("""____""")
        st.title('Avaliações')

        col1, col2 = st.columns( 2 )

        with col1:
            st.markdown('##### Avaliação média por entregador')
            coluns = ['Delivery_person_ID' , 'Delivery_person_Ratings']
            tabela_avaliacoes = ( df1.loc[: , coluns].groupby('Delivery_person_ID')
                                                     .mean()
                                                     .reset_index()
                                                     .sort_values(by='Delivery_person_Ratings', ascending=False))
            
            st.dataframe(tabela_avaliacoes)
            
            
        with col2:
            st.markdown('##### Avaliação média por trânsito')
            coluns = ['Road_traffic_density' , 'Delivery_person_Ratings']
            avaliacao_transito = ( df1.loc[: , coluns].groupby('Road_traffic_density')
                                                      .agg(Delivery_mean=('Delivery_person_Ratings' , 'mean') , Delivery_std=('Delivery_person_Ratings' , 'std'))
                                                      .reset_index())

            st.dataframe(avaliacao_transito)
            
            st.markdown('##### Avaliação média por clima')
            coluns = ['Weatherconditions' , 'Delivery_person_Ratings']
            avaliacao_clima = (df1.loc[: , coluns].groupby('Weatherconditions')
                                                  .agg(Delivery_mean=('Delivery_person_Ratings' , 'mean') , Delivery_std=('Delivery_person_Ratings' , 'std'))
                                                  .reset_index())

            st.dataframe(avaliacao_clima)


    with st.container():
        st.markdown("""____""")
        st.title('Velocidade de entrega')

        col1, col2 = st.columns( 2 )

        with col1:
            st.markdown('##### Top entregadores mais rápidos')
            coluns = ['Delivery_person_ID', 'City' , 'Time_taken(min)']
            df_aux = df1.loc[: , coluns].groupby(['City', 'Delivery_person_ID']).mean().sort_values(by=['City', 'Time_taken(min)'] , ascending=True).reset_index()

            top_10 = (df_aux.groupby('City')
                             .apply(lambda x: x.nsmallest(10, 'Time_taken(min)'))
                             .reset_index(drop=True))
            st.dataframe(top_10)

            

        with col2:
            st.markdown('##### Top entregadores mais lentos')
            colunas = ['Delivery_person_ID' , 'City' , 'Time_taken(min)']
            df_aux = df1.loc[: , colunas].groupby(['City' , 'Delivery_person_ID']).mean().sort_values(by=['City', 'Time_taken(min)'] , ascending=False).reset_index()
            lentos_10 = (df_aux.groupby('City')
                               .apply(lambda x: x.nlargest(10, 'Time_taken(min)'))
                               .reset_index(drop=True))

            st.dataframe(lentos_10)
        
            
            
            


