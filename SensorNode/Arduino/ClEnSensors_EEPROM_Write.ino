/**
 ClEnSensors / Sensor node
 by Alberto Trentadue Dec.2015
 
 Sensor node EEPROM writer for the ClEnSensors PoC2 system.
 
 Copyright Alberto Trentadue 2015, 2016
 
 This file is part of ClEnSensors

 ClEnSensors is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 ClEnSensors is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with ClEnSensors.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <EEPROM.h>

//EEPROM USED ADDRESSES
#define ADDRESS_MYID 1
#define ADDRESS_CICLI_SLEEP 2  // 2 bytes data

void setup()
{
  // Node My ID setting : Address #1
  // Modify this when programming Arduino for the 1st time
  // or you want to change the ID of a sensor's Arduino
  byte myID = 3;
  EEPROM.write(ADDRESS_MYID, myID);
  
  // Node Cicli Sleep setting : Address #2 (low) and #3 (high)
  // Modify this when programming Arduino for the 1st time
  // cicli sleep = (60000 - 3000) / MAIN_CYCLE_DELAY
  // please check the ClEnSensors main control sketch
  unsigned int cicli_sleep=228;
  byte cs = byte(cicli_sleep % 0xFF);          
  EEPROM.write(ADDRESS_CICLI_SLEEP, cs);
  cs = byte(cicli_sleep / 0xFF);
  EEPROM.write(ADDRESS_CICLI_SLEEP+1, cs);
  
}

void loop()
{
}
