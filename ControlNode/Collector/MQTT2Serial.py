#!/usr/bin/python

"""
 ClEnSensors / Control node / the MQTT2Serial relayer 
 by Alberto Trentadue Sept.2016
 
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

#"serial" is imported from the external module pySerial / https://pythonhosted.org/pyserial/
import sys, serial, time, threading
import logging
from logging.handlers import TimedRotatingFileHandler

# Constant values
MSG_TERMINATOR = '#'
CONTROL_ID = '001'
BROADCAST_ID = '000'

"""
 This Class implements a message relayer  that listens for messages
 coming from a defined MQTT Broker and relays them over a serial communication (tty)
 Then it waits for the responses over the same serial connections and
 dispatches the messages to the appropriate MQTT topic 
"""
class MQTT2Serial (threading.Thread):

    # The logger facility: activate only if needed
    __logger = logging.getLogger('MQTT2SERIAL')
    
    # The static configuration object
    __config = None

    # The application MQTT Handler
    __mqtt_handler = None    

    #Initializer
    def __init__(self, config, serial_port, mqtt_handler):
        threading.Thread.__init__(self)
        MQTT2Serial.__config = config
        # The Relayed mode subcribes to a single topic for all nodes
        mqtt_handler.add_subscription('clen/serial')
        MQTT2Serial.__mqtt_handler = mqtt_handler
        # The serial interface to communicate to sensors
        self.__serial_port = serial_port
        self.serial_if = None

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
        MQTT2Serial.__logger.addHandler(hdlr)
        loglevel=eval('logging.' + config.LOG_LEVEL)
        MQTT2Serial.__logger.setLevel(loglevel)

        # The cycle switch
        self.keep_on = True
        
    """
    The thread runner
    """
    def run(self):
        self._create_serial()
        while self.keep_on:
            self._serve_message()


    """
    Receives a message from the MQTT server and serves it
    according to the header directives
    The received message is a list made by:
    0: receiving topic
    1: the message purpose
    2: the topic to use to forward the responses
    3: the time to wait for getting responses
    4: the messsage to forward
    """
    def _serve_message(self):
        msg_fields = MQTT2Serial.__mqtt_handler.receive_mqtt_msg('clen/serial')
        if len(msg_fields):
            MQTT2Serial.__logger.debug('Header fields:' + str(msg_fields))
            if msg_fields[1] == 'COMMAND' :
                self._serve_command(msg_fields[2], int(msg_fields[3]), msg_fields[4])
        else:
            time.sleep(0.2)

    """
    Forwards a message to the nodes through the serial interface.
    Then waits for a certain amount of time for the responses and
    returns the responses via MQTT to the reply topic
    """
    def _serve_command(self, reply_topic, wait_time, msg):
        self._send_to_serial(msg);
        #Wait some time before checking serial responses
        #time.sleep(0.2)  ## TUNE here!
        #then gets the responses for a given time wait
        time_limit = time.time() + (float(wait_time)/1000.0)
        while self.keep_on and time.time() < time_limit:
            time.sleep(0.2)
            MQTT2Serial.__logger.debug('Checking the serial for response')
            rx_msg = self._receive_from_serial()
            MQTT2Serial.__logger.debug('Response was:' + rx_msg)
            if len(rx_msg):
                MQTT2Serial.__logger.debug('Relaying serial message:' + rx_msg)
                MQTT2Serial.__mqtt_handler.send_mqtt_message_with_header(rx_msg, reply_topic, 'RESPONSE', '', 0)


    """
    Open the serial communication to connected serial communication device
    """
    def _create_serial(self): 
        #Serial setup
        try:
            # Open the serial communication
            self.serial_if = serial.Serial(port=self.__serial_port, baudrate=MQTT2Serial.__config.SERIAL_BAUDRATE)
            MQTT2Serial.__logger.info('Serial port ' + self.__serial_port + ' created.')
        except:
            MQTT2Serial.__logger.error('Error when opening serial:' + str(sys.exc_info()[1]))
            sys.exit(1)
            
    """
    Sends a string command to nodes via the serial interface
    """
    def _send_to_serial(self, msg): 
        MQTT2Serial.__logger.debug('Sending:' + msg + ' via serial')            
        try:
            self.serial_if.write(msg)
            self.serial_if.flush()
        except:
            MQTT2Serial.__logger.error('Error when writing to serial:' + str(sys.exc_info()[1]))

    """
    Receives a new message from the serial source
    Returns the string received from the serial interface
    """
    def _receive_from_serial(self):
        #Empty string if nothing arrived
        rx_ser = ''                            
        try:
            while self.serial_if.inWaiting() > 0:
                rx_ser += self.serial_if.read(1)
                time.sleep(0.001)
        except:
            MQTT2Serial.__logger.error('Error when reading from serial:' + str(sys.exc_info()[1]))

        #Here the sequence of characters has been received
        #Strip possible newlines
        rx_ser = rx_ser.rstrip("\n\r")
        l = len(rx_ser)
        if l > 0:
            if rx_ser[0] != MSG_TERMINATOR or rx_ser[l-1] != MSG_TERMINATOR:
                MQTT2Serial.__logger.warning('Received incomplete message:' + rx_ser + '. Ignored.')
                MQTT2Serial.__logger.warning('Last char code was:' + str(ord(rx_ser[l-1])))
                #FIXED: Ignoring means empty the message
                rx_ser = ''
            else:
                MQTT2Serial.__logger.debug('Received message:' + rx_ser)

        return rx_ser


    """
    Causes the thread to exit
    """
    def shutdown(self):
        self.keep_on = False


### MQTT2Serial class definition ends here
