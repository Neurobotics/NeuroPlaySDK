from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from classes.Filter import ContinuousFilter, ContinuousNotchFilter

class AbstractDevice:
    VerboseOutput = False

    def __init__(self):
        self.name = None
        self.address = None

        self.dataServiceUUID = None
        self.controlServiceUUID = None
        self.dataControlUUID = None
        self.dataReadUUID = None
        
        self.dataService = None
        self.controlService = None
        self.dataControlChar = None
        self.dataReadChar = None
        self.dataReadDescriptor = None

        self.device = None
        self.deviceClient = None
        self.dataCallback = None
        self.filteredDataCallback = None

        self.samplingRate = 0
        self.channelNames = []
        self.channels = 0
        self.filters = []
    
    def setDataCallback(self, callback) -> None:
        self.dataCallback = callback

    def setFilteredDataCallback(self, callback) -> None:
        self.filteredDataCallback = callback

    def startCommandBytes(self): 
        return bytearray(b'\x01\x01')
    
    def stopCommandBytes(self): 
        return bytearray(b'\x00\x00')
    
    def processSamples(self, channelWiseData):
        if self.dataCallback: 
            self.emitSample(channelWiseData, self.dataCallback)                           
                         
        if self.filteredDataCallback:
            self.emitSample(self.filterData(channelWiseData), self.filteredDataCallback) 

    def emitSample(self, channelWiseSamples, callback):
        if not callback: return
        n = len(channelWiseSamples)   
        if n == 0: return
        m = len(channelWiseSamples[0])         
        for i in range(m):
            sample = []
            for ch in range(n):
                sample.append(channelWiseSamples[ch][i])
            callback(sample)

    def addFilters(self, hiPassFilter = 2.0, lowPassFilter = 40.0, bandStopFilter = 50.0):
        print('Add filters', hiPassFilter, lowPassFilter, bandStopFilter, self.samplingRate)
        for i in range(self.channels):
            filters = []
            if hiPassFilter > 0: filters.append(ContinuousFilter(hiPassFilter, self.samplingRate, 'high'))
            if lowPassFilter > 0: filters.append(ContinuousFilter(lowPassFilter, self.samplingRate, 'low'))
            if bandStopFilter > 0: filters.append(ContinuousNotchFilter(bandStopFilter, self.samplingRate))
            self.filters.append(filters)

    def filterData(self, channelWiseData):
        filteredData = []
        n = len(channelWiseData)
        n2 = len(self.filters)
        if n > 0 and n == n2:
            for i in range(n):
                channelData = channelWiseData[i]
                channelFilters = self.filters[i]
                m = len(channelData)
                for filter in channelFilters:
                    filtered = []
                    for j in range(m):
                        filtered.append(filter.apply_filter(channelData[j]))
                    channelData = filtered
                filteredData.append(channelData)
        else:
            return channelWiseData
        return filteredData

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
        self.device = await BleakScanner.find_device_by_address(self.address, timeout=20)
        if self.device is None:
            print(f"Cannot connect to {self.name}")
        else:
            if AbstractDevice.VerboseOutput: print(f"Connected to {self.name}!")
            self.deviceClient = BleakClient(self.device, winrt=dict(use_cached_services=False))
            await self.deviceClient.connect()
            services = []
            for service in self.deviceClient.services:
                if AbstractDevice.VerboseOutput: print(f"Found service: {service.uuid}")
                if service.uuid == self.dataServiceUUID:
                    if AbstractDevice.VerboseOutput: print("Found the data service")
                    self.dataService = service
                    services.append(service)
                    if self.controlServiceUUID == None:
                        self.controlService = service

                if service.uuid == self.controlServiceUUID:
                    if AbstractDevice.VerboseOutput: print("Found the control service")
                    self.controlService = service
                    services.append(service)             
                    
            
            for service in services:
                for char in service.characteristics:
                    if char.uuid == self.dataControlUUID:
                        self.dataControlChar = char
                        if AbstractDevice.VerboseOutput: print("Found desired control characteristic")
                    if char.uuid == self.dataReadUUID:                            
                        self.dataReadChar = char
                        if AbstractDevice.VerboseOutput: print("Found desired read characteristic")

            if AbstractDevice.VerboseOutput: print(f"Device is connected: {self.deviceClient.is_connected}")

            if self.dataService and self.dataControlChar and self.controlService and self.dataReadChar:
                if AbstractDevice.VerboseOutput: print("All services and characteristics found")
                await self.deviceClient.start_notify(self.dataReadUUID, self.notification_handler)
                await self.deviceClient.write_gatt_char(self.dataControlUUID, self.startCommandBytes())
            else: 
                print("Desired services and characteristics not found:")
                if not self.dataService: print(f"> Can't find service {self.dataServiceUUID}")
                if not self.dataControlChar: print(f"> Can't find characteristic {self.dataControlUUID}")
                if not self.dataReadChar: print(f"> Can't find characteristic {self.dataReadUUID}")
                await self.deviceClient.disconnect()
                self.deviceClient = None
                self.dataService = None
                self.dataControlChar = None
                self.controlService = None
                self.dataReadChar = None
            