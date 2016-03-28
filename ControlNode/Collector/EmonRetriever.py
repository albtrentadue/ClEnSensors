"""
 ClENSensors / Control node
 by Alberto Trentadue Mar 2016
 
 The Retriever Object interfacing EmonCMS
 
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
import urllib, urllib2, httplib
from Retriever import Retriever


"""
This class extends the abstract class Retriever
The EmonRetriever class implements the process running on the Control Node
and forwarding measures from the local RRD database to the target
Management Database running in the EmonCMS system.
"""
class EmonRetriever (Retriever):	

    # The REST Session ID
    __rest_session_id = ''

    # The connection flag
    __rest_connected = False

    #Initializer
    def __init__(self, config, collector, RRD_if):
        super(EmonRetriever, self).__init__(config, collector, RRD_if)

                        
    """
    Connects to the DreamFactory REST server
    If connection fails, the program continues, but will not save measures to
    the service
    """
    def connect(self):
        #TODO: implement a REAL connection method
        super(EmonRetriever, self).connect()
                        

    """
     Pushes the retrieved measures through the HTTP iterface to EmonCMS
    """
    def push_measures(self, timestamp, measures):
        retval = False
        Retriever.logger.debug('Pushing measures for timestamp:' + str(timestamp))
        if Retriever.connected:
            for measure in measures:
                #tc_measure = self.translate(measure) - Not used with EmonCMS
                tc_measure = measure
                if tc_measure != None:
                    #Store to DB via REST API here
                    Retriever.logger.debug('Measure record to be posted:' + str(tc_measure))
                    post_url = "http://" + Retriever.config.REST_SERVER_ADDRESS + "/emoncms/input/post.json?"
                    url_data = "apikey=" + Retriever.config.API_KEY
                    url_data = url_data + "&time=" + str(timestamp)
                    url_data = url_data + "&node=" + str(int(tc_measure['ID_SENSOR']))
                    url_data = url_data + "&json={" + tc_measure['MEAS_TAG'] + ":" + str(tc_measure['VALUE']) + "}"
                    #post_data = urllib.urlencode(url_data)
                    post_url = post_url + url_data
                    
                    Retriever.logger.debug('POST URL:'+post_url)
                    #Retriever.logger.debug('DICT DATA:'+str(dict_data))
                    request = urllib2.Request(post_url)
                    #Retriever.logger.debug('POST DATA:'+str(post_data))

                    reply = ""
                    try:
                        response = urllib2.urlopen(request, timeout=20)
                    except urllib2.HTTPError as e:
                        Retriever.logger.error("Couldn't send to server, HTTPError: " + str(e.code))
                    except urllib2.URLError as e:
                        Retriever.logger.error("Couldn't send to server, URLError: " + str(e.reason))
                    except httplib.HTTPException:
                        Retriever.logger.error("Couldn't send to server, HTTPException")
                    except Exception:
                        import traceback
                        Retriever.logger.error("Couldn't send to server, Exception: " + traceback.format_exc())
                    else:
                        reply = response.read()

                    if reply != 'ok':
                        Retriever.logger.error("Failed sending:" + str(tc_measure) + ". Response was:" + reply)
                    else:
                        Retriever.logger.debug("Sent to Emon:" + str(tc_measure))
                        retval = True
                    
                else:
                    Retriever.logger.warning('Unknown tag '+measure['MEAS_TAG']+' in translation for node '+measure['ID_SENSOR'])
        else:
            Retriever.logger.info('Measures not posted because connection to REST server is not available.')
                        
        return retval
               
### EmonRetriever class definition ends here

