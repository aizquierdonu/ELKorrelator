#!/usr/bin/python
# -*- coding: iso-8859-15
#Utilizado para obtener el argumento
import sys
#Utilizado para sendTCP
import socket
#Utilizado para los sleep
import time
#Utilizado para el decode del base64
import base64
# Utilizado en la llamada a sendTCP
import copy
#Utilizado para el parseo JSON
import json
#Utilizado para obtener el timestamp
from datetime import datetime
#Utilizado para las consultas en Elasticsearch
import requests

# Esta funcion permite eliminar caracteres no deseados para evitar posibles inyecciones en las consultas
def sanetizar_caracteres_string(st,caracteres,c_escape):
  st_sanetizado=""
  for letra in st:
    if letra in caracteres:
      st_sanetizado=st_sanetizado+letra
    else:
      st_sanetizado=st_sanetizado+c_escape
  return st_sanetizado

# Esta funcion nos permite anadir condiciones a la consulta a elastic
def get_condicion(subcondicion,cond,historico):
  if '==' in subcondicion or '=~' in subcondicion:
    if '==' in subcondicion:
      campo=subcondicion.split('==')[0]
      campo=campo[1:len(campo)-1]+'.keyword'
      valor=subcondicion.split('==')[1]
      valor=valor[1:len(valor)-1]
      termino='term'
    if '=~' in subcondicion:
      campo=subcondicion.split('=~')[0]
      campo=campo[1:len(campo)-1]+'.keyword'
      valor=subcondicion.split('=~')[1]
      valor='*'+valor[1:len(valor)-1]+'*'
      termino='wildcard'

    valor=sanetizar_caracteres_string(valor,"0123456789.:_-* qwertyuiopasdfghjklñzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM","_")
    campo=sanetizar_caracteres_string(campo,"0123456789.:_- qwertyuiopasdfghjklñzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM","_")
      
    subvalores=[]
    if "___" in valor :
      subvalores=valor.split("___")
      subvalores[0]=int(sanetizar_caracteres_string(subvalores[0],"0123456789","0"))
      if subvalores[0]<len(historico):
        try:
          valor=historico[subvalores[0]][subvalores[1]]
        except:
          valor='""'
    if valor[0]!='"':
      valor='"'+valor
    if valor[len(valor)-1]!='"':
      valor=valor+'"'
    cond=cond+'''{"'''+termino+'''": {"'''+campo+'''":'''+valor+'''}},'''
  return cond

# Esta funcon es la encargada de construir las consultas que se haran a elastic
def generar_query_elastic(t_0,t_1,condiciones,historico):
  cond_must=''
  cond_not_must=''
  cond=''
  termino=''
  yes=True
  if len(condiciones)>0:
    for condicion in condiciones:
      cond=''
      if (condicion[0]=='Y' and condicion[1]=='E' and condicion[2]=='S' and condicion[3]==' ') or (condicion[0]=='N' and condicion[1]=='O' and condicion[2]=='T' and condicion[3]==' '):
        if (condicion[0]=='Y' and condicion[1]=='E' and condicion[2]=='S' and condicion[3]==' '):
          yes=True
        else:
          yes=False
        condicion=condicion[4:]
        # si hay or es que esta condicion esta compuesta por sub condiciones
        if ' or ' in condicion:
          subcondiciones=condicion.split(' or ')
          cond=cond+''',{"bool": {"should": ['''
          for subcondicion in subcondiciones:
            cond=get_condicion(subcondicion,cond,historico)
          cond=cond[0:len(cond)-1]
          cond=cond+''']}}'''
          if yes:
            cond_must=cond_must+cond
          else:
            #print "prueba: "+cond_not_must
            if len(cond_not_must)==0:
              cond=cond[1:]
            cond_not_must=cond_not_must+cond
        else:
          # hay un solo termino sin OR
          #print "un solo ermino"
          #print condicion
          subcondicion=condicion
          cond=get_condicion(subcondicion,cond,historico)
          if yes:
            cond=','+cond[:len(cond)-1]
            cond_must=cond_must+cond
          else:
            #print cond
            if len(cond_not_must)!=0:
               cond=','+cond
            cond=cond[:len(cond)-1]
            cond_not_must=cond_not_must+cond


    
  plantilla_payload = [
  '''{''','''
    "docvalue_fields": [
      "@timestamp",
      "updated_at",
      "url.accessDate",
      "url.createDate"
    ],''','''
    "query": {
      "bool": {
        "must": [
          {
            "range": {
              "@timestamp": {
                "gte": ''',str(t_0),''',
                "lte": ''',str(t_1),''',
                "format": "epoch_millis"
              }
            }
          }''',cond_must,'''
        ],
        "filter": [],
        "should": [],
        "must_not": [ '''+cond_not_must+''' ]
      }
    }
  }''']
  payload_count=''
  for elemento in plantilla_payload:
    payload_count=payload_count+elemento
  payload_data=''
  count=0
  for elemento in plantilla_payload:
    if count!=1:
      payload_data=payload_data+elemento
    count=count+1
  #print payload_count
  return payload_count,payload_data

