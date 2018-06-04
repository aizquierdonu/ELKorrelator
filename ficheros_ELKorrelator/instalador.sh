#!/bin/bash
#
mkdir -p /var/log/elkorrelator/in
mkdir -p /var/log/elkorrelator/out
mkdir -p /var/log/elkorrelator/tmp
mkdir -p /usr/share/elkorrelator/bin/
cp elkorrelator/correlador.py /usr/share/elkorrelator/bin/
mkdir -p /usr/share/elkorrelator/src
cp elkorrelator/orquestador.c /usr/share/elkorrelator/src/
mkdir -p /usr/share/elkorrelator/rules
cp rules/e.rules /usr/share/elkorrelator/rules/
gcc -O3 -Wall -o /usr/share/elkorrelator/bin/orquestador /usr/share/elkorrelator/src/orquestador.c
bash generar_conf_Logstash/generar_detector.sh
touch /var/log/elkorrelator/in/touch
chown -R logstash.logstash /var/log/elkorrelator
cp servicio_Orquestador/orquestador.service /etc/systemd/system/orquestador.service
chmod 644 /etc/systemd/system/orquestador.service
systemctl daemon-reload
