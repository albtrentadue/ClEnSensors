#!/usr/bin/python

"""
 ClENSensors / Control node
 by Alberto Trentadue Dec.2015

 The Collector Module implements the Collector and the Retriever objects
 to collect measures from sensors, store them in the local RRD database and
 forward them to the destination storage on the remote server

 Copyright Alberto Trentadue 2015, 2016

 This file is part of ClENSensors.

 ClENSensors is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 ClENSensors is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with ClENSensors.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys, signal, threading, time
from Collector_config import Collector_config
from MQTTHandler import MQTTHandler
from Collector import Collector
from MQTT2Serial import MQTT2Serial
from RRD import RRD
#from EmonRetriever import EmonRetriever
from ThingsboardRetriever import ThingsboardRetriever

keep_on = True

"""
The SIGTERM & SIGINT signal handler to quit the process 
"""
def signal_handler(_signo, _stack_frame):
	global keep_on
	# Shutdown the processes
	#print "Caught signal for shutdown: " + str(_signo)
	keep_on = False
	
#setup the SIGTERM & SIGINT hook handler
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

"""
Execution start
"""

arg_ser = '/dev/ttyUSB0' #the default serial port

if len(sys.argv) == 2:
    arg_ser = sys.argv[1]
elif len(sys.argv) > 2:
    print 'Wrong command line arguments. Exiting.'
    sys.exit(1)

# Takes command line argument: executing script full path 
the_config = Collector_config(sys.argv[0])

mqtt_handler = MQTTHandler(the_config)
### MQTT Callbacks defined centrally here ####
"""
The callback for when the client receives a CONNACK response from the server.
"""
def _on_mqtt_connect(client, userdata, rc):
    # TODO: May be needed to handle reconnection of all subscribed topics
    #       in case of reconnection...?
    pass

"""
The callback for when a PUBLISH message is received from the server.
"""
def _on_mqtt_message(client, userdata, msg):    
    mqtt_handler.add_to_buffer(msg.topic, str(msg.payload))                

###### End MQTT Callbacks ########
mqtt_handler.init_connect_mqtt(_on_mqtt_connect, _on_mqtt_message)

if the_config.MQTT_RELAYED:
    mqtt2serial = MQTT2Serial(the_config, arg_ser, mqtt_handler)
    mqtt2serial.start()
rrd_if = RRD(the_config)
collector = Collector(the_config, mqtt_handler, rrd_if)
collector.start()
time.sleep(1)
# retriever = EmonRetriever(the_config, collector, rrd_if)
retriever = ThingsboardRetriever(the_config, collector, rrd_if)
retriever.start()

while keep_on:
        time.sleep(2)

retriever.shutdown()
collector.shutdown()
if the_config.MQTT_RELAYED:
    mqtt2serial.shutdown()
print 'Waiting Retriever to exit...'
retriever.join()
print 'Waiting Collector to exit...'
collector.join()
if the_config.MQTT_RELAYED:
    print 'Waiting MQTT2Serial to exit...'
    mqtt2serial.join()

# Exits cleanly
print 'Exiting cleanly, Bye!'

