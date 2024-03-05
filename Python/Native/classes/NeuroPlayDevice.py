from classes.AbstractDevice import AbstractDevice
from classes.Filter import ContinuousFilter, ContinuousNotchFilter

MAGIC_MICROVOLTS_BIT = 0.000186265
NEUROPLAY_QUEUE_SIZE = 4
NEUROPLAY_PACKET_SIZE = 20

def bytes_to_signed_int(bytes, byteorder = 'big'):
    num = int.from_bytes(bytes, byteorder)    
    # Check if the most significant bit is set (indicating a negative number)
    if (bytes[0] & 0x80) != 0: # for big-endian
        # Calculate the two's complement negative value
        num -= 1 << (len(bytes) * 8)
    return num

class NeuroPlayDevice (AbstractDevice) :
    def __init__(self, bleName, bleAddress) :
        super().__init__()
        self.name = bleName
        self.address = bleAddress
        self.dataServiceUUID = "f0001298-0451-4000-b000-000000000000"
        self.dataReadUUID = "f0001299-0451-4000-b000-000000000000"
        self.dataControlUUID = "f000129a-0451-4000-b000-000000000000"
        self.samplingRate = 125
        self.packets = []

        # NeuroPlay-8Cap
        if "8Cap" in bleName: 
            self.channelNames = ["O1", "P3", "C3", "F3", "F4", "C4", "P4", "O2"]
            self.channels = 8
        # NeuroPlay-6C
        else: 
            self.channelNames = ["O1", "T3", "Fp1", "Fp2", "T4", "O2"]
            self.channels = 6

        self.filters = []
        for i in range(self.channels):
            self.filters.append((ContinuousFilter(2, self.samplingRate, 'high'),
                                 ContinuousFilter(40, self.samplingRate, 'low'),
                                 ContinuousNotchFilter(50, self.samplingRate)))

    @staticmethod
    def devicesNames():
        return ("NeuroPlay")    

    def emitSample(self, channelWiseSamples, callback):
        if not callback: return
        n = len(channelWiseSamples)            
        for i in range(3):
            sample = []
            for ch in range(n):
                sample.append(channelWiseSamples[ch][i])
            callback(sample)

    def parsePacket(self, packet):
        self.packets.append(packet)
        if len(self.packets) == NEUROPLAY_QUEUE_SIZE:
            
            if self.packets[0][0] & 0x03 != 0:  #Check packet id             
                self.packets.pop(0)
                return
            meta = []          

            for i in range(NEUROPLAY_QUEUE_SIZE): # 4 packets of 20 bytes (header is 2 bytes)
                p = self.packets[i]
                for j in range(6): # 6 samples per 18 bytes
                    off = 2 + j * 3                    
                    v = bytes_to_signed_int(bytes([p[off], p[off+1], p[off+2], 0x00]), 'big') * MAGIC_MICROVOLTS_BIT                  
                    meta.append(v)


            channelWiseData = []            
            channelWiseData.append([ meta[0 + 0], meta[0 + 8], meta[0 + 16]])
            channelWiseData.append([ meta[1 + 0], meta[1 + 8], meta[1 + 16]])
            channelWiseData.append([ meta[2 + 0], meta[2 + 8], meta[2 + 16]])
            channelWiseData.append([ meta[3 + 0], meta[3 + 8], meta[3 + 16]])
            channelWiseData.append([ meta[4 + 0], meta[4 + 8], meta[4 + 16]])
            channelWiseData.append([ meta[5 + 0], meta[5 + 8], meta[5 + 16]])
            channelWiseData.append([ meta[6 + 0], meta[6 + 8], meta[6 + 16]])
            channelWiseData.append([ meta[7 + 0], meta[7 + 8], meta[7 + 16]])

            if self.channels == 6:
                channelWiseData.pop(6)
                channelWiseData.pop(1)

            if self.dataCallback: self.emitSample(channelWiseData, self.dataCallback)                           
                        
            if self.filteredDataCallback:
                filteredData = []
                index = 0
                for ff in self.filters:
                    channelData = channelWiseData[index]
                    for f in ff:
                        filtered = []
                        for i in range(3):
                            filtered.append(f.apply_filter(channelData[i]))
                        channelData = filtered
                    filteredData.append(channelData)
                    index += 1
                self.emitSample(filteredData, self.filteredDataCallback) 

                
            self.packets.clear()

