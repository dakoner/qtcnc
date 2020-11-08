import numpy as np
import pickle

from PyQt5 import QtWidgets, QtCore, uic
import sys 
import os
import subprocess
from grblesp32_qobject import GRBLESP32Client, STATE_READY

prefix="z:\\yard_pano\\4"

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('grid.ui', self)
        
        self.home_x_button.clicked.connect(self.home_x_button_clicked)
        self.home_y_button.clicked.connect(self.home_y_button_clicked)

        self.search_grid_button.clicked.connect(self.search_grid_button_clicked)

        self.grblesp32 = GRBLESP32Client()
        self.grblesp32.messageSignal.connect(self.on_ramps_read)
        self.grblesp32.statusSignal.connect(self.on_ramps_status)
        self.grblesp32.stateSignal.connect(self.on_ramps_state)

        self.state = "INITIAL"

    def home_x_button_clicked(self):
        self.grblesp32.home("x")
  
    def home_y_button_clicked(self):
        self.grblesp32.home("y")



    def search_grid_button_clicked(self):
        az =np.arange(self.start_az_spinbox.value(), self.end_az_spinbox.value(), 10)
        alt = np.arange(self.start_alt_spinbox.value(), self.end_alt_spinbox.value(), 5)
        xx, yy = np.meshgrid(az, alt)
        self.grid = np.vstack([xx.ravel(), yy.ravel()]).T

        self.search_grid_timer = QtCore.QTimer()
        self.search_grid_timer.timeout.connect(self.search_grid_next)
        self.search_grid_timer.start(100)
        self.state = "SEARCHING"
        self.grid_index = 0
        #pto_vars_fname = prefix + "\\pto_vars"
        #self.pto_vars = open(pto_vars_fname, "w")
        self.pto_vars = {}

    def search_grid_next(self):
        grid_location = self.grid[self.grid_index]
        

        if self.state == "SEARCHING":
            print("Move to", self.grid_index, grid_location)
            self.absolute_move_to(grid_location[0], grid_location[1])
            self.state = "MOVE_SENT"
        # should wait for ok
        elif self.state == "MOVING":
            self.grblesp32.send_line("G4 P0")
            self.state = "DWELLING"
        # should wait for ok
        elif self.state == "DONE_MOVING":
            print("At grid location %d of %d" % (self.grid_index, len(self.grid)))
            # Will block UI for picture duration, should run in thread
            p = "test.%06.3f,%06.3f.jpg"% (grid_location[0], grid_location[1])
            fname = os.path.join(prefix, p)
            print(fname)
            subprocess.call(["C:\\Program Files (x86)\\digiCamControl\\CameraControlCmd.exe", "/filename", fname , "/capturenoaf"])
            roll = 0
            pitch = grid_location[1]
            yaw = grid_location[0]
            
            self.pto_vars[p] = (roll, pitch, yaw)
            pto_vars_fname = prefix + "\\pto_vars.pkl"
            pickle.dump(self.pto_vars, open(pto_vars_fname, "wb"))
            self.state = "PICTURING"
        elif self.state == "PICTURING":
            print("Grid index:", self.grid_index, "len(self.grid):", len(self.grid))
            if self.grid_index == len(self.grid) - 1:
                print("at end")
                self.search_grid_timer.stop()
                del self.search_grid_timer
                
                #self.pto_vars.close()
                self.state = "DONE"
            else:
                self.grid_index += 1
                self.state = "SEARCHING"

    def on_ramps_read(self, data):
        pass
        #print(data)

    def on_ramps_status(self, data):
        self.grbl_status.setText(data['state'])
        if 'm_pos' in data:
            pos = data['m_pos']
            #print(pos)
            self.position_x.display(pos[0])
            self.position_y.display(pos[1])

    def on_ramps_state(self, state):
        print("state update:", state)
        self.state_value.setText(str(state))
        if state == STATE_READY:
            print("in STATE_READY, self.state is", self.state)
            if self.state == "MOVE_SENT":
                self.state = "MOVING"
            elif self.state == "DWELLING":
                self.state = "DONE_MOVING"
            else:
                print("Unexpected state:", state)
        else:
            print("No action for state", state)

    def relative_move_to(self, delta_x, delta_y):
        cmd = "G91 G21 F1000 X%.3f Y%.3f" % (delta_x, delta_y)
        self.grblesp32.send_line(cmd)


    def absolute_move_to(self, x, y):
        cmd = "G90 G21 G0 X%.3f Y%.3f" % (x, y)
        print("Moving to", cmd)
        if not self.grblesp32.send_line(cmd):
            print("Failed to send line")


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':      
    main()