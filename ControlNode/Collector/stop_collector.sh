#!/bin/bash

# ClEnSensors / Control node / Collector stop script
# by Alberto Trentadue Apr.2016

# Copyright Alberto Trentadue 2015, 2016

# This file is part of ClENSensors.

# ClEnSensors is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ClEnSensors is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with ClEnSensors.  If not, see <http://www.gnu.org/licenses/>.

echo "Stopping the Collector..."

CURRDIR=`pwd`

cd /opt/clensensors/bin

if [ ! -f collector.pid ]; then
    echo "PID file not found. Doing nothing."
    exit 1
fi

PID=`cat collector.pid`
kill -2 $PID

while ps -p $PID > /dev/null
do
    sleep 1
done

cd $CURRDIR
