#!/bin/bash

# ClEnSensors / Control node / Collector package maker
# by Alberto Trentadue May.2016

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

VERSION_STRING="V1dev_bld1"
PACKAGE_BASE_NAME="ClEn_Collector"

# Take the start location as the Collector root source dir
SOURCE_DIR=`pwd`

#Check build dir location
if [ -z $CLEN_COLL_BUILDDIR ]; then
  CLEN_COLL_BUILDDIR="../../../BUILD/COLLECTOR"
fi
mkdir -p $CLEN_COLL_BUILDDIR
if [ $? -ne 0 ]; then
  echo "Failed creating build dir. Exiting."
  exit 1
fi

cd $CLEN_COLL_BUILDDIR
BASE_DIR="clensensors"
mkdir -p $BASE_DIR
# Cleanup the existing, if any
cd $BASE_DIR
rm -rf bin
rm -rf cfg
rm -f GPLv3.txt LICENSE README.md INSTALL.md

# Make the dirs
mkdir bin
mkdir cfg

# Copy the executables
cd bin
cp $SOURCE_DIR/*.py .
cp $SOURCE_DIR/start_collector.sh .
cp $SOURCE_DIR/stop_collector.sh .

# Copy the configuration files
cd ../cfg
cp $SOURCE_DIR/*.cfg .

# Copy the base doc
cd ..
cp $SOURCE_DIR/../../GPLv3.txt .
cp $SOURCE_DIR/../../COPYRIGHT .
cp $SOURCE_DIR/../../3RDPARTY .
cp $SOURCE_DIR/../../README.md .
cp $SOURCE_DIR/../../INSTALL.md .

# Make the compressed package
cd ..
PACKAGE_NAME=$PACKAGE_BASE_NAME"-"$VERSION_STRING
tar czf $PACKAGE_NAME".tgz" $BASE_DIR

cd $SOURCE_DIR
echo "Collector package $PACKAGE_NAME created."

