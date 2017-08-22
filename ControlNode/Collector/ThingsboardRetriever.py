"""
 ClENSensors / Control node
 by Alberto Trentadue Mar 2016, 2017

 The Retriever Object interfacing Thingsboard

 Copyright Alberto Trentadue 2015, 2016, 2017

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
import json, urllib2, ssl

from Retriever import Retriever
from Collector import Collector


"""
This class extends the abstract class Retriever
The ThingsboardRetriever class implements the process running on the Control Node
and forwarding measures from the local RRD database to the target
Management Database running in the Thingsboard IOT platform.
"""

class ThingsboardRetriever (Retriever):	

    #Initializer
    def __init__(self, config, collector, RRD_if):
        super(ThingsboardRetriever, self).__init__(config, collector, RRD_if)

        # Needed to handle unverified self-signed cerificates
        self.ssl_ctx = ssl.create_default_context()
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE

    """
     Connects to the JSON server
     If connection fails, the program continues, but will not save measures to
     the service
    """
    def connect(self):
        #TODO: implement a REAL connection method
        super(ThingsboardRetriever, self).connect()


    """
     Pushes the retrieved measures through the HTTP iterface
     exposed by the JSON/HTTP API provider (Thingsboard)
    """
    def push_measures(self, timestamp, measures):
        retval = False
        if Retriever.connected :
            for measure in measures :
                tc_measure = self.translate(measure)
                if tc_measure != None:
                    #Store to DB via REST API here
                    Retriever.logger.debug('Measure record to be posted:' + str(tc_measure))
                    #Prepare the record
                    rec={}
                    #Thingsboard expects epoch timestamps in milliseconds
                    rec['ts'] = timestamp*1000
                    meas_key = tc_measure['ID_SENSOR']+':'+tc_measure['POSITION']+':'+tc_measure['MEASURED_ITEM']
                    #recvalues["unita"] = tc_measure['UNIT']
                    recvalues = { meas_key: tc_measure['VALUE']} #float
                    rec['values'] = recvalues

                    # Store data into DB via JSON/HTTP
		    resp = ''
                    try:
                        req = urllib2.Request("https://" + Retriever.config.JSON_SERVER_ADDRESS +"/api/v1/"+Retriever.config.API_KEY+"/telemetry", data=json.dumps(rec), headers = {'Content-Type': 'application/json'})
                        resp = urllib2.urlopen(req, context=self.ssl_ctx)
                        retval = True
                    except:
                        Retriever.logger.error('JSON Record post failed. Response was: ' + resp)
                        Retriever.logger.error('Exception info:' + str(sys.exc_info()[0]))
                else:
                    Retriever.logger.warning('Unknown tag '+measure['MEAS_TAG']+' in translation for node '+measure['ID_SENSOR'])
        else:
            Retriever.logger.info('Measures not posted because connection to JSON/HTTP server is not available.')

        return retval

### DreamFactoryRetriever class definition ends here

