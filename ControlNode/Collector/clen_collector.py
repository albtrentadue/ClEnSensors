#!/usr/bin/python

"""
 ClENSensors / Control node
 by Alberto Trentadue Dec.2015
 
 The collector process runs on the Control Node and collects 
 measures from the Sensor Nodes.
 It initially sends a broadcast message to discover the sensor nodes in range.
 Then it cyclically queries the sensor nodes for their measures
 and stores them in the local database.
 
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
#"unirest" is imported from the external module unirest / http://unirest.io/python.html
import unirest, json, binascii
#"serial" is imported from the external module pySerial / https://pythonhosted.org/pyserial/
import sys, signal, serial, time, logging
from ConfigParser import ConfigParser

# Constant values
MSG_TERMINATOR = '#'
CONTROL_ID = '001'
BROADCAST_ID = '000'

# Values from configuration
TIME_INTERVAL = 900
MAX_SENSOR_NODES = 30
SERIAL_BAUDRATE = 9600

# Rest server values
REST_SERVER_ADDRESS = 'localhost:8081'
REST_APP_USER = ''
REST_APP_PWD = ''
DF_APP = ''
DF_API_KEY = ''

LOG_TO_FILE = False
LOG_FILE_DEST = ''
LOG_LEVEL = 'INFO'

CFG_DEFAULTS = {
	'to_file' : 'False',
	'log_file_dest' : '/var/tmp/clen_collector.log',
	'log_level' : 'INFO',
	'time_interval' : 900,
	'max_sensor_nodes' : 30,
	'rest_server_address' : '127.0.0.1:8081',
}

# The logger facility: activate only if needed
logger = logging.getLogger('COLLECTOR')

# The list of the IDs of discovered sensor nodes
sensor_nodes = []
# The dictionary of transcalibration items
transcalibrations = {}
# The serial interfacce to communicate to sensors
serial_if = None
# The REST Server session id
rest_session_id = ''
# REST connection flag
rest_connected = False

# The cycle execution flag
keep_on = True

"""
 The SIGTERM & SIGINT signal handler to quit the process 
"""
def signal_handler(_signo, _stack_frame):
	global keep_on, rest_connected
	
	# Closes the serial port if open
	try:
		serial_if.close()
	except:
		pass
	
	# Disconnects from DreamFactory if connected
	if rest_connected:
		try:
			#resp = unirest.delete("http://"+REST_SERVER_ADDRESS+"/api/v2/user/session?session_token="+rest_session_id, headers = {"X-DreamFactory-Application-Name": DF_APP})
			resp = unirest.delete("http://"+REST_SERVER_ADDRESS+"/api/v2/user/session?session_token="+rest_session_id, headers = {})
			logger.info('Successfully disconnected from REST Server')
			#logger.debug('resp.raw_body returned:'+resp.raw_body)
			rest_connected = False
		except:
			logger.warning('Failed to disconnect from to REST Server')
	
	# Causes the endless loop to exit
	keep_on = False

"""
 Load parameters from the cfg file
"""
def load_config():
	global LOG_TO_FILE, LOG_FILE_DEST, LOG_LEVEL, TIME_INTERVAL, MAX_SENSOR_NODES, SERIAL_BAUDRATE, REST_SERVER_ADDRESS, REST_APP_USER, REST_APP_PWD, DF_APP, DF_API_KEY
	
	#Load the configuration file
	config = ConfigParser(CFG_DEFAULTS)
	#Assumes file exists in workdir
	config.read('clen_collector.cfg')
	#Setup the values
	LOG_TO_FILE = config.getboolean('logging','to_file')
	LOG_FILE_DEST = config.get('logging','log_file_dest')
	LOG_LEVEL = config.get('logging','log_level')
	TIME_INTERVAL = config.getint('main','time_interval')
	MAX_SENSOR_NODES = config.getint('main','max_sensor_nodes')
	SERIAL_BAUDRATE = config.getint('main','serial_baud_rate')
	REST_SERVER_ADDRESS = config.get('rest','rest_server_address')
	REST_APP_USER = config.get('rest','rest_app_user')
	REST_APP_PWD = config.get('rest','rest_app_pwd')
	DF_APP = config.get('rest','df_app')
	DF_API_KEY = config.get('rest','df_api_key')
	

"""
 Load the transformation/calibration configuration from the clen_transcalibration.cfg file
 The configuration is stored into the transcalibrations dictionary
 The key of the dictionary is the concatenation <sensor_id><measure_tag>
 The value is a tuple of 5 elements: (<position>,<measured item>,<unit>,<offset>,<mult>)
