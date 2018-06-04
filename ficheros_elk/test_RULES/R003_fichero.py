from random import randint
import time

logSNORT="10.0.1.46 snort: [1:620:2] SQL Injection [Classification: attack] [Priority: 2] {TCP} IPPRIVADA:1382 -> IPPUBLICA:80"

IPsPublicas=["1.1.1.1","2.2.2.2","3.3.3.3","4.4.4.4","5.5.5.5","6.6.6.6"]
IPsPrivadas=["10.0.1.50","10.0.1.51","10.0.1.52","10.0.1.53"]

lenIPsPublicas=len(IPsPublicas)
lenIPsPrivadas=len(IPsPrivadas)

ippublica=randint(0, lenIPsPublicas-1)
ipprivada=randint(0, lenIPsPrivadas-1)

log=logSNORT
log=log.replace("IPPUBLICA",IPsPublicas[ippublica])
log=log.replace("IPPRIVADA",IPsPrivadas[ipprivada])
print time.strftime("%b %d %H:%M:%S") + " " + log
