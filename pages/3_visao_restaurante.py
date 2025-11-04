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
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title='Visão Restaurantes', layout='wide')
#===================================================================
# Funções
#===================================================================

def clean_code(df1):
    """ Esta funcao de limpar do dataframe

        Tipos de limpeza:
        1. Remoção de valores NaN
        2. Transformacao tipo de dados
        3. Formatacao da coluna de data
        4. Remocao dos espacos das variaveis de texto
        5. Limpeza da coluna de tempo (remocao do texto da variavel numerica)

        Input: Dataframe
        Output: Dataframe
    
    """
    # Retirada de espaços em branco
    colunas_texto = ['ID', 'Road_traffic_density', 'Type_of_order', 'Type_of_vehicle', 'City', 'multiple_deliveries', 'Delivery_person_Age', 'Festival']
    for coluna in colunas_texto:
        df1[coluna] = df1[coluna].str.strip()
    
    # Removendo linhas com valores inválidos ('NaN' como string) nas colunas
    df1 = df1[df1['Road_traffic_density'] != 'NaN']
    df1 = df1[df1['City'] != 'NaN']
    df1 = df1[df1['Delivery_person_Age'] != 'NaN']
    df1 = df1[df1['multiple_deliveries'] != 'NaN']
    df1 = df1[df1['Festival'] != 'NaN']
    
    #Converter Lat/Long para numérico e tratar strings inválidas como nulo (NaN)
    df1['Delivery_location_latitude'] = pd.to_numeric(df1['Delivery_location_latitude'], errors="coerce")
    df1['Delivery_location_longitude'] = pd.to_numeric(df1['Delivery_location_longitude'], errors="coerce")
    df1['Delivery_person_Age'] = pd.to_numeric(df1['Delivery_person_Age'], errors="coerce")
    df1['Delivery_person_Ratings'] = pd.to_numeric(df1['Delivery_person_Ratings'], errors="coerce")
    df1['multiple_deliveries'] = pd.to_numeric(df1['multiple_deliveries'], errors="coerce")

    #Remover linhas onde Lat/Long são nulas (NaN) após a conversão
    df1.dropna(subset=['Delivery_location_latitude', 'Delivery_location_longitude'], inplace=True)
    
    # Convertendo para tipo data
    df1['Order_Date'] = pd.to_datetime(df1['Order_Date'], format="%d-%m-%Y")
    
    # Limpando a coluna de time taken
    df1['Time_taken(min)'] = df1['Time_taken(min)'].apply(lambda x: x.split('(min) ')[1])
    df1['Time_taken(min)'] = df1['Time_taken(min)'].astype(int)

    return df1


def top_delivers(df1, tipo):
    colunas = ['Delivery_person_ID' , 'City' , 'Time_taken(min)']
    df_aux = df1.loc[: , colunas].groupby(['City' , 'Delivery_person_ID']).mean().sort_values(by=['City', 'Time_taken(min)']).reset_index()
    if tipo == 'lentos':
        df2 = (df_aux.groupby('City')
                 .apply(lambda x: x.nlargest(10, 'Time_taken(min)'))
                 .reset_index(drop=True))
    elif tipo == 'rapidos':
        df2 = (df_aux.groupby('City')
                 .apply(lambda x: x.nsmallest(10, 'Time_taken(min)'))
                 .reset_index(drop=True))
    return df2

def distance_haversine(df1):
    coluns = ['Restaurant_latitude', 'Restaurant_longitude', 'Delivery_location_latitude', 'Delivery_location_longitude']
    df1['Distance (km)'] = (df1.loc[: , coluns].apply(lambda x: haversine((x['Restaurant_latitude'] , x['Restaurant_longitude']) , (x['Delivery_location_latitude'] , x['Delivery_location_longitude'])), axis=1))
    valor_medio = np.round(df1['Distance (km)'].mean(),2)
    return valor_medio


#------------------------------------------------------------Início da estrutura lógica do código-----------------------------------------------------------

#===================================================================
# Import dataset
#===================================================================
df = pd.read_csv('dataset/train.csv')
df1 = df.copy()


#===================================================================
# Limpando os dados
#===================================================================
df1 = clean_code(df1)


#===================================================================
#Barra Lateral
#===================================================================


st.header('Marketplace - Visão Restaurantes')

