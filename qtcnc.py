from PyQt5 import QtWidgets, QtCore, uic
import sys 
import os
from grblesp32_qobject import GRBLESP32Client



def distance_for_button(button):
    on = button.objectName()
    if on == 'distance_point1':
        return 0.1
    elif on == 'distance_1':
        return 1
    elif on == 'distance_10':
        return 10
    elif on == 'distance_100':
        return 100
    else:
        print("Unrecognized radio button", on)
        return 0

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('qtcnc.ui', self)
        self.down_button.clicked.connect(self.down_button_clicked)
        self.up_button.clicked.connect(self.up_button_clicked)
        self.right_button.clicked.connect(self.right_button_clicked)
        self.left_button.clicked.connect(self.left_button_clicked)
        self.home_x_button.clicked.connect(self.home_x_button_clicked)
        self.home_y_button.clicked.connect(self.home_y_button_clicked)
        self.dwell_button.clicked.connect(self.dwell_button_clicked)

        self.grblesp32 = GRBLESP32Client()
        self.grblesp32.messageSignal.connect(self.on_ramps_read)
        self.grblesp32.statusSignal.connect(self.on_ramps_status)
        self.grblesp32.stateSignal.connect(self.on_ramps_state)

        self.ramps_input.returnPressed.connect(self.line_entered)


    def line_entered(self):
        line = self.ramps_input.text()
        if not self.grblesp32.send_line(line):
            print("Failed sending line", line)

        self.ramps_input.clear()

    def on_ramps_read(self, data):
        self.ramps_output.insertPlainText(data)
        self.ramps_output.insertPlainText("\n")
        self.ramps_output.verticalScrollBar().setValue(self.ramps_output.verticalScrollBar().maximum())

    def on_ramps_status(self, data):
        self.grbl_status.setText(data['state'])
        if 'm_pos' in data:
            pos = data['m_pos']
            self.position_x.display(pos[0])
            self.position_y.display(pos[1])

    def on_ramps_state(self, state):
        self.status.setText(str(state))
       
    def relative_move_to(self, delta_x, delta_y):
        cmd = "G91 G21 G0 X%5.2f Y%5.2f" % (delta_x, delta_y)
        if not self.grblesp32.send_line(cmd):
            print("Failed to send line, ", cmd)

    def down_button_clicked(self):
        distance = distance_for_button(self.distance_radio_group.checkedButton())
        self.relative_move_to(0, distance)
    
    def up_button_clicked(self):
        distance = distance_for_button(self.distance_radio_group.checkedButton())
        self.relative_move_to(0, -distance)

    def right_button_clicked(self):
        distance = distance_for_button(self.distance_radio_group.checkedButton())
        self.relative_move_to(distance, 0)
    
    def left_button_clicked(self):
        distance = distance_for_button(self.distance_radio_group.checkedButton())
        self.relative_move_to(-distance, 0)
  
    def home_x_button_clicked(self):
        self.grblesp32.home(axis="x")
  
    def home_y_button_clicked(self):
        self.grblesp32.home(axis="y")
 
    def dwell_button_clicked(self):
        self.grblesp32.dwell()

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':      
    main()