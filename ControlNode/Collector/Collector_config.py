"""
 ClENSensors / Control node
 by Alberto Trentadue Dec.2015
 
 Collector Configuration Object
 
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

import sys, os.path

from ConfigParser import ConfigParser

CFG_DEFAULTS = {
	'to_file' : 'False',
	'log_file_dest' : '/var/tmp/clen_collector.log',
	'log_level' : 'INFO',
	'time_interval' : '60',
	'max_sensor_nodes' : '30',
	'rest_server_address' : '127.0.0.1:8081',
        'rrd_base_dir' : '/var/opt/clensensors',
        'rrd_length' : '10800'
}

"""
The Collector_Config class holds the configuration settings from the clen_collector.cfg file
 and the transcalibration settings from the clen_transcalibration.cfg file.
 Acts as the centralized point of access for the Collector/Retriever configuration
"""
class Collector_config:

        # The Transcalibration table
	__transcalibrations = {}

        # The list of the statically configured nodes
	__configured_nodes = []

	# The lists of configured tags for each confiured node
	__configured_tags_by_node = {}
	
	"""
	Load parameters from the cfg file
	"""
	def __init__(self, exefpath):
                #The home dir detection
                self.__home_dir = os.path.split(os.path.dirname(os.path.realpath(exefpath)))[0]
		#Load the configuration file
		config = ConfigParser(CFG_DEFAULTS)
		#Assumes file exists in workdir
		config.read(self.__home_dir + '/cfg/clen_collector.cfg')
		#Setup the values
                self.LOG_TO_FILE = config.getboolean('logging','to_file')
		self.LOG_FILE_DEST = config.get('logging','log_file_dest')
		self.LOG_LEVEL = config.get('logging','log_level')
		self.TIME_INTERVAL = config.getint('main','time_interval')
		self.MAX_SENSOR_NODES = config.getint('main','max_sensor_nodes')
		self.SERIAL_BAUDRATE = config.getint('main','serial_baud_rate')
                self.REST_SERVER_ADDRESS = config.get('rest','rest_server_address')
                self.REST_APP_USER = config.get('rest','rest_app_user')
                self.REST_APP_PWD = config.get('rest','rest_app_pwd')
                self.DF_APP = config.get('rest','df_app')
                self.DF_API_KEY = config.get('rest','df_api_key')
                self.RRD_BASE_DIR = config.get('rrd','rrd_base_dir')
                self.RRD_LENGTH = config.getint('rrd','rrd_length')

                self._load_transcalibration()
                self._set_configured_lists()

        """
        Load the transformation/calibration configuration from the clen_transcalibration.cfg file
        The configuration is stored into the transcalibrations dictionary
        The key of the dictionary is the concatenation <sensor_id><measure_tag>
        The value is a tuple of 5 elements: (<position>,<measured item>,<unit>,<offset>,<mult>)
        """
        def _load_transcalibration(self) :
                
                f = open(self.__home_dir + '/cfg/clen_transcalibration.cfg')
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
                                if tc_key in self.__transcalibrations.keys():
                                        print 'Duplicate sensor tag ' + token_list[2] + ' for node ' + token_list[0]
                                        print 'Check and fix the transcalibration config file. Exiting.'
                                        sys.exit(1)
                                else:                                
                                        tc_value = token_list[1],token_list[3],token_list[4],float(token_list[5]),float(token_list[6])
                                        self.__transcalibrations[tc_key] = tc_value

        """
        The transcalibration values getter
        Return the tuple of values associated to the <node><sensor_tag> couple
        None if the key is missing
        """
        def get_transcalibration_values(self, node_id, sens_tag):
                tc_key=node_id+sens_tag
                if tc_key in self.__transcalibrations.keys():
                        return self.__transcalibrations[tc_key]
                else:
                        return None              

        """
        Extracts the following lists from the static configuration in the Transcalibration file:
        1. Configured nodes
        2. Configired tags per node
        """
        def _set_configured_lists(self):
                for tc_key in self.__transcalibrations.keys():
                        node_id = tc_key[:3]
                        if node_id not in self.__configured_nodes:
                                self.__configured_nodes.append(node_id)
                                self.__configured_tags_by_node[node_id] = [tc_key[3:]]
                        else:
                                self.__configured_tags_by_node[node_id].append(tc_key[3:])

        """
        Gets the list of the statically configured nodes
        """
        def get_configured_nodes(self):
                return self.__configured_nodes

        """
        Gets the list of measure tags configured in the transcalibration
        for one give node
        """
        def get_configured_tags_by_node(self, node_id):
                return self.__configured_tags_by_node[node_id]
                
### Collector_config class definition ends here




