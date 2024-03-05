from PyQt5 import QtCore, QtWidgets
from model.neuroplay import NeuroPlay
import json
from PyQt5.QtCore import pyqtSlot

class MainWindow(QtWidgets.QMainWindow):
    np = None
    labelConnected = None
    labelQuery = None
    labelResponse = None

    def __init__(self, *args: object, **kwargs: object) -> object:
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi()

    def closeEvent(self, event):
        self.np.finish()
        event.accept()

    def setupUi(self):
        self.np = NeuroPlay
        self.np.load(self.np)
        self.np.onConnectedChanged.append(self.callbackConnected)
        self.np.onResponse.append(self.callbackResponse)

        layoutModeButtons = QtWidgets.QHBoxLayout()
        modes = [
            {"BCI":"bci"},
            {"Rhythms":"rhythms"},
            {"Spectrum":"lastspectrum"},
            {"Data":"grabFilteredData"}
        ]

        for mode in modes:
            for attribute in mode:
                btn = QtWidgets.QPushButton(attribute)
                m = mode[attribute]
                btn.clicked.connect(self.change_mode_factory(m))
                layoutModeButtons.addWidget(btn, 0)

        layoutModeButtons.addStretch()
        labelInfo = QtWidgets.QLabel()
        labelInfo.setText('<a href="https://neuroplay.ru/api-sdk/NeuroplayPro-API.html">API</a>')
        labelInfo.setOpenExternalLinks(True)
        layoutModeButtons.addWidget(labelInfo)

        self.labelConnected = QtWidgets.QLabel("?")
        self.labelQuery = QtWidgets.QLabel(self.np.url)
        self.labelQuery.setOpenExternalLinks(True)
        self.labelResponse = QtWidgets.QLabel("Response")
        self.labelResponse.setMaximumHeight(400)

        self.centralWidget = QtWidgets.QWidget()

        self.layout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.layout.addWidget(self.labelConnected, 0)
        self.layout.addLayout(layoutModeButtons)
        self.layout.addWidget(self.labelQuery, 0)
        self.layout.addWidget(self.labelResponse, 100)

        self.setObjectName("MainWindow")
        self.setWindowTitle("NeuroPlay")
        self.resize(400, 400)
        self.setCentralWidget(self.centralWidget)

        QtCore.QMetaObject.connectSlotsByName(self)
        self.change_mode("bci")

    def callbackConnected(self, isConnected):
        self.labelConnected.setText('Connected' if isConnected else 'Disconnected')

    def callbackResponse(self, response):
        self.labelResponse.setText(json.dumps(response, indent=2))

    @pyqtSlot()
    def change_mode_factory(self, m):
        return lambda: self.change_mode(m)

    def change_mode(self, mode):
        link = self.np.url + mode
        self.labelQuery.setText('<a href="' + link + '">' + link + '</a>')
        self.np.set_mode(self.np, mode)
