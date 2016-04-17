#!/bin/bash

# ClEnSensors / Control node / Collector start script
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

# Argument check
if [ $# -ne 1 ]; then
    echo "Missing serial USB argument. Exiting."
    exit 1
fi

echo "Starting the Collector in background..."

CURRDIR=`pwd`

cd /opt/clensensors/bin
./clen_collector.py $1 &
PID=$!

echo $PID > collector.pid
echo "Collector started"

cd $CURRDIR
