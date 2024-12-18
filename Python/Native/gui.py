
from classes.BleConnector import BleConnector
import asyncio
import sys
import numpy as np
from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QComboBox, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import QTimer
import pyqtgraph as pg

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroPlay SDK Window")  

        self.connector = BleConnector()
        self.connector.callbackFound = self.on_device_found 
        self.connector.callbackData = self.on_device_data
        self.connector.callbackDeviceConnected = self.on_device_connected

        self.comboDevices = QComboBox()
        self.comboDevices.setMinimumWidth(200)

        self.btnRefreshDevices = QPushButton("Search")
        self.btnRefreshDevices.setCheckable(True)
        self.btnConnect = QPushButton("Connect")
        self.btnConnect.setCheckable(True)

        self.plottersLayout = QVBoxLayout()
        self.plotters = []
        self.plots = []
        self.samples = []

        self.maxTime = 10
        self.dataIndex = 0

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
        mainLayout.addWidget(self.label, 0)
        mainLayout.addLayout(self.plottersLayout, 100)

        self.setCentralWidget(centralWidget)

        timer = QTimer(self)
        timer.timeout.connect(self.processOneThing)
        timer.start(100)

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

    def processOneThing(self):        
        n = len(self.plotters)
        m = len(self.samples)
        if n > 0 and n == m:
            for i in range(n):
                self.plots[i].setData(y=self.samples[i])

    def on_device_found(self, deviceName):
        self.comboDevices.addItem(deviceName)
        print('NEW DEVICE', deviceName)  

    def on_device_connected(self, device):
        print('Connected', device)

    def on_device_data(self, data):       
        n = len(data)
        if len(self.samples) != n:

            self.frequency = self.connector.currentDevice.samplingRate

            print('Frequency', self.frequency)
            self.sampleCount = self.maxTime * self.frequency
            msPerSample = 1000 / self.frequency
            timeX = []
            samples = np.zeros((n, self.sampleCount))

            for i in range(self.sampleCount):    
                timeX.append(i * msPerSample)

            print('Filling plots')
            for i in range(n):
                print('Create plot', i)        
                plot = pg.PlotWidget()
                p = plot.plot(x=samples[i], y=timeX, pen=(i,n))
                plot.setYRange(-100, 100)
                text_label = pg.TextItem(self.connector.currentDevice.channelNames[i])
                plot.addItem(text_label)
                # text_label.setPos(-100, -20)
                self.plots.append(p)
                self.plotters.append(plot)
                self.plottersLayout.addWidget(plot)

            # self.timeX = timeX
            self.samples = samples
        
        for i in range(n):
            self.samples[i][self.dataIndex] = float(data[i])

        self.dataIndex += 1
        if self.dataIndex >= self.sampleCount:
            self.dataIndex = 1


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()

    QtAsyncio.run()