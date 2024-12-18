
from classes.BleConnector import BleConnector
import asyncio
import numpy as np
from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QWidget, QSpinBox
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
        self.verticalScaleUV = 100

        self.spinSeconds = QSpinBox()
        self.spinSeconds.setRange(1, 100)
        self.spinSeconds.setValue(self.maxTime)
        self.spinSeconds.setSuffix('s')
        self.spinSeconds.valueChanged.connect(self.change_horizontal_scale)

        self.spinScale = QSpinBox()
        self.spinScale.setRange(10, 1000)
        self.spinScale.setValue(self.verticalScaleUV)
        self.spinScale.setSingleStep(10)
        self.spinScale.setSuffix('uV')
        self.spinScale.setPrefix('±')
        self.spinScale.valueChanged.connect(self.change_vertical_scale)

        self.dataIndex = 0

        self.btnConnect.clicked.connect(lambda: asyncio.ensure_future(self.handle_connect()))
        self.btnRefreshDevices.clicked.connect(lambda: asyncio.ensure_future(self.handle_search()))

        topRow = QHBoxLayout()
        topRow.addWidget(self.btnRefreshDevices)
        topRow.addWidget(self.comboDevices)
        topRow.addWidget(self.btnConnect)
        topRow.addStretch(1)
        topRow.addWidget(self.spinSeconds)
        topRow.addWidget(self.spinScale)

        centralWidget = QWidget()
        mainLayout = QVBoxLayout(centralWidget)
        mainLayout.addLayout(topRow, 0)
        mainLayout.addLayout(self.plottersLayout, 100)

        self.setCentralWidget(centralWidget)

        self.timerPlot = QTimer(self)
        self.timerPlot.timeout.connect(self.on_plot_timeout)
        self.timerPlot.interval = 50
        self.timerPlot.start()

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

    def change_horizontal_scale(self):
        self.timerPlot.stop()
        self.maxTime = int(self.spinSeconds.value())
        self.dataIndex = 0
        self.samples = []
        self.timerPlot.start()

    def change_vertical_scale(self):
        self.verticalScaleUV = int(self.spinScale.value())
        for plot in self.plotters:
            plot.setYRange(-self.verticalScaleUV, self.verticalScaleUV)

    def on_plot_timeout(self):        
        n = len(self.plotters)
        m = len(self.samples)
        if n > 0 and n == m:
            for i in range(n):
                self.plots[i].setData(x=self.timeX, y=self.samples[i])

    def on_device_found(self, deviceName):
        self.comboDevices.addItem(deviceName)

    def on_device_data(self, data):       
        n = len(data)
        if len(self.samples) != n:
            for plot in self.plotters:
                plot.setVisible(False)
                plot.setParent(None)
                plot.deleteLater()

            self.plotters.clear()
            self.plots.clear()

            self.frequency = self.connector.currentDevice.samplingRate
            self.sampleCount = self.maxTime * self.frequency
            self.samples = np.zeros((n, self.sampleCount))

            msPerSample = 1.0 / self.frequency
            timeX = []
            for i in range(self.sampleCount):
                timeX.append(i * msPerSample)
            
            self.timeX = timeX

            for i in range(n):    
                plot = pg.PlotWidget()
                p = plot.plot(x=self.timeX, y=self.samples[i], pen=(i,n))
                plot.setYRange(-self.verticalScaleUV, self.verticalScaleUV)
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