from classes.AbstractDevice import AbstractDevice
from classes.Filter import ContinuousFilter, ContinuousNotchFilter

MAGIC_EMG_MICROVOLTS_BIT = 2.42 * 310.0 / 65535.0

class EMGsensDevice (AbstractDevice) :
    def __init__(self, bleName, bleAddress) :
        super().__init__()
        self.name = bleName
        self.address = bleAddress
        self.dataServiceUUID = "5775ab91-ee53-57e1-a77b-1c87183bd78c"
        self.controlServiceUUID = "a183c5a7-1e93-8deb-a113-e8d5bb5581db"
        self.dataReadUUID = "75851135-953a-7739-c781-5a935531397a"
        self.dataControlUUID = "7395ca15-5997-5a1b-a138-75a7a573b8e5"
        self.notifyUUID = "a397cc38-e8c3-5d7c-9353-31bae53881ff"
        self.samplingRate = 1000
        self.packets = []

        self.channelNames = ["EMG"]
        self.channels = len(self.channelNames)

        self.filters = []
        self.addFilters(2, 200, 50)

    @staticmethod
    def devicesNames():
        return ["EMG-SENS"]  

    def startCommandBytes(self): 
        return bytearray(b'\x01\x00\x64\x00\x01\x00\x00\x02\x00\x9a\xf8\x1b\x1b\x89\x96\xec\x7b\x8b\x27\xe5\xd3\x48\x51\x10\x74\xb2\x7b\x22\xd8\xc3\xd5\xe8\x75\x15\xb8\xd9\x75\xc3\xc9\x27\x5e')
    
    def stopCommandBytes(self): 
        return bytearray(b'\x02\x0c\xd1\x5b\x18\x80\x1c\xaa\x49\x2d\xf8\xc5\x65\xce\x13\xb0\xd9\x70\x5b\x08\x10\xab\x47\xf2\x86\xd1\xcc\xc8\xf4\x34\x8a\x64\x41')

    def parsePacket(self, packet: bytearray):     
        code = int.from_bytes(bytes=[packet[2], packet[3], packet[4], packet[5]], byteorder='little')
        channel = []
        pos = 6
        for i in range(32):
            bytesCount = ((code >> i) & 0x01) + 1
            v = 0
            if bytesCount == 1:
                v = int.from_bytes(bytes=[packet[pos]],byteorder='little',signed=True)
                m = len(channel)
                if m > 0: v = (channel[m-1] / MAGIC_EMG_MICROVOLTS_BIT) + v
            elif bytesCount == 2:
                bb = [packet[pos], packet[pos+1]]
                v = int.from_bytes(bytes=bb,byteorder='little',signed=True)
                        
            pos += bytesCount
            channel.append(v * MAGIC_EMG_MICROVOLTS_BIT)

        channelWiseData = [channel]
        self.processSamples(channelWiseData)


        

