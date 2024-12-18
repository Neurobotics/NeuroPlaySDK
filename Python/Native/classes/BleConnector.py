from bleak import BleakScanner
from classes.NeuroPlayDevice import NeuroPlayDevice

class BleConnector:
    def __init__(self):
        self.data = []
        self.foundDevices = []
        self.devices = []
        self.connectTo = "" 
        self.canSearch = True
        self.callbackFound = None  
        self.callbackData = None
        self.scanner = None
        self.currentDevice = None     

    def availableDevices(self):
        return self.foundDevices
    
    def data_handler(self, data: tuple):
        if self.callbackData != None:
            self.callbackData(data)
        else:
            print(data)

    def multiStartsWith(name: str, names: tuple) -> bool:
        for n in names:
            if name.startswith(n): return True
        return False
    
    async def disconnectAll(self):
        for device in self.devices:
            if device.disconnect: await device.disconnect()

    async def stop_search(self):
        self.canSearch = False
        if self.scanner != None:
            await self.scanner.stop()

    async def disconnect_device(self):
        if self.currentDevice != None:
            print('Disconnecting')
            self.currentDevice.setFilteredDataCallback(None)
            await self.currentDevice.disconnect()
            self.currentDevice = None

    async def connect_device(self):
        await self.disconnect_device()
        for device in self.devices:
            if device.name == self.connectTo:
                print('Connecting to', device.name)
                self.currentDevice = device
                self.currentDevice.setFilteredDataCallback(self.data_handler)
                await self.currentDevice.connect()
                return

    async def search(self):
        self.canSearch = True
        self.scanner = BleakScanner()
        print("Scanning for NeuroPlay devices", NeuroPlayDevice.devicesNames(), self.connectTo)
        await self.scanner.start()
        async for bd, ad in self.scanner.advertisement_data():
            if self.canSearch == False:
                return
            name = (ad.local_name or "")
            if name not in self.foundDevices:                
                if BleConnector.multiStartsWith(name, NeuroPlayDevice.devicesNames()): 
                    print(f"> Found {name}")
                    self.foundDevices.append(name)
                    if self.callbackFound:
                        self.callbackFound(name)

                    np = NeuroPlayDevice(name, bd.address)
                    self.devices.append(np)

                    if self.connectTo == name:
                        await self.connect_device()


    

                    