from classes.BleConnector import BleConnector
import asyncio
import sys

from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QComboBox, QLabel, QVBoxLayout, QHBoxLayout, QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroPlay SDK Window")  

        self.connector = BleConnector()
        self.connector.callbackFound = self.on_device_found 
        self.connector.callbackData = self.on_device_data

        self.comboDevices = QComboBox()
        self.comboDevices.setMinimumWidth(200)

        self.btnRefreshDevices = QPushButton("Search")
        self.btnRefreshDevices.setCheckable(True)
        self.btnConnect = QPushButton("Connect")
        self.btnConnect.setCheckable(True)

        self.btnConnect.clicked.connect(lambda: asyncio.ensure_future(self.handle_connect()))
        self.btnRefreshDevices.clicked.connect(lambda: asyncio.ensure_future(self.handle_search()))

        self.label = QLabel("")

        topRow = QHBoxLayout()
        topRow.addWidget(self.btnRefreshDevices)
        topRow.addWidget(self.comboDevices)
        topRow.addWidget(self.btnConnect)
        topRow.addStretch(1)

        centralWidget = QWidget()
        mainLayout = QVBoxLayout(centralWidget)
        mainLayout.addLayout(topRow, 0)
        mainLayout.addWidget(self.label)

        self.setCentralWidget(centralWidget)

    async def handle_connect(self):   
        print('Handle connect', self.btnConnect.isChecked())     
        if self.btnConnect.isChecked():
            if self.btnRefreshDevices.isChecked():
                self.btnRefreshDevices.setChecked(False)
                await self.handle_search()
            npName = self.comboDevices.currentText()
            if npName != "":
                self.connector.connectTo = npName
                await self.connector.connect_device()
        else:
            await self.connector.disconnect_device()
       

    async def handle_search(self):
        print("Handle search", self.btnRefreshDevices.isChecked())
        if self.btnRefreshDevices.isChecked():
            if self.btnConnect.isChecked():
                self.btnConnect.setChecked(False)
                await self.handle_connect()
            self.comboDevices.clear()
            for device in self.connector.devices:
                self.comboDevices.addItem(device.name)
            await self.connector.search()
        else:
            await self.connector.stop_search()

    def on_device_found(self, deviceName):
        self.comboDevices.addItem(deviceName)
        print('NEW DEVICE', deviceName)  

    def on_device_data(self, data):
        # print('data', data)
        s = ''.join(str(x) for x in data)
        self.label.setText(s)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    QtAsyncio.run()