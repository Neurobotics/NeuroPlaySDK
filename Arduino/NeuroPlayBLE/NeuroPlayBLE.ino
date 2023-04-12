/*
Arduino example demonstates how to connect to NeuroPlay devices

This example is tested with M5Stack Atom device (ESP32-Pico processor with BLE/WiFi support).

Boards manager's installations: 
- esp32 by Espressif Systems v2.0.5

Include these urls in "File"->"Preferences"->"Additional boards manager URLs":
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

Usage:
- Use 115200 baud rate
- Scan by sending "{scan}"
- Connect to NeuroPlay device by sending "{connect:NeuroPlay-6C (XXXX)}"
- Values will be displayed as "1:__,2:__,3:__,4:__;5:__;6:__,7:__,8:__" (you can use Serial Plotter)
- To stop send "{stop}"

Author: Dmitry Konyshev <d.konyshev@neurobotics.ru>
https://neuroplay.ru
*/

#include "BLEDevice.h"
#include "String.h"
#include <cstring>
#include "ArduinoQueue.h"

static bool isConnected = false;

/* UUIDs of the EEG BLE service and characteristics */
static BLEUUID NEUROPLAY_EEG_SERVICE("f0001298-0451-4000-b000-000000000000");                             
static BLEUUID NEUROPLAY_DATA_CHAR("f0001299-0451-4000-b000-000000000000");
static BLEUUID NEUROPLAY_CTRL_CHAR("f000129a-0451-4000-b000-000000000000");
static BLEUUID BATTERY_SERVICE("0000180f-0000-1000-8000-00805f9b34fb");
static BLEUUID BATTERY_CHAR("00002a19-0000-1000-8000-00805f9b34fb");

static uint8_t TYPE_UNKNOWN = 0;
static uint8_t TYPE_NEUROPLAY1 = 1;
static uint8_t TYPE_NEUROPLAY8 = 8;

//Messages for characteristics
static uint8_t notificationOn[] = {0x01, 0x00};
static uint8_t notificationData1000Hz[] = {0x01, 0x08};
static uint8_t notificationData125Hz[] = {0x01, 0x01};
static uint8_t notificationOff[] = {0x00, 0x00};

BLEScan* pBLEScan = nullptr;
bool ble_inited = false;

struct Packet {
  uint8_t data[100];
  uint8_t len = 0;
  char i = 0;
};

static ArduinoQueue<Packet> packets(20);
static bool canConnect = false;

long long lastMessage = 0;

String name = "";
bool found = false;
long long lastPacketTime = 0;
uint8_t deviceType = TYPE_UNKNOWN;
BLEAddress *pServerAddress = nullptr;
BLERemoteService* pRemoteService = nullptr;
BLERemoteCharacteristic* dataCharacteristic = nullptr;
BLERemoteCharacteristic* controlCharacteristic = nullptr;
BLERemoteDescriptor* descData = nullptr;
BLEClient* pClient = nullptr;

uint8_t s1, s2, s3;
long d1 = 0;

static void dataNotifyCallback(BLERemoteCharacteristic* pBLERemoteCharacteristic, uint8_t* pData, size_t length, bool isNotify) {
  static uint8_t index = 0;
  Packet p;
  p.i = 1;
  p.len = length;
  memcpy(&p.data, pData, length);
  packets.enqueue(p);
  lastPacketTime = millis();  
}

void stopDevice() {
  packets.clear();  
  if (pBLEScan) {
    pBLEScan->stop();
    pBLEScan->clearResults();
  }
  if (deviceType != TYPE_UNKNOWN) {
    if (dataCharacteristic) {
      if (descData) descData->writeValue((uint8_t*)notificationOff, 2, true);
    }
    if (controlCharacteristic) controlCharacteristic->writeValue((uint8_t*)notificationOff, 2, true);    
  }
  if (pClient) {
    pClient->disconnect();
  }    
  found = false;
  isConnected = false;
  canConnect = false;
}

void reconnect() {
  stopDevice();
  canConnect = true;
  startScan();
}

long long timeToScan = 10000;
long long timeScanStarted = 0;
bool scanFinishedMessaged = true;

