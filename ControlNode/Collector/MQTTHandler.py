"""
 ClEnSensors / Control node / MQTT communication handler
 by Alberto Trentadue Dec.2015
 
 Copyright Alberto Trentadue 2015, 2016
 
 This file is part of ClENSensors.

 ClEnSensors is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 ClEnSensors is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with ClEnSensors.  If not, see <http://www.gnu.org/licenses/>.
"""


import sys, time
import logging
from logging.handlers import TimedRotatingFileHandler
import paho.mqtt.client as mqtt
import Queue

"""
 The MQTT Handler Class implements the interface towards MQTT Broker operation.
 It hides the details of the MQTT interaction to other components
 IMPORTANT NOTE: The MQTTHandler singleton must be used for this object in order to work
       The Paho callbacks need static methods and they can only use one single
       instance of the _MQTTHandler_class
"""
class MQTTHandler :

    # The static configuration object
    __config = None

    # The logger facility: activate only if needed
    __logger = logging.getLogger('MQTTHandler')
    
    # The MQTT client instance
    # protocol 3 ensures that old Mosquitto 0.15 version is supported
    __mqttc = mqtt.Client(protocol=3) 

    # The message buffers for subscribed topics
    __mqtt_buffers = {}

    #Explicit Initializer
    def __init__(self, config):        
        MQTTHandler.__config = config        
        
        # Logger setup: use the FileHandler only if need to troubleshoot
        if config.LOG_TO_FILE:
            try:
                hdlr = TimedRotatingFileHandler(config.LOG_FILE_DEST, 'D', 1, 1)
            except:
                hdlr = logging.StreamHandler(sys.stdout)
        else:
            hdlr = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        MQTTHandler.__logger.addHandler(hdlr)
        loglevel=eval('logging.' + config.LOG_LEVEL)
        MQTTHandler.__logger.setLevel(loglevel)
        self.mqtt_ip = config.MQTT_SERVER_ADDRESS

    """
    Initializes and connect to the MQTT Broker
    """
    def init_connect_mqtt(self, on_connect, on_message):
        MQTTHandler.__mqttc.on_connect = on_connect
        MQTTHandler.__mqttc.on_message = on_message

        #connect to the MQTT broker on, the controller
	#this connect is blocking.
	# No IP parsing at the moment - FUTURE
	broker_connected=False
	MQTTHandler.__logger.info('Trying to connect MQTT broker at ' + self.mqtt_ip)
	while not broker_connected:
            try:
                MQTTHandler.__mqttc.connect(MQTTHandler.__config.MQTT_SERVER_ADDRESS, MQTTHandler.__config.MQTT_PORT, 60)
                MQTTHandler.__logger.debug('Connected to MQTT broker on ' + MQTTHandler.__config.MQTT_SERVER_ADDRESS)
                broker_connected = True
	    except:
		pass #do nothing
	    time.sleep(1)
	    
	# Threaded call for MQTT handling
	MQTTHandler.__mqttc.loop_start()
	MQTTHandler.__logger.info('MQTT loop started')

    """
    Creates the subscription to a topic and the related queue
    to collect the messages returned on that topic
    """
    def add_subscription(self, topic):
        MQTTHandler.__mqttc.subscribe(topic)
        MQTTHandler.__logger.info('Added MQTT subscription on topic ' + topic)


    """
    Sends a message via MQTT on a given topic 
    """
    def send_mqtt_message(self, msg, topic):                         
        MQTTHandler.__mqttc.publish(topic, msg)
        MQTTHandler.__logger.info('Published:' + msg + ' on topic ' + topic)

    """
    Sends a message via MQTT with a relayer header
    It prepares the header and prepends it to the message according
    to the "clen" MQTT header format definition
    - purpose is an info indicating the reason for the message (if needed)
    - topic is the topic to publish to
    - delay_for_reply is the time in ms to wait if a synchronous reply is expected. -1 means NOT expected 
    """
    def send_mqtt_message_with_header(self, msg, topic, purpose, reply_topic, delay_for_reply=-1):                 
        msg_to_send = purpose + ';' + reply_topic + ';' + str(delay_for_reply) + ';' +  msg
        MQTTHandler.__mqttc.publish(topic, msg_to_send)
        MQTTHandler.__logger.info('Published:' + msg_to_send + ' on topic ' + topic)

    """
    Stores a message received by the MQTT Client into the
    appropriate topic queue
    """
    def add_to_buffer(self, topic, message):
        MQTTHandler.__logger.info('Message received from MQTT server:' + topic + ' : ' + message)
        if not topic in MQTTHandler.__mqtt_buffers:
            # if there is no buffer queue for this topic, one is created
            # this makes the code more robust
            msgq = Queue.Queue()
            MQTTHandler.__mqtt_buffers[topic] = msgq

        MQTTHandler.__mqtt_buffers[topic].put(message)
            

    """
    Retrieves the first available message from MQTT for a given topic
    Returns a list made by:
    0: receiving topic
    1: the message purpose
    2: the topic to use to forward the returned responses
    3: the time to wait for getting responses
    4: the messsage to forward
    """
    def receive_mqtt_msg(self, topic):
        header_fields = []
    	#Empty list of fields if nothing arrived
        if topic in MQTTHandler.__mqtt_buffers:
            msgq = MQTTHandler.__mqtt_buffers[topic]
            if not msgq.empty():
                new_msg = msgq.get_nowait() 
                MQTTHandler.__logger.info('Popped up from topic '+ topic +' queue:' + new_msg)
                header_fields = [topic] + new_msg.split(';')
            
        return header_fields

### MQTTHandler class definition ends here
 
