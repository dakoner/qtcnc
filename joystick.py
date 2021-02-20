#!/usr/bin/python3
import math
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
import sys
import time
from gamepad_qobject import Gamepad
from mqtt_qobject import MqttClient

STEP_SIZE=2
class Tui(QtCore.QObject):

    def __init__(self, app):
        super(Tui, self).__init__()

        self.app = app
        self.gamepad_thread = QtCore.QThread()
        self.gamepad = Gamepad()
        self.gamepad.messageSignal.connect(self.on_gamepadSignal)
        self.gamepad.moveToThread(self.gamepad_thread)
        self.gamepad_thread.started.connect(self.gamepad.loop)
        self.gamepad_thread.start()

        self.client = MqttClient(self)
        self.client.hostname = "localhost"
        self.client.connectToHost()
        self.client.stateChanged.connect(self.on_stateChanged)
        self.client.messageSignal.connect(self.on_messageSignal)

        self.lastTime = time.time()
        self.lastValue = 0
        self.move_x = False
        self.last_x = 0
        self.move_y = False
        self.last_y = 0

        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.do_status)
        self.status_timer.start(5)

        self.led_state = 0

    def do_status(self):
        if self.move_x or self.move_y:
            cmd = "$J=G91"
            if self.move_x:
                if self.last_x > 0:
                    step = -STEP_SIZE
                else:
                    step = STEP_SIZE
                cmd += " Y%d" % step
            if self.move_y:
                if self.last_y > 0:
                    step = -STEP_SIZE
                else:
                    step = STEP_SIZE

                cmd += " X%d" % step
            feed = int(math.sqrt((self.last_x * self.last_x) + (self.last_y * self.last_y)))
            cmd += " F%d" % feed
            self.client.publish("grblesp32/command", cmd)


    @QtCore.pyqtSlot(int)
    def on_stateChanged(self, state):
        if state == MqttClient.Connected:
            self.client.subscribe("grblesp32/status")
            self.client.subscribe("grblesp32/output")
            self.client.subscribe("grblesp32/state")

    @QtCore.pyqtSlot(str, str)
    def on_messageSignal(self, topic, payload):
        print("Message: ", topic, payload)
        
    @QtCore.pyqtSlot(str, str, int)
    def on_gamepadSignal(self, type_, code, state):
        if type_ == 'Key':
            if code == 'BTN_TL' and state == 1:
                    cmd = "$J=G91 F10000 Z-0.05"
                    self.client.publish("grblesp32/command", cmd)
            elif code == 'BTN_TR' and state == 1:
                    cmd = "$J=G91 F10000 Z0.05"
                    self.client.publish("grblesp32/command", cmd)
            elif code == 'BTN_SELECT' and state == 1:
                    cmd = "M5"
                    self.client.publish("grblesp32/command", cmd)
            elif code == 'BTN_START' and state == 1:
                    if self.led_state < 4:
                        self.led_state += 1
                    else:
                        self.led_state = 0
                    strength = (self.led_state)*1024
                    if strength == 0:
                        strength = 100
                    print("led strength: ", strength)
                    cmd = "M3 S%d" % strength
                    self.client.publish("grblesp32/command", cmd)
        elif type_ == 'Absolute':
            if code in ('ABS_HAT0X', 'ABS_HAT0Y'):
                if state in (-1, 1):
                    move = -15 * state
                    dir_ = 'X'
                    if code == 'ABS_HAT0X':
                        dir_ = 'Y'
                    cmd = "$J=G91 F10000 %s%d" % (dir_, move)
                    print("send cmd", cmd)
                    self.client.publish("grblesp32/command", cmd)
            elif code == 'ABS_X':
                if abs(state) > 100:
                    self.move_x = True
                    self.last_x = state
                else:
                    self.move_x = False
                    self.last_x = 0
                    if not self.move_y:
                        self.client.publish("grblesp32/cancel", "")
            elif code == 'ABS_Y':
                if abs(state) > 100:
                    self.move_y = True
                    self.last_y = state
                else:
                    self.move_y = False
                    self.last_y = 0
                    if not self.move_x:
                        self.client.publish("grblesp32/cancel", "")
 
            # if code == 'ABS_THROTTLE':
            #     t = time.time()
            #     value =  (1024 - (state * 4))
            #     if abs(value - self.lastValue) > 5 or t - self.lastTime > 1000:
            #         cmd = "M3 S%d" % value
            #         self.client.publish("grblesp32/command", cmd)
            #         self.lastTime = t
            #         self.lastValue = value
            

if __name__ == "__main__":
    import sys
    app = QtCore.QCoreApplication(sys.argv)
    tui = Tui(app)
    sys.exit(app.exec_())
