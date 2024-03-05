from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

class AbstractDevice:
    VerboseOutput = False

    def __init__(self):
        self.name = None
        self.address = None

        self.dataServiceUUID = None
        self.dataControlUUID = None
        self.dataReadUUID = None
        
        self.dataService = None
        self.dataControlChar = None
        self.dataReadChar = None
        self.dataReadDescriptor = None

        self.device = None
        self.deviceClient = None
        self.dataCallback = None
        self.filteredDataCallback = None
    
    def setDataCallback(self, callback) -> None:
        self.dataCallback = callback

    def setFilteredDataCallback(self, callback) -> None:
        self.filteredDataCallback = callback

    async def disconnect(self) -> None:
        if self.deviceClient:
            await self.deviceClient.stop_notify(self.dataReadUUID)
            await self.deviceClient.write_gatt_char(self.dataControlUUID, bytearray(b'\x00\x00'))

    def parsePacket(self, packet):
        # Should override this function
        print(packet)

    def notification_handler(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        self.parsePacket(data)

    async def connect(self):
        self.device = await BleakScanner.find_device_by_address(self.address)
        if self.device is None:
            print(f"Cannot connect to {self.name}")
        else:
            if AbstractDevice.VerboseOutput: print(f"Connected to {self.name}!")
            self.deviceClient = BleakClient(self.device, winrt=dict(use_cached_services=False))
            await self.deviceClient.connect()
            for service in self.deviceClient.services:
                if AbstractDevice.VerboseOutput: print(f"Found service: {service.uuid}")
                if service.uuid == self.dataServiceUUID:
                    if AbstractDevice.VerboseOutput: print("Found the data service")
                    self.dataService = service
                    for char in service.characteristics:
                        if char.uuid == self.dataControlUUID:
                            self.dataControlChar = char
                            if AbstractDevice.VerboseOutput: print("Found desired control characteristic")
                        if char.uuid == self.dataReadUUID:                            
                            self.dataReadChar = char
                            if AbstractDevice.VerboseOutput: print("Found desired read characteristic")
            
            if AbstractDevice.VerboseOutput: print(f"Device is connected: {self.deviceClient.is_connected}")

            if self.dataService and self.dataControlChar and self.dataReadChar:
                if AbstractDevice.VerboseOutput: print("All services and characteristics found")
                await self.deviceClient.start_notify(self.dataReadUUID, self.notification_handler)
                await self.deviceClient.write_gatt_char(self.dataControlUUID, bytearray(b'\x01\x01'))
            else: 
                print("Desired services and characteristics not found:")
                if not self.dataService: print(f"> Can't find service {self.dataServiceUUID}")
                if not self.dataControlChar: print(f"> Can't find characteristic {self.dataControlUUID}")
                if not self.dataReadChar: print(f"> Can't find characteristic {self.dataReadUUID}")
                self.deviceClient.disconnect()
                self.deviceClient = None
                self.dataService = None
                self.dataControlChar = None
                self.dataReadChar = None
            