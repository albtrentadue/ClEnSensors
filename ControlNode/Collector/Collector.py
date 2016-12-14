"""
 ClEnSensors / Control node / Collector object
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

#"serial" is imported from the external module pySerial / https://pythonhosted.org/pyserial/
import sys, time, threading, copy
import logging
from logging.handlers import TimedRotatingFileHandler

# Constant values
MSG_TERMINATOR = '#'
CONTROL_ID = '001'
BROADCAST_ID = '000'

"""
 The Collector Class implements the process running on the Control Node and collecting 
 measures from the Sensor Nodes.
 It initially sends a broadcast message to discover the sensor nodes in range.
 Then it cyclically queries the sensor nodes for their measures
 and stores them in the local RRD database.
 
 The collector should be a singleton object
"""
class Collector (threading.Thread):

    # The logger facility: activate only if needed
    __logger = logging.getLogger('COLLECTOR')
    
    # The static configuration object
    __config = None

    # The application MQTT Handler
    __mqtt_handler = None

    #Initializer
    def __init__(self, config, mqtt_handler, RRD_if):
        threading.Thread.__init__(self)
        Collector.__config = config
        mqtt_handler.add_subscription('clen/collector')
        Collector.__mqtt_handler = mqtt_handler
        # The RRD interface
        self.__RRD_if = RRD_if
        
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
        Collector.__logger.addHandler(hdlr)
        loglevel=eval('logging.' + config.LOG_LEVEL)
        Collector.__logger.setLevel(loglevel)

        #Initialization of the dictionary with unknowns
        self.empty_measures = {}
        for nd in config.get_configured_nodes():
            self.empty_measures[nd] = {tg : 'U' for tg in config.get_configured_tags_by_node(nd)}

        # MQTT relays to serial or not
        self.mqtt_relayed_to_serial = config.MQTT_RELAYED_TO_SERIAL
        # The list of the IDs of discovered sensor nodes
        self.sensor_nodes = []
        # The last collected timestamp
        self.last_collected_ts = 0
        # The thread safety lock
        self.collector_lock = threading.Lock()
        # The cycle switch
        self.keep_on = True

    """
    The thread runner
    """
    def run(self):
        self._discover()
        self._send_configs()
        while self.keep_on:
            self._fetch()

    """
    Detects the Sensor Nodes in range.
    Sends out a broadcast message asking each sensor to return its ID
    The received ID are stored in the available sensor_nodes list.
    Once a node is discovered, the Collector sends a configuration message
    communicating the time granularity configured in the system.
    """
    def _discover(self):
        while self.keep_on :
            Collector.__logger.info('Starting new discovering cycle')
            #Sends out the broadcast message
            discover_wait = 2 * (Collector.__config.MAX_SENSOR_NODES + 3)
            self._send_command(BROADCAST_ID, 'IDNREQ', '', discover_wait * 1000)
            time_limit = time.time()+ discover_wait
            while self.keep_on and time.time() < time_limit:
                time.sleep(0.2)
                rx_msg = self._receive_msg()
                if rx_msg != None:
                    discovered_id = rx_msg['SENDER_ID']
                    if not discovered_id in self.sensor_nodes:
                        self.sensor_nodes.append(discovered_id)
                        Collector.__logger.info('Discovered new sensor node with ID:' + discovered_id)
                    else:
                        Collector.__logger.warning('Anomaly: duplicate discovery of node:' + discovered_id)
                        
            Collector.__logger.debug('Ending discovering cycle after {0} seconds'.format(discover_wait))			
            
            if len(self.sensor_nodes) > 0:
                break
            else:
                #No sensor found : wait some time
                Collector.__logger.info('No sensor found in range. Waiting ...')
                for i in range(15):
                    time.sleep(2)
                    if not self.keep_on:
                        break

        if len(set(self.sensor_nodes) - set(Collector.__config.get_configured_nodes())) > 0:
                Collector.__logger.debug('Some discovered nodes are not present in the Transcalibration config file. Exiting')
                sys.exit(1)

    """
    Sends the configuration message to all discovered nodes,
    containing the currently supported configuration info:
    TG: time granularity configured for the system
    """
    def _send_configs(self):
        for node_id in self.sensor_nodes:
            Collector.__logger.info('Sending the config message to node ' + node_id)
            #Sends the CONFIG message
            self._send_command(node_id, 'CONFIG', 'TG'+str(Collector.__config.TIME_INTERVAL / 60), 600)
            # Wait for a time after which there must be the answer, otherwise there is a problem!
            time.sleep(0.8)
            rx_msg = self._receive_msg()
            if rx_msg != None:
                if rx_msg['MSG_TYPE'] == 'CFGACK' and rx_msg['SENDER_ID'] == node_id:
                    #Only a basic logging for now...
                    Collector.__logger.info('Node ' + node_id + ' successfully configured.')
            else:
                Collector.__logger.error('No response received after sending config message')
                
                        
    """
    Fetches data from the sensors
    """
    def _fetch(self):
        data_time = self._align_time()
        Collector.__logger.info('Collecting measures for timestamp {0}.'.format(data_time))
        measures = self._collect_measures()
        self._store_measures_rrd(data_time, measures)
        self.collector_lock.acquire()
        self.last_collected_ts = data_time
        self.collector_lock.release()

    """
     Returns the last collected ts whose data have been insterted in the RRD
     This is a thread synchronisation method
    """
    def get_last_collected_ts(self):
        self.collector_lock.acquire()
        lct = self.last_collected_ts
        self.collector_lock.release()
        return lct

    """
    Waits until the current time is an integral multiple of the
    configured granularity. 
    Returns the time (as long) that will be used as timestamp of measures
    """
    def _align_time(self):
        tm_interval = Collector.__config.TIME_INTERVAL
        #Wait at least 1 second to avoid double alignments
        time.sleep(1)
        
        Collector.__logger.info('Waiting the next {0} secs interval start'.format(tm_interval))
        while True:
            dm = divmod(time.time(), tm_interval)
            if long(dm[1]) == 0L:
                break
            time.sleep(0.5)
        
        return long(dm[0] * tm_interval)

    """
    Queries the active sensors and collects the available measures from them.
    Returns a dictionary with the node_id as key and a list of pairs (meas_tag, value as string) as value.
    
    Each RRD created for a node must always receive the same amount of values
    to feed the data sources defined in it, either actual values or UNKNOWN.
    To do ths, the returned dictionary is initialized with all UNKNOWN and they are replaced
    by  values if thei are extracted from the messages	
    """
    def _collect_measures(self):
        #Initialization to empty
        measures = copy.deepcopy(self.empty_measures)

        for sn in self.sensor_nodes :                        
            self._send_command(sn, 'QRYMSR')
            time.sleep(0.8)
            rx_msg = self._receive_msg()
            if rx_msg != None:
                valued_measures = self._calibrate(sn, self._extract_measures(rx_msg['MSG_DATA']))
                for tg in valued_measures.keys():
                    measures[sn][tg] = valued_measures[tg]

        return measures

    """
    Extract the measures from the data part of the message received from a node. 
    Returns a dictionary: measure tag as key, value_as_string as value
    """
    def _extract_measures(self, data_part):
        measures = {}
        
        meas_list = data_part.split(':')
        #now each element of the lits is a string '<TT><VALUE>'
        #where TT is a 2 chars tag
        for meas in meas_list:
            tag = meas[0:2]
            value = meas[2:]
            measures[tag] = value
        
        return measures

    """
    Calibrate the measures based on the transcalibration configuration.
    Takes the node id and dictionary of measures (tag as key, value_as_string as value).
    Returns the same dictionary, but with calibrated values
    """
    def _calibrate(self, node_id, measures):
        for tg in measures.keys():                        
            tc = Collector.__config.get_transcalibration_values(node_id, tg)
            if tc != None:
                measures[tg] = str(int(measures[tg]) * tc[4] + tc[3])                                
            else:
                Collector.__logger.warning('Tag ' + tg + ' is not configured for node ' + node_id + ': measure will be dropped.')
                del measures[tg]

        return measures

    """
    Stores the received measures into the RRD database used as a local measure buffer.
    Takes the timestamp and the current dictionary of collected measures
    """
    def _store_measures_rrd(self, timestamp, measures):                
        for node_id in measures.keys():
            self.__RRD_if.store_measures(timestamp, node_id, measures[node_id])                        

    """
    Sends a string command to nodes via MQTT
    Topic to be used is "nodes"
    """
    def _send_command(self, dest, cmd, msg_data='', resp_wait=600): 
        msg = MSG_TERMINATOR + CONTROL_ID + dest + cmd + msg_data + MSG_TERMINATOR
        Collector.__logger.debug('Sending:' + msg + ' to ' + dest)
        if self.mqtt_relayed_to_serial:
            # If relayed on serial communication, destination is parsed from the payload
            # and the use of a specific topic per node is not needed
            Collector.__mqtt_handler.send_mqtt_message_with_header(msg, 'clen/serial', 'COMMAND', 'clen/collector', resp_wait)
	else:
            Collector.__mqtt_handler.send_mqtt_message(msg, 'clen/nodes/' + dest)

    """
    Receives a new message from nodes through MQTT
    Returns a dictionary where elements are:
    m['SENDER_ID']: the id of the sender
    m['DEST_ID']: the id of the destination
    m['MSG_TYPE']: the message type
    m['MSG_DATA']: the data payload
    """
    def _receive_msg(self):
        msg = None
        msg_fields = Collector.__mqtt_handler.receive_mqtt_msg('clen/collector')
        if len(msg_fields):
            Collector.__logger.debug('Header fields:' + str(msg_fields))
            if msg_fields[1] == 'RESPONSE' :
                rx_msg = msg_fields[4]
                msg = dict([('SENDER_ID', rx_msg[1:4]), ('DEST_ID', rx_msg[4:7]), ('MSG_TYPE', rx_msg[7:13]), ('MSG_DATA', '')])
                l = len(rx_msg)
                if l>14:
                    msg['MSG_DATA'] = rx_msg[13:l-1]

        if msg != None:
            Collector.__logger.debug('Message list:' + str(msg))
            
        return msg

    """
    Causes the thread to exit
    """
    def shutdown(self):
        self.keep_on = False

### Collector class definition ends here

