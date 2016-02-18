#!/usr/bin/python

"""
 ClENSensors / Control node
 by Alberto Trentadue Dec.2015
 
 The rrdcreate utility creates the right rrd database in the intended directory
 based on the transfer calibration configuration holding the expected nodes
 and sensor tags.
 This utility is to be used ONLY ONCE at first system configuration
 
 Copyright Alberto Trentadue 2015, 2016
 
 This file is part of ClEnSensors.

 ClEnSensors is free software: you can redistribute it and/or modify
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

# The library python-rrdtoll must be available and installed
import sys, os, rrdtool
from Collector_config import Collector_config

#ATTENTION: the application user MUST have WRITE permission on this directory
BASE_DIR = '/var/opt/clensensors'
the_config = Collector_config(sys.argv[0])

nodetags = {}

#The home dir detection
home_dir = os.path.split(os.path.dirname(os.path.realpath(sys.argv[0])))[0]

f = open(home_dir + '/cfg/clen_transcalibration.cfg')
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
                node_id = token_list[0]
                sens_tag = token_list[2]

                if node_id in nodetags.keys():
                        if sens_tag in nodetags[node_id]:
                                print 'Duplicate sensor tag ' + sens_tag + ' for node ' + node_id
                                print 'Check and fix the transcalibration config file. Exiting.'
                                sys.exit(1)
                        else:
                                tag_list = nodetags[node_id].append(sens_tag)
                else:
                        nodetags[node_id] = [sens_tag]

# Here all nodes and sensor tags have been collected in the datasource dictionary
for nd in nodetags.keys():
        db_name = 'n' + nd + '.rrd'
        datasources = []
        for tg in nodetags[nd]:
                datasources.append('DS:' + tg + ':GAUGE:' + str(2*the_config.TIME_INTERVAL) + ':U:U')

        #print datasources
        rrdtool.create( the_config.RRD_BASE_DIR + '/' + db_name,
                        '--step', str(the_config.TIME_INTERVAL), '--no-overwrite',
                        datasources,
                        'RRA:AVERAGE:0:1:' + str(the_config.RRD_LENGTH))

        print 'RRD Database created:' + BASE_DIR + '/' + db_name
