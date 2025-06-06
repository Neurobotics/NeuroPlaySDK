
from classes.BleConnector import BleConnector
from classes.SpectumCalc import SpectrumCalc
import asyncio
import numpy as np
from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QWidget, QSpinBox, QLabel
from PySide6.QtCore import QTimer
import pyqtgraph as pg

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroPlay SDK Window")  

        self.samples = []
        self.maxTime = 10
        self.verticalScaleUV = 100
        self.dataIndex = 0

        self.connector = BleConnector()
        self.connector.callbackFound = self.on_device_found 
        self.connector.callbackData = self.on_device_data

        self.comboDevices = QComboBox()
        self.comboDevices.setMinimumWidth(160)

        self.btnSearchDevices = QPushButton("Search")
        self.btnSearchDevices.setCheckable(True)
        self.btnSearchDevices.clicked.connect(lambda: asyncio.ensure_future(self.handle_search()))

        self.btnConnect = QPushButton("Connect")
        self.btnConnect.setCheckable(True)
        self.btnConnect.clicked.connect(lambda: asyncio.ensure_future(self.handle_connect()))

        plottersHolder = QWidget()
        plottersHolder.setMinimumSize(200, 200)
        plottersHolder.setContentsMargins(0, 0, 0, 0)
        self.plottersLayout = QVBoxLayout(plottersHolder)
        self.plottersLayout.setContentsMargins(8, 8, 8, 8)
        self.plotters = []
        self.plots = []

        spectrumsHolder = QWidget()
        spectrumsHolder.setMinimumSize(200, 200)
        spectrumsHolder.setContentsMargins(0, 0, 0, 0)
        self.spectrumsLayout = QVBoxLayout(spectrumsHolder)
        self.spectrumsLayout.setContentsMargins(8, 8, 8, 8)
        self.spectrumPlotters = []
        self.spectrumPlots = []
        self.spectrums = []

        rhythmsHolder = QWidget()
        rhythmsHolder.setMinimumSize(200, 200)
        rhythmsHolder.setContentsMargins(0, 0, 0, 0)
        self.rhythmsLayout = QVBoxLayout(rhythmsHolder)
        self.rhythmsLayout.setContentsMargins(8, 8, 8, 8)
        self.rhythmsPlotters = []
        self.rhythmsPlots = []
        self.rhythms = []

        graphicsHolder = QHBoxLayout()
        graphicsHolder.addWidget(plottersHolder, 100)
        graphicsHolder.addWidget(spectrumsHolder, 50)
        graphicsHolder.addWidget(rhythmsHolder, 0)

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

        topRow = QHBoxLayout()
        topRow.setContentsMargins(8, 8, 8, 0)
        topRow.addWidget(self.btnSearchDevices)
        topRow.addWidget(self.comboDevices)
        topRow.addWidget(self.btnConnect)
        topRow.addStretch(1)
        topRow.addSpacing(10)
        topRow.addWidget(self.spinSeconds)
        topRow.addWidget(self.spinScale)

        centralWidget = QWidget()
        mainLayout = QVBoxLayout(centralWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.addLayout(topRow, 0)
        mainLayout.addLayout(graphicsHolder, 100)

        self.setCentralWidget(centralWidget)

        self.timerPlot = QTimer(self)
        self.timerPlot.timeout.connect(self.on_plot_timeout)
        self.timerPlot.interval = 50
        self.timerPlot.start()

    async def handle_connect(self):   
        print('Handle connect', self.btnConnect.isChecked())     
        if self.btnConnect.isChecked():
            if self.btnSearchDevices.isChecked():
                self.btnSearchDevices.setChecked(False)
                await self.handle_search()
            npName = self.comboDevices.currentText()
            if npName != "":
                self.connector.connectTo = npName
                await self.connector.connect_device()
        else:
            await self.connector.disconnect_device()
       
    def startSearch(self):
        self.btnSearchDevices.isChecked = True
        self.btnSearchDevices.click()

    async def handle_search(self):
        print("Handle search", self.btnSearchDevices.isChecked())
        if self.btnSearchDevices.isChecked():
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

    def on_spectrum_data(self, index, data, rhythms):
        self.spectrumPlots[index].setData(x=self.spectrums[index].frequencies, y=data)
        t = "δ (0.5-4 Hz)=" + str(int(rhythms[0])) + "%<br>θ &nbsp;&nbsp;(4-8 Hz)=" + str(int(rhythms[1])) + "%<br>α &nbsp;(8-14 Hz)=" + str(int(rhythms[2])) + "%<br>β (14-35 Hz)=" + str(int(rhythms[3])) + "%<br>δ (35-50 Hz)=" + str(int(rhythms[4])) + "%<br>"
        self.rhythmsPlots[index].setText(t)

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

                spec = SpectrumCalc()
                spec.index = i
                self.spectrums.append(spec)
                
                spectrumPlot = pg.PlotWidget()
                p2 = spectrumPlot.plot(x=spec.frequencies, y=spec.spectrum, pen=(i,n))
                spectrumPlot.setYRange(0, 20)
                self.spectrumPlots.append(p2)
                self.spectrumPlotters.append(spectrumPlot)
                self.spectrumsLayout.addWidget(spectrumPlot)

                spec.callback = self.on_spectrum_data

                label = QLabel("?<br>?<br>?<br>?<br>?")
                label.setStyleSheet("font-family: 'Courier New', monospace")

                self.rhythmsLayout.addWidget(label)
                self.rhythmsPlots.append(label)

        
        for i in range(n):
            self.samples[i][self.dataIndex] = float(data[i])
            self.spectrums[i].addData(float(data[i]))
            # self.spectrums[i].addData(float(data[i]))

        self.dataIndex += 1
        if self.dataIndex >= self.sampleCount:
            self.dataIndex = 0


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    QtAsyncio.run()