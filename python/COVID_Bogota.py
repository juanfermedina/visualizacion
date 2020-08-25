#Carga librerias
import pandas as pd
import matplotlib.pyplot as plt
from ipywidgets import interact, interactive
import ipywidgets as widgets
import numpy as np
import re
from traceback import format_exc #Para try, except
import plotly.express as px
import seaborn as sns
from datetime import date, timedelta

#Prepara ruta de fuente de datos
ayer = date.today() - timedelta(days=1)
ayer = ayer.strftime('%d-%m-%Y')

date = re.sub("-","", ayer)
txt_ini = "https://datosabiertos.bogota.gov.co/dataset/44eacdb7-a535-45ed-be03-16dbbea6f6da/resource/b64ba3c4-9e41-41b8-b3fd-2da21d627558/download/osb_enftransm-covid-"
txt_fini = "-.csv"
url = txt_ini + date + txt_fini
#url

#Carga archivo a partir de la url

#Inicializa variable que captura la posicion del error
posicion = 0

try:
    #Carga archivo desde url en dataframe
    df=pd.read_csv(url,encoding='latin1', sep=';')
    
    #Elimina registros NaN
    df = df.dropna()

except ValueError:
    #Captura el mensaje de error
    exc = format_exc()
    
    #Inicio de la posicicion que indica el numero del registro con error
    inicio = exc.find('in line ') + 8

    #Fin de la posicicion que indica el numero del registro con error
    fin = exc.find(', saw')

    #Extrae el numero del registro con error
    posicion = int(exc[inicio:fin])
        
    #Capturado el error e identificado el registro errado se intenta cargar hasta antes del error
    df=pd.read_csv(url,encoding='latin1', nrows = posicion - 4, sep=';')
    
    #Elimina registros NaN
    df = df.dropna()
    
#Renombra las columnas
df = df.rename(columns={'Fecha de inicio de síntomas': 'FechaSint', 
                       'Fecha de diagnóstico': 'FechaDiag', 
                       'Ciudad de residencia': 'CiudadRes',
                       'Localidad de residencia': 'Localidad',
                       'Unidad de medida de la edad': 'UnidadEdad',
                       'Tipo de caso': 'TipoCaso',
                       'Ubicación': 'Ubicacion',})

#Estandariza variable Estado
df["Estado"]=[i.replace("Fallecido No aplica No causa Directa","Fallecido_OC").replace(" ","") for i in df["Estado"]]
#df["Estado"].unique()

#Recategoriza UnidadEdad
#Transforma variable en cadena
df['UnidadEdad'] = df['UnidadEdad'].astype(str)
df['UnidadEdad']=[i.replace('1.0','Años').replace('2.0','Meses').replace('3.0','Dias') for i in df["UnidadEdad"]]
#df.head()


#####################################################
### AJUSTA EL TIPO DE DATO DE LAS COLUMNAS FECHA ####
#No se puede cambiar a la columna Fecha de inicio de 
#síntomas porque una de sus categorias es asintomatico
#####################################################
#df['FechaSint'] =  pd.to_datetime(df['FechaSint'], format='%d/%m/%Y')
df['FechaDiag'] =  pd.to_datetime(df['FechaDiag'], format='%d/%m/%Y')
#df.head()

#Ordena por fecha de diagnostico
df = df.sort_values(by=['FechaDiag'])
df.head()

#Crea columna que contiene todas las edades en unidad fechas

#Funcion que recalcula la edad en años
def pasaAños(row):
    if row['UnidadEdad'] == 'Meses':
        edad = row['Edad'] / 12 #Convierte meses a años
    elif row['UnidadEdad'] == 'Dias':
        edad = row['Edad'] / 362 #Convierte dias a años
    else:
        edad = row['Edad'] #Mantiene años en años
    return edad

#Creacion de nueva variable
df['EdadAños'] = df.apply(pasaAños, axis=1)
#df.head()

#Crea columna que contiene los rangos de edad de acuerdo al ciclo de vida del Ministerior de Salud de Colombia
#Funcion que recategoriza la edad segun el ciclo de vida
def cicloVida(row):
    if row['EdadAños'] < 1:
        etapa = ' < 1'
    elif row['EdadAños'] <= 10:
        etapa = '1 - 10'
    elif row['EdadAños'] <= 20:
        etapa = '11 - 20'
    elif row['EdadAños'] <= 30:
        etapa = '21 - 30'
    elif row['EdadAños'] <= 40:
        etapa = '31 - 40'
    elif row['EdadAños'] <= 50:
        etapa = '41 - 50'
    elif row['EdadAños'] <= 60:
        etapa = '51 - 60'
    elif row['EdadAños'] <= 70:
        etapa = '61 - 70'
    elif row['EdadAños'] <= 80:
        etapa = '71 - 80'
    elif row['EdadAños'] <= 90:
        etapa = '81 - 90'
    else:
        etapa = '>= 90'
    return etapa

#Creacion de nueva variable
df['RangoEdad'] = df.apply(cicloVida, axis=1)
#df.head()

#Genera agregado de total casos acumulados
totalAcum = pd.DataFrame(df['FechaDiag'].value_counts()).sort_index().reset_index() #Calcula agregado por dia
totalAcum.columns = ['FechaDiag', 'NroCasosDia'] #Renombra las columnas
totalAcum['Acumulado'] = totalAcum['NroCasosDia'].cumsum() # Calcula acumulado
#totalAcum

#####################################################
#Genera grafico
fig = px.line(totalAcum, x='FechaDiag', y='Acumulado')
fig.update_layout(title='Total Casos Acumulados COVID19')

#Agrega dias sin IVA
fig.add_shape(dict(type= 'line', yref= 'paper', y0= 0, y1= 1,  xref= 'x', x0= '2020-06-20', x1= '2020-06-20', 
                       line=dict(color='Red', width=1, dash='dashdot')))

fig.add_annotation(text="Día sin IVA #1", x='2020-06-18', y=totalAcum['Acumulado'].max(), showarrow=False, textangle = 270)

fig.add_shape(dict(type= 'line', yref= 'paper', y0= 0, y1= 1, xref= 'x', x0= '2020-07-03', x1= '2020-07-03', 
                       line=dict(color='Red', width=1, dash='dashdot')))

fig.add_annotation(text="Día sin IVA #2", x='2020-07-01', y=totalAcum['Acumulado'].max(), showarrow=False, textangle = 270)
fig.show()

#####################################################
#Genera grafico
fig = px.line(totalAcum, x='FechaDiag', y='NroCasosDia')

fig.add_shape(dict(type= 'line', yref= 'paper', y0= 0, y1= 1,  xref= 'x', x0= '2020-06-20', x1= '2020-06-20', 
                       line=dict(color='Red', width=1, dash='dashdot')))

fig.add_annotation(text="Día sin IVA #1", x='2020-06-18', y=totalAcum['NroCasosDia'].max(), showarrow=False, textangle = 270)

fig.add_shape(dict(type= 'line', yref= 'paper', y0= 0, y1= 1, xref= 'x', x0= '2020-07-03', x1= '2020-07-03', 
                       line=dict(color='Red', width=1, dash='dashdot')))

fig.add_annotation(text="Día sin IVA #2", x='2020-07-01', y=totalAcum['NroCasosDia'].max(), showarrow=False, textangle = 270)

fig.update_layout(title='Total Casos Por Día COVID19')
fig.show()