//Callback function on received device's advertisement 
class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    if (advertisedDevice.haveName()) {
      std::string devName = advertisedDevice.getName();
      
      Serial.print("{found=");
      Serial.print(devName.c_str());
      Serial.println("}");

      if (canConnect && !found) {
        if (!found && std::strcmp(name.c_str(), devName.c_str()) == 0) {
          if (pServerAddress) {
            free(pServerAddress);
            pServerAddress = nullptr;
          }
          pServerAddress = new BLEAddress(advertisedDevice.getAddress());
          found = true; 
          pBLEScan->stop();
          Serial.println("{scanstopped}");          
        }        
      }
    }
  }
};

static MyAdvertisedDeviceCallbacks* callback = nullptr;

void startScan() {
  if (!ble_inited) {
    BLEDevice::init("NeuroPlayConnector");
    pBLEScan = BLEDevice::getScan();
    if (!callback) callback = new MyAdvertisedDeviceCallbacks();
    pBLEScan->setAdvertisedDeviceCallbacks(callback);
    pBLEScan->setActiveScan(true);
    ble_inited = true;
  }
  Serial.println("{scanstarted}");
  pBLEScan->start(timeToScan / 1000);  
  timeScanStarted = millis();
  scanFinishedMessaged = false;
}

void stopScan() { 
  scanFinishedMessaged = true;
  Serial.println("{scanstopped}");
  stopDevice();  
}  

bool connectToDevice() {
  BLEAddress pAddress = *pServerAddress;  
  if (pClient) {
    pClient->~BLEClient();
    free(pClient);
    pClient = nullptr;
  }
  pClient = BLEDevice::createClient();
  // Connect to the remove device
  pClient->connect(pAddress);

  if (deviceType >= TYPE_NEUROPLAY1 && deviceType <= TYPE_NEUROPLAY8) {
    pRemoteService = pClient->getService(NEUROPLAY_EEG_SERVICE);
    if (pRemoteService == nullptr) {
      Serial.print("{Failed to find EEG service UUID}");
      return false;
    }
    dataCharacteristic = pRemoteService->getCharacteristic(NEUROPLAY_DATA_CHAR);
    controlCharacteristic = pRemoteService->getCharacteristic(NEUROPLAY_CTRL_CHAR);
  }

  if (dataCharacteristic == nullptr || controlCharacteristic == nullptr) {
    Serial.print("{Failed to find EEG service characteristics}");
    return false;
  } 
  dataCharacteristic->registerForNotify(dataNotifyCallback, true);
  return true;
}

void setup() {
  Serial.begin(115200);
  Serial.println("NeuroPlayConnector started, use {startscan} and {connect:NeuroPlay-6C (XXXX)}");
}

void connectDevices(String cmd) {
  int l = cmd.length();
  stopDevice();
  canConnect = false;
  String devName = "";
  uint8_t devCount = 0;
  bool foundDeviceName = false;
  for (int i = 8; i<l; i++) {
    char c = cmd.charAt(i);
    if (c == ';' || i == (l-1)) {        
      name = devName;
      found = false;
      isConnected = false;
      deviceType = TYPE_UNKNOWN;
      if (devName.indexOf("NeuroPlay-6C") == 0) {
        deviceType = TYPE_NEUROPLAY8;
      } else if (devName.indexOf("NeuroPlay-8Cap") == 0) {
        deviceType = TYPE_NEUROPLAY8;
      } else if (devName.indexOf("Physiobelt") == 0) {
        deviceType = TYPE_NEUROPLAY1;
      }
      foundDeviceName = true;
      break;
    } else {
      devName += c;
    }
  } 
  if (foundDeviceName) {
    canConnect = true;
    Serial.println("{connecting}");
    startScan();  
  }
}

void parseMessage(String cmd) {
  lastMessage = millis();
  isConnected = true;
	int l = cmd.length();
	if (cmd == "scan" || cmd == "startscan") {
    Serial.println("{started}");
    stopDevice();
    startScan();		
	}	else if (cmd == "stop" || cmd == "stopscan") {
    stopScan();
		Serial.println("{stopped}");
	} else if (cmd.indexOf("connect:") == 0) {
    connectDevices(cmd);
	}
}