# Mediante esta funcion se lanza la consulta anteriormente construida a elastic
def peticionElastic(contexto,queryElastic,ipElastic):
  headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
  url = 'http://'+ipElastic+':9200/logs*/_search'
  try:
    r = requests.post(url, data=queryElastic, headers=headers)
  except Exception as error:
    salirOrdenadamente(contexto,error,"Error llamada Elastic")
  if (str(r)!='<Response [200]>'):
    error=str(r.text)
    salirOrdenadamente(contexto,error,"No 200 llamada Elastic")
  respuesta=str(copy.copy(r.text))
  json_response=json.loads(respuesta)
  try:
    json_response=json.loads(respuesta)
  except Exception as error:
    salirOrdenadamente(contexto,error,"Error JSON")
  return json_response

# Se encarga de finalizar el contexto de correlacion de manea ordenada
def salirOrdenadamente(contexto,error,msg):
  print str(msg) + " - " + str(error)
  finContexto(contexto)
  sys.exit(0)
  
# Se encarga de finalizar un contexto, que sera eliminado por el orquestador
def finContexto(contexto):
  # Anadimos el comando de eliminacion de este contexto
  comando='d'+contexto
  # Enviamos el comando de eliminacion por TCP al Detector
  try:
    sendTCP(copy.copy(comando),ipDetector,TCP_PORT)
  except Exception as error:
    salirOrdenadamente(contexto,error,"Error sendTCP")

