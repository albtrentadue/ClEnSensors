#!/usr/bin/python

"""
 ClENSensors / Control node
 by Alberto Trentadue Dec.2015
 
 The Collector Module implements the Collector and the Retriever objects
 to collect measures from sensors, store them in the local RRD database and
 forward them to the destination storage on the remote server
 
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

#"serial" is imported from the external module pySerial / https://pythonhosted.org/pyserial/
import sys, signal, threading, time

from Collector_config import Collector_config
from Collector import Collector
from RRD import RRD
from Retriever import Retriever

# Constant values
MSG_TERMINATOR = '#'
CONTROL_ID = '001'
BROADCAST_ID = '000'

keep_on = True

"""
The SIGTERM & SIGINT signal handler to quit the process 
"""
def signal_handler(_signo, _stack_frame):
	global keep_on
	# Shutdown the processes
	#print "Caught signal for shutdown: " + str(_signo)
	keep_on = False
	
#setup the SIGTERM & SIGINT hook handler
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

"""
Execution start
"""

if len(sys.argv) != 2:
        print 'Wrong command line arguments. Exiting.'
        sys.exit(1)

# Takes command line argument: the serial port name
the_config = Collector_config(sys.argv[0])
rrd_if = RRD(the_config)
collector = Collector(the_config, sys.argv[1], rrd_if)
collector.start()
time.sleep(1)
retriever = Retriever(the_config, rrd_if)
retriever.start()

while keep_on:
        time.sleep(2)

retriever.shutdown()
collector.shutdown()
print 'Waiting Retriever to exit...'
retriever.join()
print 'Waiting Collector to exit...'
collector.join()

# Exits cleanly
print 'Exiting cleanly, Bye!'

