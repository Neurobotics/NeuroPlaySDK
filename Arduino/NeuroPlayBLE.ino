/*
Arduino example how to connect to NeuroPlay devices

This example works with M5Stack Atom device (ESP32-Pico processor with BLE/WiFi support).

Based on tutorial of Rui Santos at https://RandomNerdTutorials.com/esp32-ble-server-client/

Boards manager's installations: 
- esp32 by Espressif Systems v1.0.6
- M5Stack by M5Stack official v1.0.8

Libraries:
- ESP32 BLE Arduino by Neil Kolban v1.0.1
- M5Atom by M5Stack v0.1.0

Include these urls in "File"->"Preferences"->"Additional boards manager URLs" (single line, notice the comma):
https://dl.espressif.com/dl/package_esp32_index.json,https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/arduino/package_m5stack_index.json


Author: Dmitry Konyshev d.konyshev@neurobotics.ru
https://neuroplay.ru
*/

#include "BLEDevice.h"
#include "String.h"
#include <cstring>

static std::string bleServerName = "Physiobelt (0037)";

/* UUIDs of the EEG BLE service and characteristics */
static BLEUUID     eegServiceUUID("f0001298-0451-4000-b000-000000000000");                             
static BLEUUID    eegCharDataUUID("f0001299-0451-4000-b000-000000000000");
static BLEUUID eegCharControlUUID("f000129a-0451-4000-b000-000000000000");

//Flags and objects
static boolean doConnect = false;
static boolean connected = false;
static BLEAddress *pServerAddress;
BLEScan* pBLEScan;
 
//Characteristics that we want to read
static BLERemoteCharacteristic* dataCharacteristic;
static BLERemoteCharacteristic* controlCharacteristic;

//Messages for characteristics
const uint8_t notificationOn[] = {0x1, 0x0};
const uint8_t notificationData1000Hz[] = {0x1, 0x8};
const uint8_t notificationOff[] = {0x0, 0x0};

bool newData = false;
int counter = 0;

//Data storage
uint8_t* lastData;
long d1;
uint8_t s1;
uint8_t s2;
uint8_t s3;

//NeuroPlay sends data as a notification call on the dataCharacteristic
static void dataNotifyCallback(BLERemoteCharacteristic* pBLERemoteCharacteristic, uint8_t* pData, size_t length, bool isNotify) {
  lastData = pData;
  counter++;
  lastData += 2;
  for (int i = 2; i<length; i+=3) {
    d1 = 0;
    s3 = *(lastData++);
    s2 = *(lastData++);
    s1 = *(lastData++);
    d1 = (long(s1) << 16) + (long(s2) << 8) + s3;
    Serial.println(String(d1 / 5369));
    break;    
  }
  newData = true;
}

//Connect to the NeuroPlay BLE with provided name
bool connectToNeuroPlay(BLEAddress pAddress) {
  BLEClient* pClient = BLEDevice::createClient();
 
  Serial.println("-> Connecting to NeuroPlay");
  
  // Connect to the remove device
  pClient->connect(pAddress);
  Serial.println("-> Connected to NeuroPlay");
 
  // List all device's services
  // std::map<std::string, BLERemoteService*>* services = pClient->getServices();
  // for(std::map<std::string, BLERemoteService*>::iterator it = services->begin(); it != services->end(); ++it) 
  // {
  //   Serial.print(it->first.c_str());
  //   Serial.print("=");
  //   Serial.println(it->second->toString().c_str());
  // }

  BLERemoteService* pRemoteService = pClient->getService(eegServiceUUID);
  if (pRemoteService == nullptr) {
    Serial.print("! Failed to find EEG service UUID: ");
    Serial.println(eegServiceUUID.toString().c_str());
    return false;
  }

  // Obtain characteristics in the service of the NeuroPlay device
  dataCharacteristic = pRemoteService->getCharacteristic(eegCharDataUUID);
  controlCharacteristic = pRemoteService->getCharacteristic(eegCharControlUUID);

  if (dataCharacteristic == nullptr || controlCharacteristic == nullptr) {
    Serial.print("! Failed to find EEG service characteristics");
    return false;
  }
  Serial.println("-> Found EEG service and it's characteristics");
 
  //Assign callback functions for data notification of the EEG service
  dataCharacteristic->registerForNotify(dataNotifyCallback, true);

  //Stop scanning for other devices
  pBLEScan->stop();
  return true;
}

//Callback function on received device's advertisement 
class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    if (advertisedDevice.haveName()) {
      std::string devName = advertisedDevice.getName();
      
      Serial.print("Found [");
      Serial.print(devName.c_str());
      Serial.println("]");
      if (std::strcmp(bleServerName.c_str(), devName.c_str()) == 0) { //Check if the name matches
        advertisedDevice.getScan()->stop(); //Stop scanning for other devices
        pServerAddress = new BLEAddress(advertisedDevice.getAddress()); //Remember device's address
        doConnect = true; //Set flag that the search is over and it's data grab time
        Serial.println("Device found. Connecting!");
      }
    }
  }
};
 
void setup() {
  Serial.begin(115200);
  Serial.println("Starting Arduino NeuroPlay BLE Client app");

  //Init BLE device and scanner
  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true);
  pBLEScan->start(10);
}



void loop() {
  // "doConnect" states that the NeuroPlay device is discovered and a connection to it's EEG service can be established to grab data 
  if (doConnect == true) {
    if (connectToNeuroPlay(*pServerAddress)) {
      Serial.println("We are now connected to the BLE Server.");
      
      //Activate the Notify property of each data characteristic
      BLERemoteDescriptor* descData = dataCharacteristic->getDescriptor(BLEUUID((uint16_t)0x2902));
      descData->writeValue((uint8_t*)notificationOn, 2, true);

      //Set control to { 0x1, 1000/rate }, where "rate" can either be 125 Hz (8 channels), 250 Hz (4 channels), 500 Hz (2 channels) or 1000 Hz (1 channel)
      //! At this time, the tutorial is using single channel at 1000 Hz
      controlCharacteristic->writeValue((uint8_t*)notificationData1000Hz, 2, true);
      connected = true;
    } else {
      Serial.println("We have failed to connect to NeuroPlay BLE device; Restart your device to restart scan.");
    }
    doConnect = false;
  }
  delay(5);
}