String messageAccum = "";
bool messageStarted = false;

void parseRawMsg (String text) {
	if (text == "") return;
	if (!messageStarted) {
		int bracketPos = text.indexOf('{');
		if (bracketPos >= 0) {
			messageStarted = true;
			text = text.substring(bracketPos + 1);
			parseRawMsg(text);
		}
	} else {
		int bracketPos2 = text.indexOf('}');
		if (bracketPos2 < 0) {
			messageAccum += text;
		} else {
			messageAccum += text.substring(0, bracketPos2);
			parseMessage(messageAccum);
			messageAccum = "";
			messageStarted = false;
			parseRawMsg(text.substring(bracketPos2));
		}
	}
}


const uint8_t packetsInSample = 4;
const uint8_t valuesInPacket = 6;
const uint8_t valuesInSample = valuesInPacket * packetsInSample;
long sample[valuesInSample];

static String NEUROPLAY6_CHANNELS[] = { "", "Fp1", "T3", "O1", "O2", "", "T4", "Fp2", "" };

void loop() {
  if (Serial.available() > 0) {
    String cmd;
    while (Serial.available() > 0) {
      cmd += (char)Serial.read();
    }
    parseRawMsg(cmd);
  } 

  if (packets.itemCount() >= packetsInSample) {
    if (!found) {
      packets.clear();
    } else {
      uint8_t c = 0;
      for (int s = 0; s < packetsInSample; s++) {
        Packet p = packets.dequeue();          
        for (int i = 2; i<p.len; i+=3) {
          d1 = ((long(p.data[i]) << 24) + (long(p.data[i+1]) << 16) + (long(p.data[i+2]) << 8)) / 5369;
          sample[c++] = d1;
        }
      }
      if (deviceType == TYPE_NEUROPLAY1) {
        //Single channel, 1000 Hz
        for (int i = 0; i<valuesInSample; i++) {
          Serial.print(String(sample[i]));
          Serial.print(',');
        }
      } else if (deviceType == TYPE_NEUROPLAY8) {
        int ch = 1;
        // 8 channels, 125 Hz
        for (int i = 0; i<valuesInSample; i++) {
          Serial.print(String(ch));
          Serial.write(':');
          Serial.print(String(sample[i]));
          Serial.print(',');
          ch++;
          if (ch > 8) {
            ch = 1;
            Serial.println();
          }
        }
      } 
    }
  }

  if (canConnect) {
    if (found) {
      if (!isConnected) {
        if (connectToDevice()) {
          uint8_t type = deviceType;
          bool good = true;
          if (type == TYPE_UNKNOWN) {
            good = false;
          } else if (type >= TYPE_NEUROPLAY1 && type <= TYPE_NEUROPLAY8) {
            if (dataCharacteristic) {
              descData = dataCharacteristic->getDescriptor(BLEUUID((uint16_t)0x2902));
              if (descData) {
                descData->writeValue((uint8_t*)notificationOn, 2, true);
              } else {
                Serial.println("{Failed to find data descriptor}");
                good = false;
              }
            } else {
              Serial.println("{Failed to find data characteristic}");
            }              
            if (controlCharacteristic) {
              if (type == TYPE_NEUROPLAY1) {
                controlCharacteristic->writeValue((uint8_t*)notificationData1000Hz, 2, true);  
              } else if (type == TYPE_NEUROPLAY8) {
                controlCharacteristic->writeValue((uint8_t*)notificationData125Hz, 2, true); 
              }
            } else {
              Serial.println("{Failed to find control characteristic}");
              good = false;
            }
          }

          if (good) {
            isConnected = true;
            lastPacketTime = millis();
            Serial.print("{connected=");
            Serial.print(name);
            Serial.println("}");
          }
        }
      } 
    } else {
      if ((millis() - lastPacketTime) > 5000) {
        found = false;
        isConnected = false; 
        startScan();
        return; 
      }
    }
  } else {
    if (!scanFinishedMessaged && millis() - timeScanStarted > timeToScan) {
      scanFinishedMessaged = true;
      Serial.println("{scanstopped}");
    }
  }
}
