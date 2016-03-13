/**
 ClEnSensors / Sensor node
 by Alberto Trentadue Dec.2015
 
 Sensor node control for the ClEnSensors PoC2 system.
 
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
#include <SoftwareSerial.h>
 
#define LED_BUILTIN 13
#define EXT_LED 11
#define PART_ENABLE 12
#define XBEE_SLEEP 8
#define PIN_DHT1 4
#define PIN_DHT2 5
#define SWSERIAL_RX 10 //swapped after circuit change
#define SWSERIAL_TX 9 //swapped after circuit change
#define VALIM_ANALOG A4
#define PIN_ANALOG1 A0
#define PIN_ANALOG2 A1


//EEPROM USED ADDRESSES
#define ADDRESS_MYID 1
#define ADDRESS_CICLI_SLEEP 2

//serve() response codes
#define RESP_OK 0
#define NOT_MINE 1
#define UNHANDLED 2

//other fixed values
#define MAX_RXMSG_LEN 25 //>14+10:To be rechecked EACH protocol change!!
#define MAX_TXMSG_LEN 56 //>14+42 = std msg + 7 * 6 bytes (measures)
#define MAIN_CYCLE_DELAY 250
#define CICLI_HEART 2

const char MSG_TERM = '#';
const char DATA_SEP = ':';
const String BROADCAST = "000";
const String VALIM_MIS = "20";

//Configuration item id's (protocol)
const String TIME_GRAN = "TG";

int node_ID;
String myID;

char msg_buffer[MAX_RXMSG_LEN];
String response;

byte heart = 0;
byte ext_led_on = 0;
byte cnt_heart = CICLI_HEART;
//The amount of MAIN_CYCLE_DELAY times the XBee will be in sleep.
//equal to = (TimeGranularity*60*1000-3000)/MAIN_CYCLE_DELAY
//default is considering TG=1 -> 228
unsigned int cicli_sleep=228;
unsigned int cnt_sleep=0;
boolean xbee_sleeping = false;

SoftwareSerial XBee(SWSERIAL_RX, SWSERIAL_TX);

String msg_sender = "";
String msg_dest = "";
String msg_type = ""; 
String msg_data = "";

DHT dht1;
DHT dht2;

/* NODE SETUP */
void setup()
{ 
  //NOTE! The ID of this card must be PRE-programmed by writing 
  //in the ADDRESS_MYID EEPROM location
  node_ID = EEPROM.read(ADDRESS_MYID);
  myID = format_byte(node_ID, 3);
  //NOTE! The default value of cicli_sleep (228,0) must be PRE-programmed by
  //writing in the ADDRESS_CICLI_SLEEP EEPROM location
  byte bl = EEPROM.read(ADDRESS_CICLI_SLEEP);
  byte bh = EEPROM.read(ADDRESS_CICLI_SLEEP+1);//2 bytes are read!
  cicli_sleep = bl + 0xFF * bh;
  
  
  //Serial.begin(9600); //For test when no XBee
  XBee.begin(9600);
  
  pinMode(LED_BUILTIN, OUTPUT); //Heartbeat led pin 13
  pinMode(EXT_LED, OUTPUT);  //Auxiliary led pin 11
  pinMode(PART_ENABLE, OUTPUT);  //Partitor enabler pin 12
  
  dht1.setup(PIN_DHT1, DHT::DHT22);
  dht2.setup(PIN_DHT2, DHT::DHT22);
  //Starting mode: the battery sampler is enabled and XBee awake
  set_xbee_sleep(false);
  delay(50);
  
}

