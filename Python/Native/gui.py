
from classes.BleConnector import BleConnector
import asyncio
import numpy as np
from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import QTimer
import pyqtgraph as pg

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

        self.plottersLayout = QVBoxLayout()
        self.plotters = []
        self.plots = []
        self.samples = []

        self.maxTime = 10
        self.dataIndex = 0

        self.btnConnect.clicked.connect(lambda: asyncio.ensure_future(self.handle_connect()))
        self.btnRefreshDevices.clicked.connect(lambda: asyncio.ensure_future(self.handle_search()))

        topRow = QHBoxLayout()
        topRow.addWidget(self.btnRefreshDevices)
        topRow.addWidget(self.comboDevices)
        topRow.addWidget(self.btnConnect)
        topRow.addStretch(1)

        centralWidget = QWidget()
        mainLayout = QVBoxLayout(centralWidget)
        mainLayout.addLayout(topRow, 0)
        mainLayout.addLayout(self.plottersLayout, 100)

        self.setCentralWidget(centralWidget)

        timerPlot = QTimer(self)
        timerPlot.timeout.connect(self.on_plot_timeout)
        timerPlot.start(50)

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

    def on_plot_timeout(self):        
        n = len(self.plotters)
        m = len(self.samples)
        if n > 0 and n == m:
            for i in range(n):
                self.plots[i].setData(y=self.samples[i])

    def on_device_found(self, deviceName):
        self.comboDevices.addItem(deviceName)

    def on_device_data(self, data):       
        n = len(data)
        if len(self.samples) != n:
            self.frequency = self.connector.currentDevice.samplingRate
            self.sampleCount = self.maxTime * self.frequency
            self.samples = np.zeros((n, self.sampleCount))

            for i in range(n):    
                plot = pg.PlotWidget()
                p = plot.plot(x=self.samples[i], pen=(i,n))
                plot.setYRange(-100, 100)
                text_label = pg.TextItem(self.connector.currentDevice.channelNames[i])
                plot.addItem(text_label)
                self.plots.append(p)
                self.plotters.append(plot)
                self.plottersLayout.addWidget(plot)
        
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