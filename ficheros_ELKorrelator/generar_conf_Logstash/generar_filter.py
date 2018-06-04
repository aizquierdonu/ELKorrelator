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
config='''filter{
  if "new_elko" in [tags]{
    # Obtenemos los campos
    json{
      source => "message"
      target => "json"
    }
'''
for regla in reglas:
  cont=0
  config_regla=""
  for linea in fichero:
    if linea[0]=='#' or linea[0]=='\n':
      continue
    sp=linea.rstrip().split(':')
    if regla+'_N0_C'+str(cont)==str(sp[0]):
      #print sp[1]
      cont=cont+1
      if sp[1][0]=='Y' and sp[1][1]=='E' and sp[1][2]=='S' and sp[1][3]==' ' :
        sp[1]=sp[1][4:]
        config_regla=config_regla+'''if [json]'''+sp[1]+"{"
      if sp[1][0]=='N' and sp[1][1]=='O' and sp[1][2]=='T' and sp[1][3]==' ' :
        sp[1]=sp[1][4:]
        config_regla=config_regla+'''if !([json]'''+sp[1]+"){"
  if len(config_regla)>0:
    config_regla=config_regla+'''mutate{add_tag => [ "'''+regla+'''" ]}'''
    config_regla=config_regla+("}")*cont+"\n"
  #print "config "+config_regla
  config=config+config_regla

config=config+"}}"
  
        
    
  
print config