/* MAIN LOOP */
void loop()
{
  int nr = receive_msg();
  //If something has been retrieved from serial
  if (nr) { 
    if (msg_buffer[0] == '?') send_error(1); //error 1: Incorrect string received
    else {
      switch (serve()) {
        case NOT_MINE: //Not for this node: forget it
          break;
        case UNHANDLED:
          if (msg_dest == myID) send_error(2); //error 2: Unhandled command
          break;
        case RESP_OK:
          send_message();
          after_message();
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
  
  if (!xbee_sleeping) {
    // see if there's incoming serial data:
    if (XBee.available() > 0) {
      //Search the message starter
      char incomingByte = XBee.read();
      //Skip any pre-existing byte from the serial which is not a 127
      if (incomingByte == MSG_TERM) {
        //Build up the message string
        num_read = XBee.readBytesUntil(MSG_TERM, msg_buffer, MAX_RXMSG_LEN);
        //If MAX_RXMSG_LEN bytes were read, means that # was not received! 
        if (num_read == MAX_RXMSG_LEN) msg_buffer[0] = '?';
        else
          //readd the terminator stripped by readBytesUntil()
          msg_buffer[num_read] = MSG_TERM;
      }
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
  
  if (msg_type.equals("CONFIG")) {
    //Interprets and applies the configuration setting
    apply_config(msg_data);
    make_response(msg_sender, "CFGACK", "");
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
 Note: the initial '#' in the message has been stripped...
 Parsed values are stored into global strings:
 msg_type, msg_sender, msg_dest, msg_data until the next command arrives.
 */
void parse_message() 
{
  String buf = String(msg_buffer);
  msg_sender = buf.substring(0, 3);
  msg_dest = buf.substring(3, 6);
  msg_type = buf.substring(6,12);
  msg_data = buf.substring(12);    
}

/**
 Builds the string 'response' with the response to the handled command;
*/
void make_response (String dest, String resp_type, String resp_data) 
{  
  response = myID+dest+resp_type+resp_data;
}

/**
 Parses the configuration string and applies the setting passed
 */
void apply_config(String cfg)
{
  int idx=0;
  while (idx < cfg.length()-1) {
    if (cfg.charAt(idx) == MSG_TERM) break;
    if (cfg.charAt(idx) == DATA_SEP) idx++;
    idx += apply_setting(cfg.substring(idx));
  }
}

/**
 Scans a string, extract the first configuration setting and applies it
 Returns the amount of characters scanned in the given string.
 Each setting always starts with a 2-char setting ID and then a value up to
 the separator ':' or terminator '#'
 */
int apply_setting(String s) {
  if (s.length() > 2) {
    String cfg_setting = s.substring(0,2);
    int cnt=2;
    while (s.charAt(cnt) != DATA_SEP && s.charAt(cnt) != MSG_TERM && cnt < s.length()-1) cnt++;
    String cfg_value = s.substring(2,cnt);
    
    //Start the config cases
    if (cfg_setting.equals("TG")) {
      //****Time Granularity setting:
      //Dimension the sleep duration
      int granularity = cfg_value.toInt();
      if (granularity) {
        //Sleep time = granularity minus 3sec
        long gm = granularity*60000L-3000L;
        unsigned int new_cicli_sleep = gm/MAIN_CYCLE_DELAY;
        if (new_cicli_sleep != cicli_sleep) {
          cicli_sleep = new_cicli_sleep;
          //Stores the last configuration in EEPROM
          byte b = byte(cicli_sleep % 0xFF);          
          EEPROM.write(ADDRESS_CICLI_SLEEP, b);
          b = byte(cicli_sleep / 0xFF);
          EEPROM.write(ADDRESS_CICLI_SLEEP+1, b);
        }
      }
    }
    return cnt;
  }
  //If the string is incomplete, just skip it
  else return s.length();
  
}
/**
 Load the measures as they are configured in the board.
 
 In the PoC version, only temperature and humidity are read from one or two DHT22 sensors
 and returned as digital sources #4, #5 (and #6, #7 if two sensors are used).
 */
String collect_measures() 
{
  String measures = "";
  float ms;
  
  //Read the temp value from DHT22 sensor - the read can take some time.
  ms = dht1.getTemperature();
  if (String(dht1.getStatusString()) == "OK") 
    measures = measures + "04" + String(int(ms)); //meas tag #4
  //Serial.print("DHT_STATUS_T:"+String(dht1.getStatusString()));

  //Read the humidity value from DHT22 sensor - the read can take some time.  
  ms = dht1.getHumidity();
  if (String(dht1.getStatusString()) == "OK") {
    if (measures.length() > 0) measures += ":";
    measures = measures + "05" + String(int(ms)); //meas tag #5
  }
  //Serial.print("DHT_STATUS_H:"+String(dht1.getStatusString()));
  
  ms = dht2.getTemperature();
  if (String(dht2.getStatusString()) == "OK") {
    if (measures.length() > 0) measures += ":";
    measures = measures + "06" + String(int(ms)); //meas tag #6
  }    
  //Serial.print("DHT_STATUS_T:"+String(dht2.getStatusString()));

  //Read the humidity value from DHT22 sensor - the read can take some time.  
  ms = dht2.getHumidity();
  if (String(dht2.getStatusString()) == "OK") {
    if (measures.length() > 0) measures += ":";
    measures = measures + "07" + String(int(ms)); //meas tag #7
  }
  //Serial.print("DHT_STATUS_H:"+String(dht2.getStatusString()));  
  
  //Read the analog values
  if (measures.length() > 0) measures += ":";
  measures = measures + "00" + String(analogRead(PIN_ANALOG1)) + ":01" + String(analogRead(PIN_ANALOG2));
  //Battery voltage value measured by analog pin.
  measures = measures + ":" + VALIM_MIS + String(analogRead(VALIM_ANALOG));

  return measures; 
}

/**
 Control the sleep status of Xbee
 When the XBee is in sleep mode, also the battery sampling partitor
 shall be disabled
 */
void set_xbee_sleep(boolean to_sleep) {
  xbee_sleeping = to_sleep;
  if (to_sleep) {
    pinMode(XBEE_SLEEP, INPUT);
    digitalWrite(XBEE_SLEEP,0);
    digitalWrite(PART_ENABLE,0);
    cnt_sleep=cicli_sleep;
  }
  else {
    pinMode(XBEE_SLEEP, OUTPUT);
    digitalWrite(XBEE_SLEEP,0);
    digitalWrite(PART_ENABLE,1);
  }
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
  //Serial.print(String(MSG_TERM) + response + String(MSG_TERM));
  XBee.print(String(MSG_TERM) + response + String(MSG_TERM));
}

/**
 Here any action that has to be done after sending the response
 can be specified
 */
void after_message() {
  //manages the XBee sleep after sending the measures
  if (msg_type.equals("QRYMSR")) {
    //Waits an amount of time to allow the serial transmission
    delay(3*MAX_TXMSG_LEN);
    //Then sets the Xbee to sleep
    set_xbee_sleep(true);
  }
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
   
   //Sleep cycles management
   if (xbee_sleeping) {
     cnt_sleep--;
     if (cnt_sleep == 0) set_xbee_sleep(false);       
   }
}
