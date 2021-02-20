#!/usr/bin/python3
import math
from PyQt5 import QtCore
from mqtt_qobject import MqttClient
from qt_grbl import grblesp32_serial_qobject

class Tui(QtCore.QObject):

    def __init__(self, app):
        super(Tui, self).__init__()

        self.app = app
        self.client = MqttClient(self)
        self.client.hostname = "localhost"
        self.client.connectToHost()
        self.client.stateChanged.connect(self.on_stateChanged)
        self.client.messageSignal.connect(self.on_messageSignal)

        self.grblesp32 = grblesp32_serial_qobject.GRBLESP32Client()
        self.grblesp32.messageSignal.connect(self.on_ramps_read)
        self.grblesp32.statusSignal.connect(self.on_ramps_status)
        self.grblesp32.stateSignal.connect(self.on_ramps_state)
        
    @QtCore.pyqtSlot(int)
    def on_stateChanged(self, state):
        if state == MqttClient.Connected:
            self.client.subscribe("grblesp32/command")
            self.client.subscribe("grblesp32/cancel")


    @QtCore.pyqtSlot(str, str)
    def on_messageSignal(self, topic, payload):
        if topic == 'grblesp32/command':    
            print("Got command:", payload)
            if not self.grblesp32.send_line(payload):
                print("Failed sending line", payload)
        elif topic == 'grblesp32/cancel':
            print("Cancelling")
            self.grblesp32.internal_write(0x85)

    def on_ramps_read(self, data):
        print("grblesp32 serial read:", data)
        self.client.publish("grblesp32/output", data)

    def on_ramps_status(self, status):
        print("grblesp32 serial status:", status)
        self.client.publish("grblesp32/status", status)

    def on_ramps_state(self, state):
        print("grblesp32 serial state:", state)
        self.client.publish("grblesp32/state", state)

if __name__ == "__main__":
    import sys
    app = QtCore.QCoreApplication(sys.argv)
    tui = Tui(app)
    sys.exit(app.exec_())