# Se encarga de enviar mensajes TCP al Detector o a Logstash
def sendTCP(msg,ip,port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((ip,port))
  s.send(msg)
  s.close()

# Obtenemos la fecha en milisecA
def get_timestamp_elastic(tiempo,zona_h):
  try:
    dt=datetime.now().strptime(tiempo,'%Y-%m-%dT%H:%M:%S.%fZ')
    timestamp=dt.strftime('%s')
  except Exception as error:
    salirOrdenadamente(contexto,error,"Error Parse Timestamp")
  timestamp=(int(timestamp)*(10**3))+(int(dt.microsecond)/(10**3))
  timestamp=timestamp+(zona_h*60*60*(10**3))
  return timestamp

# Se encarga de obtener los campos regla, log y contexto del mensaje
def getFields(mensaje):
  regla=''
  log=''
  contexto=''
  leer_regla = True
  leer_log = False
  leer_contexto = True
  for i in mensaje:
    if (i=='_'):
      leer_regla = False
    if (i=='{'):
      leer_log = True
      leer_regla = False
      leer_contexto = False
    if ord(i)==0:
      leer_log = False
    if (leer_regla):
      regla=regla+i
    if (leer_log):
      log=log+i
    if (leer_contexto):
      contexto=contexto+i
  return regla,log,contexto


# Definimos las variables
ipElastic='IP_ELASTICSEARCH'
ipDetector = 'IP_DETECTOR'
ipLogstash = 'IP_LOGSTASH'
TCP_PORT = 35555
TCP_PORT_ALERTA = 45555
T_ESPERA = 5


# Obtenemos el argumento
MESSAGE_64 = sys.argv[1]

# Se espera para iniciar la correlacion , recomendable 5 segundos para no sobrecargar elastic
time.sleep( T_ESPERA )

# Decodificamos el mensaje que nos llega en Base64
print MESSAGE_64
try:
  mensaje=base64.b64decode(MESSAGE_64)
except:
  print ('Error Base64')
  sys.exit(0)

# Eliminamos el primer caracter, que corresponde con el comando, en este caso siempre es c
mensaje=mensaje[1:]

# Obtenemos la regla y el log
regla,log,contexto=getFields(mensaje)

##print (regla)
##print (contexto)
##print (log)

# Parseamos el log en formato JSON para menejarlo de manera mas sencilla
try:
  json_data=json.loads(log)
except Exception as error:
  salirOrdenadamente(contexto,error,"Error JSON")
#print (json_data['@timestamp'])

# Se almacena el historico de resutados, se adjuntaran si finalmente se cumple a regla de correlacion
historico_resultados_json=[]
historico_resultados_json.append(json_data)
 
# No he conseguido automatizar la zona_horaria, es un punto a mejorar para futuras versiones
zona_horaria=+2
timestamp=get_timestamp_elastic(str(json_data['@timestamp']),zona_horaria)
#print (timestamp)

# cargamos la regla
try:
  with open('/usr/share/elkorrelator/rules/e.rules') as f:
    fichero = f.readlines()
  f.close()
except Exception as error:
  salirOrdenadamente(contexto,error,"Error Read rules")

nombre_regla=""
descripcion_regla=""
level_regla=""

# Obtenemos los valores genericos de la regla como nombre, descripcion...
for linea in fichero:
  if linea[0]=='#':
    continue
  sp=linea.rstrip().split(':')
  if (regla+'_DESCRIPTION' == sp[0]):
    descripcion_regla=sanetizar_caracteres_string(str(sp[1]),"0123456789qwertyuiopasdfghjklñzxcvbnmQWERTYUIOPASDFGHJKLÑZXCVBNM","_")
  if (regla+'_LEVEL' == sp[0]):
    level_regla=sanetizar_caracteres_string(str(sp[1]),"0123456789qwertyuiopasdfghjklñzxcvbnmQWERTYUIOPASDFGHJKLÑZXCVBNM","_")
  if (regla+'_NAME' == sp[0]):
    nombre_regla=sanetizar_caracteres_string(str(sp[1]),"0123456789qwertyuiopasdfghjklñzxcvbnmQWERTYUIOPASDFGHJKLÑZXCVBNM","_")

# comienza la evaluacion de la regla
nivel=1
while True:
  #Obtenemos los valores del nivel correspondiente para la regla obtenida
  configuraciones_regla=[]
  for linea in fichero:
    if linea[0]=='#':
      continue
    sp=linea.split(':')
    if ((regla+'_N'+str(nivel)) in sp[0]):
      configuraciones_regla.append(linea.rstrip())

  # Si ya no hay mas niveles finalizamos, la regla se ha cumplido
  if len(configuraciones_regla)==0:
    print "Ya no hay mas niveles"
    resultados_to_elastic=[]
    id_resultados_to_elastic=[]
    count_resultados_to_elastic=0
    mensaje_to_elastic="{"
    for r in historico_resultados_json:
      if count_resultados_to_elastic!=0:
        mensaje_to_elastic=mensaje_to_elastic+","
      mensaje_to_elastic=mensaje_to_elastic+'"message_n'+str(count_resultados_to_elastic)+'":"'+r['message']+'"'
      count_resultados_to_elastic=count_resultados_to_elastic+1
    mensaje_to_elastic=mensaje_to_elastic+"}"
    # Enviamos a Logstash la alerta de correlacion generada
    sendTCP(copy.copy(str(regla)+","+str(level_regla)+","+str(nombre_regla)+","+str(descripcion_regla)+","+str(contexto)+","+str(mensaje_to_elastic)),ipLogstash,TCP_PORT_ALERTA)
    # Una vez enviada, eliminamos el contexto y salimos
    salirOrdenadamente(contexto,"FIN_contexto"+str(contexto),"Se genera alerta")
    break

  
  # Valores por defecto para un nivel
  sleep_level=10
  sleep_query=60
  timestamp_min=-60
  timestamp_max=+1200
  comportamiento_negado=0
  resultados_cumple=1
  evento_resultado=0
  condiciones = []
  numero_condiciones = 0
  
  # Obtenemos los valores del fichero de reglas, para esta regla en este nivel concreto
  try:
    for configuracion in configuraciones_regla:
      sp=configuracion.split(':')
      if ((regla+'_N'+str(nivel)+'_SL') == sp[0]):
        sleep_level=int(sp[1])
      if ((regla+'_N'+str(nivel)+'_SQ') == sp[0]):
        sleep_query=int(sp[1])
      if ((regla+'_N'+str(nivel)+'_Tmin') == sp[0]):
        timestamp_min=int(sp[1])
      if ((regla+'_N'+str(nivel)+'_Tmax') == sp[0]):
        timestamp_max=int(sp[1])
      if ((regla+'_N'+str(nivel)+'_Rnot') == sp[0]):
        comportamiento_negado=int(sp[1])
      if ((regla+'_N'+str(nivel)+'_RyOK') == sp[0]):
        resultados_cumple=int(sp[1])
      if ((regla+'_N'+str(nivel)+'_Event') == sp[0]):
        evento_resultado=int(sp[1])
      if ((regla+'_N'+str(nivel)+'_C'+str(numero_condiciones)) == sp[0]):
        condiciones.append(sanetizar_caracteres_string(str(sp[1]),"0123456789.-_=\"~: qwertyuiopasdfghjklñzxcvbnmQWERTYUIOPASDFGHJKLÑZXCVBNM","_"))
        numero_condiciones=numero_condiciones+1
  except Exception as error:
    salirOrdenadamente(contexto,error,"Error cargando el nivel "+str(nivel)+" de la regla "+regla)
  
  # Obtenemos las fechas min y max, no en funcion del momento actual si no en funcion del tiempo del evento
  timestamp_min=timestamp+(timestamp_min*10**3)
  timestamp_max=timestamp+(timestamp_max*10**3)
 
  # Se realiza el sleep de este nivel, importante poner algo para no sobrecargar elastic
  time.sleep( sleep_level )
  
  # Obtenemos la fecha actual
  timestamp_now=int(datetime.now().strftime('%s'))*(10**3)
  #timestamp_now=timestamp_now-(zona_horaria*60*60*(10**3))
  
  # Contador para saber si se trata de la primera peticion
  primera_peticion=True
  totales=0
  log_respuesta=""
  while True:
    #Si por lo que sea es mayor, por ejemplo por el spleet entonces
    if timestamp_now>timestamp_max:
      timestamp_now=timestamp_max

    # Obtenemos la consultas que se realizara a elastic para contar resultados
    payload_count,payload_data=generar_query_elastic(timestamp_min,timestamp_now,condiciones,historico_resultados_json)

    # Parseamos la respesta como JSON
    json1=peticionElastic(contexto,payload_count,ipElastic)
 
    # Si ha resultados entonces intentamos obtener uno de ellos, el primero o el ultimo
    totales=totales+int(json1['hits']['total'])
    if totales>0 and primera_peticion and evento_resultado==0:
      json2=peticionElastic(contexto,payload_data,ipElastic)
      log_respuesta = (json2['hits']['hits'][0]['_source'])
      primera_peticion=False
    if resultados_cumple<=totales and evento_resultado==1:
      json2=peticionElastic(contexto,payload_data,ipElastic)
      log_respuesta = (json2['hits']['hits'][-1]['_source'])
  
    #Valorar si se ha cumplido este nivel
    if resultados_cumple<=totales:
      if comportamiento_negado==0:
        historico_resultados_json.append(log_respuesta)
        timestamp=get_timestamp_elastic(str(log_respuesta['@timestamp']),zona_horaria)
        nivel=nivel+1
        break
      elif comportamiento_negado==1:
        salirOrdenadamente(contexto,"FIN_contexto"+str(contexto),"No se cumple la regla de correlacion")
        break
    if timestamp_now>=timestamp_max:
      if comportamiento_negado==0:
        salirOrdenadamente(contexto,"FIN_contexto"+str(contexto),"No se cumple la regla de correlacion")
        break
      elif comportamiento_negado==1:
        historico_resultados_json.append({'message' : 'Se cumple que no hay log'})
        print "se cumple, no hay log"
        timestamp=int(datetime.now().strftime('%s'))*(10**3)
        timestamp=timestamp-(zona_horaria*60*60*(10**3))
        nivel=nivel+1
        break
    # Actualizamos los tiempos para la siguiente consulta
    timestamp_min=timestamp_now+1
    timestamp_now=int(datetime.now().strftime('%s'))*(10**3)
    
    # Importante tener un sleep entre consutas del mismo nivel para no sobrecargar elastic
    time.sleep( sleep_query )
    
# FIN





