"""
 ClENSensors / Control node
 by Alberto Trentadue Mar 2016
 
 The Retriever Object interfacing DreamFactory
 
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
from Retriever import Retriever
from Collector import Collector


"""
This class extends the abstract class Retriever
The DreamFactoryRetriever class implements the process running on the Control Node
and forwarding measures from the local RRD database to the target
Management Database running in the Bitnami DreamFactory system.

WARNING: This class has not been tested within the PoC2 development
"""
class DreamFactoryRetriever (Retriever):	

    # The REST Session ID
    __rest_session_id = ''

    #Initializer
    def __init__(self, collector, config, RRD_if):
        super(DreamFactoryRetriever, self).__init__(config, collector, RRD_if)

                        
    """
    Connects to the DreamFactory REST server
    If connection fails, the program continues, but will not save measures to
    the service
    """
    def connect(self):
        resp = ''
        # Creazione del session_id
        try:
            #resp = unirest.post("http://"+REST_SERVER_ADDRESS+"/api/v2/user/session", headers = {"X-DreamFactory-Application-Name": DF_APP}, params=json.dumps({ "email":REST_APP_USER, "password":REST_APP_PWD, "remember_me": False }))
            resp = unirest.post("http://"+Retriever.config.REST_SERVER_ADDRESS+"/api/v2/user/session", headers = {}, params=json.dumps({ "email":Retriever.config.REST_APP_USER, "password":Retriever.config.REST_APP_PWD, "remember_me": False }))
            self.__rest_session_id=json.loads(resp.raw_body)["session_id"]
            Retriever.logger.info('Successfully authenticated with DreamFactory. Session ID:' + self.__rest_session_id)
            Retriever.connected = True
        except:
            Retriever.logger.warning('Failed to connect to REST Server. Measures will not be forwarded and stored in local RRD')                            

    """
     Pushes the retrieved measures through the HTTP iterface
     exposed by the REST API provider (DreamFactory)
    """
    def push_measures(self, timestamp, measures):
        retval = False
        if Retriever.connected :
            for measure in measures :
                tc_measure = self._translate(measure)
                if tc_measure != None:
                    #Store to DB via REST API here
                    Retriever.logger.debug('Measure record to be posted:' + str(tc_measure))
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
                    #resp = unirest.post("http://" + Retriever.config.REST_SERVER_ADDRESS +"/api/v2/thcsensors/_table/thc_misure?api_key="+Retriever.config.API_KEY+"&session_token="+rest_session_id, headers = {"X-DreamFactory-Application-Name": DF_APP, "X-DreamFactory-Session-Token": rest_session_id}, params=json.dumps(rest_sensors_api))
                    try:
                        resp = unirest.post("http://" + Retriever.config.REST_SERVER_ADDRESS +"/api/v2/thcsensors/_table/thc_misure?api_key="+Retriever.config.API_KEY+"&session_token="+rest_session_id, headers = {}, params=json.dumps(rest_sensors_api))
                        Retriever.logger.debug('REST Record posted to DB:' + str(rec))
                        retval = True
                    except:
                        Retriever.logger.error('REST Record post failed. Response was ' + resp)
                else:
                    Retriever.logger.warning('Unknown tag '+measure['MEAS_TAG']+' in translation for node '+measure['ID_SENSOR'])
        else:
            Retriever.logger.info('Measures not posted because connection to REST server is not available.')
                        
        return retval

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
                
### DreamFactoryRetriever class definition ends here

