/**
 ClEnSensors / Sensor node
 by Alberto Trentadue Dec.2015
 
 Sensor node control for the ClEnSensors PoC system.
 
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
#include <DHT.h>
 
#define LED_BUILTIN 13
#define EXT_LED 11
#define ADDRESS_MYID 1
#define PIN_DHT1 4

//serve() response codes
#define RESP_OK 0
#define NOT_MINE 1
#define UNHANDLED 2

const char MSG_TERM = '#';

const String BROADCAST = "000";

const int VALIM_ANALOG = A4;
const String VALIM_MIS = "20";

const int MAX_RXMSG_LEN=15;
const int MAX_TXMSG_LEN=30; //For the PoC 30 is enough
const int MAIN_CYCLE_DELAY=250;
const int CICLI_HEART=2;

int node_ID;
String myID;

char msg_buffer[MAX_RXMSG_LEN];
String response;

byte heart = 0;
byte ext_led_on = 0;
byte cnt_heart = CICLI_HEART;

String msg_sender = "";
String msg_dest = "";
String msg_type = ""; 
String msg_data = "";

DHT dht1;

/* NODE SETUP */
void setup()
{ 
  //The ID of this card must be PRE-programmed.
  node_ID = EEPROM.read(ADDRESS_MYID);
  myID = format_byte(node_ID, 3);
  
  Serial.begin(9600); //XBee module is like a serial
  
  pinMode(LED_BUILTIN, OUTPUT); //Heartbeat led pin 13
  pinMode(EXT_LED, OUTPUT);  //Auxiliary led pin 11
  
  dht1.setup(PIN_DHT1, DHT::DHT22);
  
}

/* MAIN LOOP */
void loop()
{
  int nr = receive_msg();
  //If something has been retrieved from serial
  if (nr) { 
    if (msg_buffer[0] == '?') send_error(1); //error 1: Incorrect string received
    else {
      int rv=serve();
      switch (rv) {
        case NOT_MINE: //Not for this node: forget it
          break;
        case UNHANDLED:
          if (msg_dest == myID) send_error(2); //error 2: Unhandled command
          break;
        case RESP_OK:
          send_message(); 
          break;
      }
    }
  }
  
  heartbeat();
  delay(MAIN_CYCLE_DELAY);
}

/**
 Formats a byte into a fixed length string padded with zeros
 */
String format_byte(byte b, byte len)
{
  String r = String(b);
  while (r.length() < len) r = '0' + r;
  return r;
}


/**
 Retrieves a message string from the bus.
 Returns the received string into message buffer, 
 or "?" in case of any problem.
 */
int receive_msg() 
{ 
  int num_read = 0;
  //Init the message buffer to empty
  msg_buffer[0] = MSG_TERM;
  
  // see if there's incoming serial data:
  if (Serial.available() > 0) {
    //Search the message starter
    char incomingByte = Serial.read();
    //Skip any pre-existing byte from the serial which is not a 127
    if (incomingByte == MSG_TERM) {
      //Build up the message string
      num_read = Serial.readBytesUntil(MSG_TERM, msg_buffer, MAX_RXMSG_LEN);
      //If MAX_RXMSG_LEN bytes were read, means that # was not received! 
      if (num_read == MAX_RXMSG_LEN) msg_buffer[0] = '?';
      else
        //readd the terminator stripped by readBytesUntil()
        msg_buffer[num_read] = MSG_TERM;
    }
  }
  
  return num_read;
}

/**
 Serve the command requested by the incoming message 
 and load response with the reply
 Returns 0 if OK, or non zero if any error
 */
int serve() 
{
  //Message is parsed
  parse_message();
  if ((msg_dest != BROADCAST) && (msg_dest != myID)) return NOT_MINE;
  //Serial.print("MSGTYPE:"+msg_type);
  //Handles the IDNREQ Command
  if (msg_type.equals("IDNREQ")) {
    //Waits a time in seconds equal to myID - to avoid collision
    delay(1000L * node_ID);
    make_response(msg_sender, "IDRESP", "");
    return RESP_OK;
  }
  
  if (msg_type.equals("QRYMSR")) {
    //Read values from the available sensors
    make_response(msg_sender, "QRYRES", collect_measures());
    return RESP_OK;
  }
  
  //Or signal an Unhandled command
  return UNHANDLED;
  
}

/**
 Parses the command message stored in the message buffer.
 The command messages from the controller have the following format:
 "<MITT><DEST><TIPO_MESSAGGIO>#"
 Parsed values are stored into global strings:
 msg_type, msg_sender, msg_dest, msg_data until the next command arrives.
 */
void parse_message() 
{
  String buf = String(msg_buffer);
  msg_sender = buf.substring(0, 3);
  msg_dest = buf.substring(3, 6);
  msg_type = buf.substring(6,12);
    
  /*
  not required in the PoC version
  
  msg_data = buf.substring(12);
  */    
}

/**
 Builds the string 'response' with the response to the handled command;
*/
void make_response (String dest, String resp_type, String resp_data) 
{  
  response = myID+dest+resp_type+resp_data;
}

/**
 Load the measures as they are configured in the board.
 
 In the PoC version, only temperature and humidity are read from one or two DHT22 sensors
 and returned as digital sources #4, #5 (and #6, #7 if two sensors are used).
 */
String collect_measures() 
{
  String measures = "";
  
  //Read the temp value from DHT22 sensor - the read can take some time.
  float t1 = dht1.getTemperature();
  if (String(dht1.getStatusString()) == "OK") 
    measures = measures + "04" + String(int(t1)); //meas tag #4
  //Serial.print("DHT_STATUS_T:"+String(dht1.getStatusString()));

  //Read the humidity value from DHT22 sensor - the read can take some time.  
  float h1 = dht1.getHumidity();
  if (String(dht1.getStatusString()) == "OK") {
    if (measures.length() > 0) measures += ":";
    measures = measures + "05" + String(int(h1)); //meas tag #5
  }
  //Serial.print("DHT_STATUS_H:"+String(dht1.getStatusString()));
  
  //Always send the Voltage value measured by analog pin.
  int valim_value = analogRead(VALIM_ANALOG);
  if (measures.length() > 0) measures += ":";
  measures = measures + VALIM_MIS + String(valim_value);

  return measures; 
}

/**
 Sends an ERROR indication
 */
void send_error(byte err_code) 
{
  make_response(msg_sender, "SERROR", String(err_code));
  send_message();
}

/**
 Send a string message on the RF interface
 */
void send_message() 
{
  ext_led_on = 1;
  Serial.print(String(MSG_TERM) + response + String(MSG_TERM));
}


/**
 Heartbeat on the built_in Led + EXT_LED
 */
void heartbeat() 
{
  cnt_heart--;
  if (cnt_heart == 0) {
      heart++;
      digitalWrite(LED_BUILTIN, bitRead(heart,0));
      digitalWrite(EXT_LED, bitRead(ext_led_on,0));
      if (ext_led_on) ext_led_on = 0;
      
      cnt_heart = CICLI_HEART;
   }
}