"""
def load_transcalibration() :
	global transcalibrations
	
	f = open('clen_transcalibration.cfg')
	while True:
		fline=f.readline()
		if fline == '':
			break
		
		l=len(fline)
		if l > 5 and fline[0] != ';':
			#Valid line:
			#removes the ending \n
			if fline[l-1] == '\n':
				s = fline[:l-1]
			else:
				s = fline
			token_list = s.split(',')
			tc_key = token_list[0]+token_list[2]
			tc_value = token_list[1],token_list[3],token_list[4],float(token_list[5]),float(token_list[6])
			transcalibrations[tc_key] = tc_value
			logger.debug('Loaded into transcalibration: key ' + tc_key + ' tuple ' + str(transcalibrations[tc_key]))

# CONTROL NODE SETUP #
def setup():
	global serial_if
	
	# Loads the configuration settings
	load_config()	
	# Use the FileHandler only if need to troubleshoot
	if LOG_TO_FILE:
		try:
			hdlr = logging.FileHandler(LOG_FILE_DEST)
		except:
			hdlr = logging.StreamHandler(sys.stdout)
	else:
		hdlr = logging.StreamHandler(sys.stdout)
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr)
	loglevel=eval('logging.' + LOG_LEVEL)
	logger.setLevel(loglevel)
	
	#Loads the transcalibration settings
	load_transcalibration()
	
	# Takes command line argument: the serial port name
	serial_port = sys.argv[1]
	try:
		# Open the serial communication
		serial_if = serial.Serial(port=serial_port, baudrate=SERIAL_BAUDRATE)
		logger.info('Serial port ' + serial_port + ' created.')
	except:
		logger.error('Error when opening serial:' + str(sys.exc_info()[1]))
		sys.exit(1)
	
	#setup the SIGTERM & SIGINT hook handler
	signal.signal(signal.SIGTERM, signal_handler)
	signal.signal(signal.SIGINT, signal_handler)
	
"""
 Detects the Sensor Nodes in range.
 Sends out a broadcast message asking each sensor to return its ID
 The received ID are stored in the available sensor_nodes list
"""
def discover():
	global sensor_nodes, keep_on
	
	while keep_on :
            logger.info('Starting new discovering cycle')
            #Sends out the broadcast message
            send_command(BROADCAST_ID, 'IDNREQ')
            #Collects the responses. 
            time.sleep(1)
            #Responses are collected for a time interval equal to MAX_SENSOR_NODES + 2	
            time_limit = time.time()+ MAX_SENSOR_NODES + 1
            while keep_on and time.time() < time_limit:
                    rx_msg = receive_msg()
                    if rx_msg != None:
                            discovered_id = rx_msg['SENDER_ID']
                            sensor_nodes.append(discovered_id)
                            logger.info('Discovered sensor node with ID:' + discovered_id)
                    time.sleep(0.2)
            logger.debug('Ending discovering cycle after {0} seconds'.format(MAX_SENSOR_NODES + 2))
            
            if len(sensor_nodes) > 0:
                break
            else:
                    #No sensor found : wait 1 minute
                    logger.info('No sensor found in range. Sleeping 1 minute')
                    time.sleep(60)
		
"""
 Connects to the DreamFactory REST server
 If connection fails, the program continues, but will not save measures to db

"""
def rest_connect():
	global rest_session_id, rest_connected
	
	# Creazione del session_id
	try:
		#resp = unirest.post("http://"+REST_SERVER_ADDRESS+"/api/v2/user/session", headers = {"X-DreamFactory-Application-Name": DF_APP}, params=json.dumps({ "email":REST_APP_USER, "password":REST_APP_PWD, "remember_me": False }))
		resp = unirest.post("http://"+REST_SERVER_ADDRESS+"/api/v2/user/session", headers = {}, params=json.dumps({ "email":REST_APP_USER, "password":REST_APP_PWD, "remember_me": False }))
		rest_session_id=json.loads(resp.raw_body)["session_id"]
		logger.info('Successfully authenticated with DreamFactory. Session ID:' + rest_session_id)
		rest_connected = True
	except:
		logger.debug('resp.raw_body returned:'+resp.raw_body)
		logger.warning('Failed to connect to REST Server. Measures will not be stored in DB')

# MAIN LOOP #
def loop():
	data_time = align_time()
	logger.info('Collecting measures for timestamp {0}.'.format(data_time))
	measures = collect_measures()
	if len(measures) > 0:
		store_measures(data_time, measures)


"""
 Waits until the current time is an integral multiple of the
 configured granularity. 
 Returns the time (as long) that will be used as timestamp of measures
"""
def align_time():
	#Wait at least 1 second to avoid double alignments
	time.sleep(1)
	
	logger.info('Waiting the next {0} secs interval start'.format(TIME_INTERVAL))
	while True:
		dm = divmod(time.time(), TIME_INTERVAL)
		if long(dm[1]) == 0L:
			break
		time.sleep(0.5)
	
	return long(dm[0] * TIME_INTERVAL)

"""
 Queries the active sensors and collects the available measures from them.
 Returns a list of structures (dictionary) where elements are:
 t['ID_SENSOR']: sensor id
 t['MEAS_TAG']: measure tag
 t['VALUE']: measure value (int)
"""
def collect_measures():
	measures = []
	
	for sn in sensor_nodes :
		send_command(sn, 'QRYMSR')
		time.sleep(1)
		rx_msg = receive_msg()
		if rx_msg != None:
			sensor_measures = extract_measures(rx_msg['MSG_DATA'])
			for meas in sensor_measures:
				new_item = dict([('ID_SENSOR',sn), ('MEAS_TAG',meas[0]), ('VALUE',int(meas[1]))])
				measures.append(new_item)
			
	return measures

"""
 Extrct the measures from the data part of the message
 Returns a list of pairs (measure tag string, value as string)
