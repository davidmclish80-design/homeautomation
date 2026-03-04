

#include <SoftwareSerial.h>
// IMPORT ALL REQUIRED LIBRARIES

#include <math.h>
#include <NewPing.h>

   
//**********ENTER IP ADDRESS OF SERVER******************//

#define HOST_IP     "172.16.192.66"       // REPLACE WITH IP ADDRESS OF SERVER ( IP ADDRESS OF COMPUTER THE BACKEND IS RUNNING ON) 
#define HOST_PORT   "8080"               // REPLACE WITH SERVER PORT (BACKEND FLASK API PORT)
#define route       "api/update"         // LEAVE UNCHANGED 
#define idNumber    "620171852"          // REPLACE WITH YOUR ID NUMBER 

// WIFI CREDENTIALS
//const char* SSID = "ARRIS-F53D";           // Add your Wi-Fi ssid 
//const char* password = "70DFF79FF53D";     // Add your Wi-Fi password
//const char* ssid         = "gadfa’s iPhone"; // Add your Wi-Fi ssid
//const char* password     = "12345678"; // Add your Wi-Fi password 
const char* SSID       = "MonaConnect";     // Add your Wi-Fi ssid
const char* password   = ""; // Add your Wi-Fi password 
#define stay        100
 
//**********PIN DEFINITIONS******************//

#define espRX         10
#define espTX         11
#define espTimeout_ms 300

//arduino to sonic boom detector
#define TRIGGER_PIN 6
#define ECHO_PIN 7
#define MAX_DISTANCE 200
//max distance unit? ==>8cm?

//**********CUP DIMENSIONS******************//
#define CUP_HEIGHT_CM   8.0
#define CUP_DIAMETER_CM 7.0
#define CUP_RADIUS_CM   3.5
 
/* Declare your functions below */
float clampFloat(float value, float minVal, float maxVal);
float getWaterHeight(unsigned int distance);
float getReserve(float waterheight);
int getPercentage(float waterheight);

NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE); 

SoftwareSerial esp(espRX, espTX); 

//SoftwareSerial espSerial(RX, TX); EXPLANATION IN LINE BELOW: 
//THIS IS A FUNCTION THAT ALLOWS DATA PINS TO MIMIC SERIAL TRANSMISION PINS, IT TAKES TWO PINS IN THE ORDER SEEN HERE 

void setup(){

  Serial.begin(115200); 
  // Configure GPIO pins here

  espInit();  
 
}

void loop(){ 
   unsigned int distance = sonar.ping_cm();

   float waterheight = getWaterHeight(distance);
   float reserve = getReserve(waterheight);
   int percentage = getPercentage(waterheight);

   Serial.print(distance);
   Serial.print(" cm");
   Serial.print(" | waterheight = ");
   Serial.print(waterheight);
   Serial.print(" cm | reserve = ");
   Serial.print(reserve);
   Serial.print(" cm^3(ml) | percentage = ");
   Serial.print(percentage);
   Serial.println("%");
   
   char payload[220] = {0};
   char waterStr[20] = {0};
   char reserveStr[20] = {0};

   // AVR-safe float conversion
   dtostrf(waterheight, 0, 2, waterStr);
   dtostrf(reserve, 0, 2, reserveStr);

   snprintf(
      payload,
      sizeof(payload),
      "{\"id\":\"%s\",\"type\":\"ultrasonic\",\"radar\":%u,\"waterheight\":%s,\"reserve\":%s,\"percentage\":%d}",
      idNumber,
      distance,
      waterStr,
      reserveStr,
      percentage
   );

   Serial.println(payload);

   espUpdate(payload);

   delay(1000);  
}

 
void espSend(char command[] ){   
    esp.print(command); // send the read character to the esp    
    while(esp.available()){ Serial.println(esp.readString());}    
}


void espUpdate(char mssg[]){ 
    char espCommandString[50] = {0};
    char post[290]            = {0};

    snprintf(espCommandString, sizeof(espCommandString),"AT+CIPSTART=\"TCP\",\"%s\",%s\r\n",HOST_IP,HOST_PORT); 
    espSend(espCommandString);    //starts the connection to the server
    delay(stay);

    // GET REQUEST 
    // snprintf(post,sizeof(post),"GET /%s HTTP/1.1\r\nHost: %s\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: %d\r\n\r\n%s\r\n\r\n",route,HOST_IP,strlen(mssg),mssg);

    // POST REQUEST
    snprintf(post,sizeof(post),"POST /%s HTTP/1.1\r\nHost: %s\r\nContent-Type: application/json\r\nContent-Length: %d\r\n\r\n%s\r\n\r\n",route,HOST_IP,strlen(mssg),mssg);
  
    snprintf(espCommandString, sizeof(espCommandString),"AT+CIPSEND=%d\r\n", strlen(post));
    espSend(espCommandString);    //sends post length
    delay(stay);
    Serial.println(post);
    espSend(post);                //sends POST request with the parameters 
    delay(stay);
    espSend("AT+CIPCLOSE\r\n");   //closes server connection
   }

void espInit(){
    char connection[100] = {0};
    esp.begin(115200); 
    Serial.println("Initiallizing");
    esp.println("AT"); 
    delay(1000);
    esp.println("AT+CWMODE=1");
    delay(1000);
    while(esp.available()){ Serial.println(esp.readString());} 

    snprintf(connection, sizeof(connection),"AT+CWJAP=\"%s\",\"%s\"\r\n",SSID,password);
    esp.print(connection);

    delay(3000);  //gives ESP some time to get IP

    if(esp.available()){   Serial.print(esp.readString());}
    
    Serial.println("\nFinish Initializing");    
   
}

//***** Design and implement all util functions below ******

float clampFloat(float value, float minVal, float maxVal){
  if(value < minVal) return minVal;
  if(value > maxVal) return maxVal;
  return value;
}

float getWaterHeight(unsigned int distance){
  float h = CUP_HEIGHT_CM - distance;
  return clampFloat(h, 0.0, CUP_HEIGHT_CM);
}

float getReserve(float waterheight){
  return 3.14159 * CUP_RADIUS_CM * CUP_RADIUS_CM * waterheight;
}

int getPercentage(float waterheight){
  float p = (waterheight / CUP_HEIGHT_CM) * 100.0;
  if(p < 0) p = 0;
  if(p > 100) p = 100;
  return (int)p;
}