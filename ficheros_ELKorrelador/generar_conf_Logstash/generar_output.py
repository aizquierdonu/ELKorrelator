#!/usr/bin/python
# -*- coding: iso-8859-15
try:
  with open('/usr/share/elkorrelator/rules/e.rules') as f:
    fichero = f.readlines()
  f.close()
except Exception as error:
  salirOrdenadamente(contexto,error,"Error Read rules")

nombre_regla=""
descripcion_regla=""
level_regla=""

reglas=[]
for linea in fichero:
  if linea[0]=='#' or linea[0]=='\n':
    continue
  regla=linea.rstrip().split('_')[0]
  if regla not in reglas:
    reglas.append(regla)

cont=0
config='''output {

    if "del_elko" in [tags]{
      file {
        codec => line {
          format => "%{message}"
        }
        path => "/var/log/elkorrelator/in/%{+YYYY.MM.dd.HH}.log"
      }
    }
    else{'''
for regla in reglas:
  cont=0
  config_regla=""
  for linea in fichero:
    if linea[0]=='#' or linea[0]=='\n':
      continue
    sp=linea.rstrip().split(':')
    if regla+'_CONTEXTO'==str(sp[0]):
      config_regla=config_regla+'''if "'''+regla+'''" in [tags]{
        file {
          codec => line {
            format => "c'''+regla+'''_%{[json]['''+sp[1]+''']}%{message}"
          }
          path => "/var/log/elkorrelator/in/%{+YYYY.MM.dd.HH}.log"
        }
     }'''
  config=config+config_regla

config=config+"}}"
  
print config