"""
def extract_measures(data_part):
	measures = []
	
	meas_list = data_part.split(':')
	#now each element of the lits is a string '<TT><VALUE>'
	#where TT is a 2 chars tag
	for meas in meas_list:
		tag = meas[0:2]
		value = meas[2:]
		measures.append((tag,value))
	
	return measures

"""
 Stores the received measures through the REST iterface
 exposed by the REST API provider (DreamFactory)
"""
def store_measures(timestamp, measures):
	for measure in measures :
		tc_measure = trans_calibrate(measure)
		#Store to DB via REST API here
		logger.debug('Measure record to be stored:' + str(tc_measure))
		if rest_connected :
			#Prepare the record
			rec={}
			rec["timestamp"] = timestamp
			rec["id_sensore"] = int(tc_measure['ID_SENSOR'])
			rec["posizione"] = tc_measure['POSITION']
			rec["misura"] = tc_measure['MEASURED_ITEM']
			rec["unita"] = tc_measure['UNIT']
			rec["valore"] = tc_measure['VALUE'] #float
			
			rest_sensors_api={}
			rest_sensors_api["resource"]=rec
			# Store data into DB via REST
			#resp = unirest.post("http://" + REST_SERVER_ADDRESS +"/api/v2/thcsensors/_table/thc_misure?api_key="+DF_API_KEY+"&session_token="+rest_session_id, headers = {"X-DreamFactory-Application-Name": DF_APP, "X-DreamFactory-Session-Token": rest_session_id}, params=json.dumps(rest_sensors_api))
			resp = unirest.post("http://" + REST_SERVER_ADDRESS +"/api/v2/thcsensors/_table/thc_misure?api_key="+DF_API_KEY+"&session_token="+rest_session_id, headers = {}, params=json.dumps(rest_sensors_api))
			logger.debug('REST Record stored in DB:' + str(rec))
		else:
			logger.info('Measures not stored because connection to REST server is not available.')

"""
 Translates the raw data into data to be stored in the database
 Also, calibrate the measures according to the defined calibration settings
 The measure parameter is a measure dictionary (see collect_measures for structure)
 Returns a dictionay that is the initial measure structure as above, enriched with fields:
 t['POSITION']
 t['MEASURED_ITEM']
 t['UNIT']
"""
def trans_calibrate(measure) :
	tc_measure = measure
	mkey = measure['ID_SENSOR']+measure['MEAS_TAG']
	if mkey in transcalibrations.keys():
		tc = transcalibrations[mkey]
		tc_measure['POSITION'] = tc[0]
		tc_measure['MEASURED_ITEM'] = tc[1]
		tc_measure['UNIT'] = tc[2]
		tc_measure['VALUE'] = measure['VALUE'] * tc[4] + tc[3]
	else:
		tc_measure['POSITION'] = 'UNKNOWN'
		tc_measure['MEASURED_ITEM'] = 'NUMBER'
		tc_measure['UNIT'] = 'N'
		tc_measure['VALUE'] = float(measure['VALUE'])
	
	return tc_measure

"""
 Sends a string command to nodes via the serial interface
"""
def send_command(dest, cmd): 
	msg = MSG_TERMINATOR + CONTROL_ID + dest + cmd + MSG_TERMINATOR
	logger.debug('Sending:' + msg + ' to ' + dest)
	
	try:
		serial_if.write(msg)
		serial_if.flush()
	except:
		logger.error('Error when writing to serial:' + str(sys.exc_info()[1]))
	

"""
 Receives a new message from the serial source
 Returns a dictionary where elements are:
 m['SENDER_ID']: the id of the sender
 m['DEST_ID']: the id of the destination
 m['MSG_TYPE']: the message type
 m['MSG_DATA']: the data payload
"""
def receive_msg():
	#Empty string if nothing arrived
	rx_ser = ''
	msg = None
			
	try:
		while serial_if.inWaiting() > 0:
			rx_ser += serial_if.read(1)
			#time.sleep(0.01)
	except:
		logger.error('Error when reading from serial:' + str(sys.exc_info()[1]))
		
	l = len(rx_ser)
	if l > 0:
		if rx_ser[0] != MSG_TERMINATOR or rx_ser[l-1] != MSG_TERMINATOR:
			logger.warning('Received incomplete message:' + rx_ser + '. Ignored.')
		else:
			logger.debug('Received message:' + rx_ser)
			msg = dict([('SENDER_ID', rx_ser[1:4]), ('DEST_ID', rx_ser[4:7]), ('MSG_TYPE', rx_ser[7:13]), ('MSG_DATA', '')])
			if l>14:
				msg['MSG_DATA'] = rx_ser[13:l-1]
				
	if msg != None :
		logger.debug('Messages fields:' + str(msg))
		
	return msg


"""
Execution start
"""
setup()
discover()
rest_connect()
while keep_on:
	loop()

# Exits cleanly
logger.info('Exiting cleanly, Bye!')

