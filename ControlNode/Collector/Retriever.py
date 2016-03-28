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
from Collector import Collector

# The file holding the serialized last ts sent to the remote DB
LAST_SENT_TS_DAT = 'last_sent_ts.dat'
TIME_WAIT_SYNC = 30

"""
The Retriever class implements the process running on the Control Node
and forwarding measures from the local RRD database to the target
Management Database through the exposed REST interface
"""
class Retriever (threading.Thread):
        
    # The logger facility: activate only if needed
    logger = logging.getLogger('RETRIEVER')

    # The connection established flag
    connected = False
	
    # The static configuration object
    config = None

    #Initializer
    def __init__(self, config, collector, RRD_if):
        threading.Thread.__init__(self)
	Retriever.config = config
	# The RRD interface
	self.__RRD_if = RRD_if
	# The Collector reference
	self.__collector = collector

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
	Retriever.logger.addHandler(hdlr)
	loglevel=eval('logging.' + config.LOG_LEVEL)
	Retriever.logger.setLevel(loglevel)

	# The last timestamp sent to the remote DB
        self.last_sent_ts = 0
	self.keep_on = True


    """
    The thread runner
    """
    def run(self):
        self.connect()
        self._load_last_sent_ts()
        while self.keep_on:
            data_time = self._set_data_time()
            if data_time > 0:
                data_sent = self._retrieve(data_time)
            if data_time == 0 or not data_sent:
                Retriever.logger.info('Retriever sleeps waiting. last_sent_ts is:' + str(self.last_sent_ts))
                time.sleep(Retriever.config.TIME_INTERVAL)

                        
    """
    Abstract connection to the dashboard server
    It should be overridden by classes which require an initial connection
    to the dashboard service.
    Implementing classes must allow that if connection fails,
    the program continues, but will not save measures to the service
    """
    def connect(self):
        Retriever.connected = True

    """
    Initialize the last timestamp for which data has been sent to the remote DB
    from the persistent serialized file 'last_sent_ts.dat'.
    If the file is not present, means that past values are not relevant
    """
    def _load_last_sent_ts(self):
        try:
            f = open(LAST_SENT_TS_DAT)
            self.last_sent_ts = long(pickle.load(f))
            f.close()
            Retriever.logger.info('Last sent timestamp loaded from last_sent_ts.dat:' + str(self.last_sent_ts))
        except:            
            Retriever.logger.warning('File last_sent_ts.dat not found for initialization.')
        

    """
    Determines the timestamp for which measures should be retrieved from the RRD
    and sent to the remot db.
    If 0 is returned, it means that the retriever must wait to get properly
    in sync with the collector
    """
    def _set_data_time(self):
        tm_interval = Retriever.config.TIME_INTERVAL
        # if last_sent_ts has a non zero value, it means that we are:
        # - either at startup with the persistent last timestamp loaded
        # - or at regime functioning
        if self.last_sent_ts > 0:
            if self.last_sent_ts < self.__collector.get_last_collected_ts():
                dt = self.last_sent_ts + tm_interval
            else:
                dt = 0
        else:
            # Otherwise, get in sync with the collector
            # check that at least some data time has been collected
            lct = self.__collector.get_last_collected_ts()
            if lct > 0:
                dt = lct - tm_interval
            else:
                dt = 0
        
        return dt
                

    """
    The main method: retrieves data from the RRD and transfers to database via the HTTP interface
    Data are extracted stored after the last sent timestamp.
    It is assumed that all RRDs are aligned in time. If for any reason a RRD has no data for
    a requested timestamp, that RRD is ignored.
    Only data for one timestamp is sent by each call and then the "last sent timestamp" is updated.
    Returns True if data has been actually sent to the remote server, False otherwise
    """
    def _retrieve(self, data_time):
        retval = False
        # New data is safely present in all RRDs
        Retriever.logger.info('Retrieving measures for timestamp ' + str(data_time) + ' from the RRD')
        measures = self._retrieve_measures_rrd(data_time)
        Retriever.logger.debug('Retrieved measures:' + str(measures))
        if len(measures) > 0:
            if self.push_measures(data_time, measures):
                self.last_sent_ts = data_time
                retval = True
                f = open(LAST_SENT_TS_DAT, 'w')
                pickle.dump(self.last_sent_ts, f)
                f.close()                
            else:
                Retriever.logger.warning('Push to remote server not successful. Last sent timestamp not updated')
        else:
            #If no data was found and the retriever is behind the collector
            #then this was a hole and the return value maust be as if data
            #was actually sent
            if data_time < self.__collector.get_last_collected_ts():
                self.last_sent_ts = data_time
                retval = True
                
        return retval
                
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
        
        for node_id in Retriever.config.get_configured_nodes():
            if tstamp <= self.__RRD_if.get_last_tstamp(node_id):
                retrieved_measures = self.__RRD_if.fetch_measures(node_id, tstamp)
                for meas in retrieved_measures:
                    new_item = dict([('ID_SENSOR',node_id), ('MEAS_TAG',meas[0]), ('VALUE',int(meas[1]))])
                    measures.append(new_item)
            else:
                Retriever.logger.warning('tstamp ' + str(tstamp) + ' to fetch for node ' + node_id + ' is beyond the last data loaded in RRD')
                        
        return measures


    """
     This method MUST be implemented by the extending class.
     Pushes the retrieved measures through the actual interface to
     the dashboard servuce
    """
    def push_measures(self, timestamp, measures):
        return False

    """
     Translates the raw data into data to be stored in the database
     The measure parameter is a measure dictionary (see collect_measures for structure)
     Returns a dictionay that is the initial measure structure as above, enriched with fields:
     t['POSITION']
     t['MEASURED_ITEM']
     t['UNIT']
    """
    def _translate(self, measure) :
        tc_measure = measure
        tc = Retriever.config.get_transcalibration_values(measure['ID_SENSOR'], measure['MEAS_TAG'])
        if tc != None:
            tc_measure['POSITION'] = tc[0]
            tc_measure['MEASURED_ITEM'] = tc[1]
            tc_measure['UNIT'] = tc[2]
            return tc_measure
        else:
            return None

    """
    Causes the thread to exit
    """
    def shutdown(self):
        self.keep_on = False
                
### Retriever class definition ends here

