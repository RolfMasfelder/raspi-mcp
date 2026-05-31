#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import configparser
import json
import paho.mqtt.client as paho
from time import sleep, gmtime, strftime

def config_lesen():
    config=configparser.ConfigParser()
    config.read(os.path.realpath(__file__)[:-2]+'ini')
    mqtt_topic= config['MQTT']['topic']    #"/pi3/temp"
    mqtt_ip   = config['MQTT']['ip']       #"192.168.178.25"
    mqtt_port = int(config['MQTT']['port'])#1883
    return mqtt_topic,mqtt_ip,mqtt_port

mqtt_topic, mqtt_ip, mqtt_port = config_lesen()

# 1-Wire Slave-Liste lesen
# wieviele Sensoren sind denn vorhanden?
file = open('/sys/devices/w1_bus_master1/w1_master_slaves')
w1_slaves = file.readlines()
file.close()

def on_connect(client, userdata, flags, rc) :
    if rc==0:
        print("connected ok")
    else:
        print("not connected", rc)


def on_disconnect(client, userdata, flags, rc=0) :
    print("disconnect result code "+str(rc))

def on_publish(client,userdata,result):             #create function for callback
    print("data published \n")

client1= paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1,
                     client_id=mqtt_topic)         #create client object
client1.on_publish = on_publish                     #assign function to callback
client1.on_connect = on_connect
client1.on_disconnect = on_disconnect

client1.connect(mqtt_ip,mqtt_port)                  #establish connection

p = { 'id': '28-*', 'temp': '0', 'time': '' }

# Fuer jeden 1-Wire Slave aktuelle Temperatur ausgeben
for line in [ l for l in w1_slaves if l[:3] == '28-'] :
    # 1-wire Slave extrahieren
    w1_slave = line.split("\n")[0]
    # 1-wire Slave Datei lesen
    file = open('/sys/bus/w1/devices/' + str(w1_slave) + '/w1_slave')
    filecontent = file.read()
    file.close()

    # Temperaturwerte auslesen und konvertieren
    stringvalue = filecontent.split("\n")[1].split(" ")[9]
    temperature = str(float(stringvalue[2:]) / 1000)

    p['id'] = w1_slave
    p['temp'] = temperature
    p['time'] = strftime("%Y%m%d %H:%M:%S +0000", gmtime()) 

    # Temperatur ausgeben
    print(json.dumps(p))
    ret= client1.publish(mqtt_topic,json.dumps(p))                   #publish

sleep(0.1)
client1.disconnect()
