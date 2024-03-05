from classes.BleConnector import BleConnector
# from classes.AbstractDevice import AbstractDevice
import asyncio

connector = BleConnector()

def main():
    # AbstractDevice.VerboseOutput = True
    connector.connectTo = ["NeuroPlay-6C (0615)"]
    asyncio.run(connector.search())

if __name__ == "__main__":
    main()