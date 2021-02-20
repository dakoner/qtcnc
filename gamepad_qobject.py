import sys
from PyQt5 import QtCore
from inputs import devices
from inputs import get_gamepad

class Gamepad(QtCore.QObject):
    messageSignal = QtCore.pyqtSignal(str, str, int)

    def __init__(self, parent=None):
        super(Gamepad, self).__init__(parent)

    def loop(self):
        while True:
            events = get_gamepad()
            for event in events:
                self.messageSignal.emit(event.ev_type, event.code, event.state)
