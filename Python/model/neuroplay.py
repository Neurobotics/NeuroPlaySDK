import requests
from model.repeatTimer import RepeatTimer


class NeuroPlay:
    url = "http://127.0.0.1:2336/"
    headers = {'Connection': 'keep-alive', "Accept": "application/json, text/json"}
    num_raw = 0
    interval = 1
    timer = None

    isConnected = False
    onBciReceived = []
    onRhythmsReceived = []
    onConnectedChanged = []
    onConnected = []
    onDisconnected = []
    onResponse = []

    mode = "bci"

    def set_connected(self, connected):
        if self.isConnected != connected:
            print('Connected', connected)
            self.isConnected = connected
            if connected:
                for callback in self.onConnected:
                    callback()
            else:
                for callback in self.onDisconnected:
                    callback()
            for callback in self.onConnectedChanged:
                callback(connected)

    def on_timer(self):
        try:
            data = requests.get(self.url + self.mode)
            if data.ok:
                response = data.json()
                self.set_connected(self, True)
                for callback in self.onResponse:
                    callback(response)
                if self.mode == 'rhythms':
                    if 'rhythms' in response:
                        rhythms = response['rhythms']
                        if len(rhythms) > 0:
                              if len(self.onRhythmsReceived) > 0:
                                for callback in self.onRhythmsReceived:
                                    callback(rhythms)
                    elif 'error' in response:
                        if 'enableDataGrabMode' in response['error']:
                            requests.get(self.url + "enableDataGrabMode")
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            self.set_connected(self, False)

    def load(self):
        self.timer = RepeatTimer(0.1, lambda: self.on_timer(self))
        self.timer.start()

    def finish(self):
        self.timer.cancel()

    def set_mode(self, mode):
        self.mode = mode

    def start_record(self, start=True, path = ''):
        if start:
            requests.get(self.url + "startRecord?path=" + path)
        else:
            requests.get(self.url + "stopRecord")

    def stop_record(self):
        self.stopRecord(False)
