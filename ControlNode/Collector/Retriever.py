"""
 ClENSensors / Control node
 by Alberto Trentadue Dec.2015
 
 The Retriever Object
 
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

import sys, time, logging, pickle, threading
#"unirest" is imported from the external module unirest / http://unirest.io/python.html
import unirest, json, binascii

# The file holding the serialized last ts sent to the remote DB
LAST_SENT_TS_DAT = 'last_sent_ts.dat'

"""
The Retriever class implements the process running on the Control Node
and forwarding measures from the local RRD database to the target
Management Database through the exposed REST interface
"""
class Retriever (threading.Thread):
        
        # The logger facility: activate only if needed
	__logger = logging.getLogger('RETRIEVER')
	
	# The static configuration object
	__config = None	

	# The cycle switch
	__keep_on = True

        # The REST Session ID
	__rest_session_id = ''

        # The connection flag
	__rest_connected = False

	# The last timestamp sent to the remote DB
	__last_sent_ts = 0

	# The "first run" flag
	__first_run = False

	# The cycle switch
	__keep_on = True

	#Initializer
	def __init__(self, config, RRD_if):
                threading.Thread.__init__(self)
		self.__config = config
		# The RRD interface
		self.__RRD_if = RRD_if		

		# Logger setup: use the FileHandler only if need to troubleshoot
		if config.LOG_TO_FILE:
			try:
				hdlr = logging.FileHandler(config.LOG_FILE_DEST)
			except:
				hdlr = logging.StreamHandler(sys.stdout)
		else:
			hdlr = logging.StreamHandler(sys.stdout)
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		hdlr.setFormatter(formatter)
		self.__logger.addHandler(hdlr)
		loglevel=eval('logging.' + config.LOG_LEVEL)
		self.__logger.setLevel(loglevel)


        """
        The thread runner
        """
        def run(self):
                self._rest_connect()
                self._load_last_sent_ts()
                while self.__keep_on:
                        data_time = self._set_data_time()
                        # From the scheduled data time, wait 1 second for each configured node.
                        # This gives time to the Collector to query all the nodes and fill the RRD
                        while self.__keep_on and (time.time() - data_time) < len(self.__config.get_configured_nodes()):
                                # self.__logger.debug('Waiting for next data timestamp:' + str(data_time))
                                time.sleep(1)
                        if self.__keep_on:
                                self._retrieve(data_time)
                        
        """
        Connects to the DreamFactory REST server
        If connection fails, the program continues, but will not save measures to db
        """
        def _rest_connect(self):
                resp = ''
                # Creazione del session_id
                try:
                        #resp = unirest.post("http://"+REST_SERVER_ADDRESS+"/api/v2/user/session", headers = {"X-DreamFactory-Application-Name": DF_APP}, params=json.dumps({ "email":REST_APP_USER, "password":REST_APP_PWD, "remember_me": False }))
                        resp = unirest.post("http://"+self.__config.REST_SERVER_ADDRESS+"/api/v2/user/session", headers = {}, params=json.dumps({ "email":self.__config.REST_APP_USER, "password":self.__config.REST_APP_PWD, "remember_me": False }))
                        self.__rest_session_id=json.loads(resp.raw_body)["session_id"]
                        self.__logger.info('Successfully authenticated with DreamFactory. Session ID:' + self.__rest_session_id)
                        self.__rest_connected = True
                except:
                        self.__logger.warning('Failed to connect to REST Server. Measures will not be forwarded and stored in local RRD')


        """
        Loads the last timestamp for which data has been sent to the remote DB.
        It loads it from the serialized file 'last_sent_ts.dat'.
        If the file is not present, means that this is the 1st run after installation
        and the first_run flag is set to True
        """
        def _load_last_sent_ts(self):
                try:
                        f = open(LAST_SENT_TS_DAT)
                        self.__last_sent_ts = long(pickle.load(f))
                        f.close()
                        self.__logger.info('Last sent timestamp loaded from last_sent_ts.dat:' + str(self.__last_sent_ts))
                except:
                        self.__first_run = True
                        self.__logger.warning('File last_sent_ts.dat not found for initialization.')
        

        """
        Determines the timestamp for which measures should be retrieved from the RRD
        and sent to the remot db.
        """
        def _set_data_time(self):
                tm_interval = self.__config.TIME_INTERVAL
                if self.__first_run or self.__last_sent_ts == 0:
                        #At the 1st run, the next data timestamp is the nearest timestamp
                        #aligned to the granularity in the future
                        dm = divmod(time.time(), tm_interval)
                        dt = long(dm[0] * tm_interval) + tm_interval
                        self.__first_run = False
                else:
                        #If this is not the 1st run, then self.__last_sent_ts has a valid value
                        #The next data timestamp shall be retrieved
                        dt = self.__last_sent_ts + tm_interval
                
                return dt
                

        """
        The main method: retrieves data from the RRD and transfers to database via REST
        Data are extracted stored after the last sent timestamp.
        It is assumed that all RRDs are aligned in time. If for any reason a RRD has no data for
        a requested timestamp, that RRD is ignored.
        Only data for one timestamp is sent by each call and then the "last sent timestamp" is updated.
        """
        def _retrieve(self, data_time):                
                # New data is safely present in all RRDs
                self.__logger.info('Retrieving measures for timestamp ' + str(data_time) + ' from the RRD')
                measures = self._retrieve_measures_rrd(data_time)
                if len(measures) > 0:
                        if self._push_measures(data_time, measures):
                                self.__last_sent_ts = data_time
                                f = open(LAST_SENT_TS_DAT, 'w')
                                pickle.dump(self.__last_sent_ts, f)
                                f.close()
                        else:
                                self.__logger.warning('Push to remote server not successful. Last sent timestamp not updated')
                
                
        """
         Retrieves the measures from the RRD buffer database.
         Starts from the last sent timestamp for all the configured RRD and sends the available measures
         until all the RRDs have been scanned up to the latest timestamp
         
         Returns a list of structures (dictionary) where elements are:
         t['ID_SENSOR']: sensor id
         t['MEAS_TAG']: measure tag
         t['VALUE']: measure value (int)
        """
        def _retrieve_measures_rrd(self, tstamp):
                measures = []
                
                for node_id in self.__config.get_configured_nodes() :
                        if tstamp <= self.__RRD_if.get_last_tstamp(node_id):
                                self.__logger.debug('Fetching RRD for node ' + node_id + ' tstamp ' + str(tstamp))
                                retrieved_measures = self.__RRD_if.fetch_measures(node_id, tstamp)
                                for meas in retrieved_measures:
                                        new_item = dict([('ID_SENSOR',node_id), ('MEAS_TAG',meas[0]), ('VALUE',int(meas[1]))])
                                        measures.append(new_item)
                        else:
                                self.__logger.warning('tstamp ' + str(tstamp) + ' to fetch for node ' + node_id + ' is beyond the last data loaded in RRD')
                                
                return measures


        """
         Pushes the retrieved measures through the REST iterface
         exposed by the REST API provider (DreamFactory)
        """
        def _push_measures(timestamp, measures):
                retval = False
                if self.__rest_connected :
                        for measure in measures :
                                tc_measure = self._trans_calibrate(measure)
                                #Store to DB via REST API here
                                self.__logger.debug('Measure record to be posted:' + str(tc_measure))
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
                                try:
                                        resp = unirest.post("http://" + REST_SERVER_ADDRESS +"/api/v2/thcsensors/_table/thc_misure?api_key="+DF_API_KEY+"&session_token="+rest_session_id, headers = {}, params=json.dumps(rest_sensors_api))
                                        self.__logger.debug('REST Record posted to DB:' + str(rec))
                                        retval = True
                                except:
                                        self.__logger.error('REST Record post failed. Response was ' + resp)
                else:
                        self.__logger.info('Measures not posted because connection to REST server is not available.')
                                
                return retval

        """
         Translates the raw data into data to be stored in the database
         Also, calibrate the measures according to the defined calibration settings
         The measure parameter is a measure dictionary (see collect_measures for structure)
         Returns a dictionay that is the initial measure structure as above, enriched with fields:
         t['POSITION']
         t['MEASURED_ITEM']
         t['UNIT']
        """
        def _trans_calibrate(measure) :
                tc_measure = measure
                tc = self.__config.get_transcalibration_values(measure['ID_SENSOR'], measure['MEAS_TAG'])
                
                tc_measure['POSITION'] = tc[0]
                tc_measure['MEASURED_ITEM'] = tc[1]
                tc_measure['UNIT'] = tc[2]
                tc_measure['VALUE'] = measure['VALUE'] * tc[4] + tc[3]
                
                return tc_measure

        """
        Causes the thread to exit
        """
        def shutdown(self):
                self.__keep_on = False
                
### Retriever class definition ends here

