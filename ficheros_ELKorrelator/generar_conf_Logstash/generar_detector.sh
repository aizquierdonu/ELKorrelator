#!/bin/bash
python generar_conf_Logstash/generar_input.py > /etc/logstash/conf.d/1-input.conf
python generar_conf_Logstash/generar_filter.py > /etc/logstash/conf.d/2-filter.conf
python generar_conf_Logstash/generar_output.py > /etc/logstash/conf.d/3-output.conf