#image_path = '/home/lincon/repos/ftc_analisando_dados_com_python/logo.png'
image = Image.open('logo.png')
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
        st.markdown("""___""")
        st.title("Overall Metrics")

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            qtd_entregadores = len(df1['Delivery_person_ID'].unique())
            col1.metric('Entregadores únicos', qtd_entregadores)

        with col2:
            valor_medio = distance_haversine(df1)
            col2.metric('Distância média das entregas' , valor_medio)            

        with col3:
            tempo_medio_festival = np.round(df1.loc[df1['Festival'] == 'Yes' , 'Time_taken(min)'].mean(), 2)
            col3.metric('Tempo entrega com festival' , tempo_medio_festival)

        with col4:
            desvpad_festival = np.round(df1.loc[df1['Festival'] == 'Yes' , 'Time_taken(min)'].std(), 2)
            col4.metric('Desvio padrão entrega com festival' , desvpad_festival)

        with col5:
            df_final = (df1.loc[: , ['City' , 'Time_taken(min)' , 'Type_of_vehicle']].groupby(['City' , 'Type_of_vehicle'])
                                                                                    .agg(tempo_medio=('Time_taken(min)' , 'mean') , desvio_padro=('Time_taken(min)' , 'std'))
                                                                                    .reset_index())
            tempo_medio_nao_festival = np.round(df1.loc[df1['Festival'] == 'No' , 'Time_taken(min)'].mean(), 2)
            col5.metric('Tempo entrega sem festival' , tempo_medio_nao_festival)
            

        with col6:
            df_final = (df1.loc[: , ['City' , 'Time_taken(min)' , 'Type_of_vehicle']].groupby(['City' , 'Type_of_vehicle'])
                                                                                    .agg(tempo_medio=('Time_taken(min)' , 'mean') , desvio_padro=('Time_taken(min)' , 'std'))
                                                                                    .reset_index())
            desvpad_nao_festival = np.round(df1.loc[df1['Festival'] == 'No' , 'Time_taken(min)'].std(), 2)
            col6.metric('Desvio padrão entrega sem festival' , desvpad_nao_festival)

    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""___""")
            df_aux = df1.loc[:, ['City', 'Time_taken(min)']].groupby('City').agg({'Time_taken(min)': ['mean', 'std']})
            df_aux.columns = ['avg_time', 'std_time']
            df_aux = df_aux.reset_index()

            fig = go.Figure()
            fig.add_trace(go.Bar(
            name='Control',
            x=df_aux['City'],
            y=df_aux['avg_time'],
            error_y=dict(type='data', array=df_aux['std_time'])
            ))

            fig.update_layout(barmode='group')
            st.plotly_chart(fig)

        with col2:
            st.markdown("""___""")
            st.markdown("###### Tempo médio e o desvio padrão de entrega por cidade e tipo de pedido")
            coluns = ['City' , 'Time_taken(min)' , 'Type_of_order']
            df_final = df1.loc[: , coluns].groupby(['City' , 'Type_of_order']).agg(tempo_medio=('Time_taken(min)' , 'mean') , desvio_padro=('Time_taken(min)' , 'std')).reset_index()
            st.dataframe(df_final)


    
        
    with st.container():
        st.markdown("""___""")
        st.title("Distribuição de Tempo")
        
        col1, col2 = st.columns(2)
        with col1:
           
            st.markdown("##### Proporção da distância média de entrega por cidade")
    
            cols = ['Delivery_location_latitude', 'Delivery_location_longitude', 
            'Restaurant_latitude', 'Restaurant_longitude']
    
            df1['distance'] = df1.loc[:, cols].apply(
        lambda x: haversine(
            (x['Restaurant_latitude'], x['Restaurant_longitude']),
            (x['Delivery_location_latitude'], x['Delivery_location_longitude'])
            ), axis=1
            )

            avg_distance = df1.loc[:, ['City', 'distance']].groupby('City').mean().reset_index()

            fig2 = go.Figure(
            data=[go.Pie(
            labels=avg_distance['City'], 
            values=avg_distance['distance'], 
            pull=[0, 0.05, 0]
            )]
            )
    
            st.plotly_chart(fig2)

            
                       

        with col2:
            st.markdown("##### Proporção da distância média de entrega por cidade e por tipo de tráfego")
    
            cols = ['City', 'Time_taken(min)', 'Road_traffic_density']
            df_aux = df1.loc[:, cols].groupby(['City', 'Road_traffic_density']).agg({'Time_taken(min)': ['mean', 'std']})

            df_aux.columns = ['avg_time', 'std_time']
            df_aux = df_aux.reset_index()

            fig1 = px.sunburst(
            df_aux, path=['City', 'Road_traffic_density'], values='avg_time',
            color='std_time', color_continuous_scale='RdBu',
            color_continuous_midpoint=np.average(df_aux['std_time'])
            )

            st.plotly_chart(fig1)
            


        



































