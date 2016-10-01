"""
 ClENSensors / Control node
 by Alberto Trentadue Dec.2015
 
 The RRD Database representation object
 
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

#"rrdtool" is imported from the external module python-rrdtool / https://pypi.python.org/pypi/python-rrdtool
import rrdtool, threading, sys
import logging
from logging.handlers import TimedRotatingFileHandler

"""
 The RRD class implements the centralised interface to the RRD database.
 It also ensures that there is no race condition between threads accessing the
 same RRD database
"""

class RRD ():

    # The logger facility: activate only if needed
    __logger = logging.getLogger('RRD')

    # The static configuration object
    __config = None

    # The thread safety lock
    __RRDlock = threading.Lock()

    #Initializer
    def __init__(self, config):
        RRD.__config = config

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
        RRD.__logger.addHandler(hdlr)
        loglevel=eval('logging.' + config.LOG_LEVEL)
        RRD.__logger.setLevel(loglevel)

    """
    Stores measures into the RRD database associated to a given node id
    Values are passed as a dictionary: tag as key, value_as_string as value
    """
    def store_measures(self, timestamp, node_id, values):
        rrd_db = RRD.__config.RRD_BASE_DIR + '/n' + node_id + '.rrd'
        ds_list = ''
        vl_list = str(timestamp)
        for tg in values.keys():                        
            if len(ds_list):
                ds_list = ds_list + ':' + tg
            else:
                ds_list = tg                        
            vl_list = vl_list + ':' + values[tg]
                
        RRD.__logger.debug('For node' + node_id +' RRD datasource list is ' + ds_list)
        RRD.__logger.debug('For node' + node_id +' RRD value list is ' + vl_list)

        RRD.__RRDlock.acquire()
        rrdtool.update( rrd_db,
                        '--template', ds_list,
                        vl_list )
        RRD.__RRDlock.release()
        RRD.__logger.info('Stored measures in RRD db ' + rrd_db + ' at timestamp '+ str(timestamp) )

    """
    Returns the lastest timestamp for which data has been updated for a given node RRD
    """
    def get_last_tstamp(self, node_id):
        rrd_db = RRD.__config.RRD_BASE_DIR + '/n' + node_id + '.rrd'  
        RRD.__RRDlock.acquire()                                                     
        lt = rrdtool.last(rrd_db)
        RRD.__RRDlock.release()
        return lt

    """
    Fetches measurs from all the datasources associated to a node id
    for a given timestamp

    RRD.fetch retrieves a tuple of three elements, as example
    ((1454840070, 1454840100, 30), ('20', '04', '05'), [(None, None, None)])
    element[0]: the start time and end time (excluded) of the query and the configured granularity
    element[1]: a tupe of the datasources labels
    element[2]: a list of tuples of values, corresponding to the datasource labels, one for each timestamp fetched

    Returns a list of couples (measure_tag, value)
    """
    def fetch_measures(self, node_id, tstamp):
        rrd_db = RRD.__config.RRD_BASE_DIR + '/n' + node_id + '.rrd'
        RRD.__logger.debug('Fetching RRD datasources for node ' + node_id + ' and time stamp ' + str(tstamp))

        RRD.__RRDlock.acquire()
        rrd_result = rrdtool.fetch( rrd_db,
                                    'AVERAGE',
                                    '--start', str(tstamp), '--end', str(tstamp) )
        RRD.__RRDlock.release()
        measures = []
        rrd_values = rrd_result[2][0]
        for idx in range(0, len(rrd_values)):
            if not rrd_values[idx] == None:
                measures.append((rrd_result[1][idx], rrd_values[idx]))

        return measures
        
