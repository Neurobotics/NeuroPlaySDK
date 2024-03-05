from bleak import BleakScanner
from classes.NeuroPlayDevice import NeuroPlayDevice

class BleConnector:
    def __init__(self):
        self.data = []
        self.foundDevices = []
        self.devices = []
        self.connectTo = []        

    def availableDevices(self):
        return self.foundDevices
    
    def data_handler(self, data: tuple):
        print(data)

    def multiStartsWith(name: str, names: tuple) -> bool:
        for n in names:
            if name.startswith(n): return True
        return False
    
    async def disconnectAll(self):
        for device in self.devices:
            if device.disconnect: await device.disconnect()

    async def search(self):
        async with BleakScanner() as scanner:
            print("Scanning for NeuroPlay devices", NeuroPlayDevice.devicesNames())
            async for bd, ad in scanner.advertisement_data():
                name = (ad.local_name or "")
                if name not in self.foundDevices:                
                    if BleConnector.multiStartsWith(name, NeuroPlayDevice.devicesNames()): 
                        print(f"> Found {name}")
                        self.foundDevices.append(name)

                        if name in self.connectTo: 
                            np = NeuroPlayDevice(name, bd.address)
                            np.setFilteredDataCallback(self.data_handler)
                            self.devices.append(np)
                            await np.connect()


    

                    