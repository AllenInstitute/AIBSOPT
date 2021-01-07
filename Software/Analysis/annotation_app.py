"""

This app allows a user to browse through an OPT volume and mark probe track locations.

"""

import sys
from functools import partial
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QFileDialog, QSlider, QLabel
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtGui import QIcon, QKeyEvent, QImage, QPixmap, QColor
from PyQt5.QtCore import pyqtSlot, Qt

from PIL import Image, ImageQt

import numpy as np
import pandas as pd

import os

DEFAULT_SLICE = 400
DEFAULT_VIEW = 0

class App(QWidget):
 
    def __init__(self):
        super().__init__()
        self.title = 'OPT Annotation'
        self.left = 500
        self.top = 100
        self.width = 800
        self.height = 800
        self.initUI()
     
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        grid = QGridLayout()

        self.image = QLabel()
        self.image.setObjectName("image")
        self.image.mousePressEvent = self.clickedOnImage
        im8 = Image.fromarray(np.ones((800,800),dtype='uint8')*255)
        imQt = QImage(ImageQt.ImageQt(im8))
        imQt.convertToFormat(QImage.Format_ARGB32)
        self.image.setPixmap(QPixmap.fromImage(imQt))
        grid.addWidget(self.image, 0, 0)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1022)
        self.slider.setValue(DEFAULT_SLICE)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(100)
        self.slider.valueChanged.connect(self.sliderMoved)
        grid.addWidget(self.slider, 1,0)

        self.slider_values = [DEFAULT_SLICE, DEFAULT_SLICE, DEFAULT_SLICE]

        subgrid = QGridLayout()

        self.probes = ('A1', 'B1', 'C1', 'D1', 'E1', 'F1',
                       'A2', 'B2', 'C2', 'D2', 'E2', 'F2')
        
        self.probe_map = {'Probe A1': 0, 'Probe B1': 1, 'Probe C1': 2, 'Probe D1' : 3,
                          'Probe E1': 4, 'Probe F1': 5,
                          'Probe A2': 6, 'Probe B2': 7, 'Probe C2': 8, 'Probe D2' : 9,
                          'Probe E2': 10, 'Probe F2': 11,
                     }

        self.color_map = {'Probe A1': 'darkred', 'Probe B1': 'peru',
                     'Probe C1': 'goldenrod', 'Probe D1' : 'darkgreen',
                     'Probe E1': 'darkblue', 'Probe F1': 'blueviolet',
                     'Probe A2': 'red', 'Probe B2': 'orange',
                     'Probe C2': 'yellow', 'Probe D2' : 'green',
                     'Probe E2': 'blue', 'Probe F2': 'violet'}

        self.probe_buttons = [QPushButton('Probe ' + i) for i in self.probes]

        for i, button in enumerate(self.probe_buttons):
            button.setToolTip('Annotate ' + button.text())
            button.clicked.connect(partial(self.selectProbe, button))
            subgrid.addWidget(button, i//6, i % 6)

        self.coronal_button = QPushButton('Coronal', self)
        self.coronal_button.setToolTip('Switch to coronal view')
        self.coronal_button.clicked.connect(self.viewCoronal)

        self.horizontal_button = QPushButton('Horizontal', self)
        self.horizontal_button.setToolTip('Switch to horizontal view')
        self.horizontal_button.clicked.connect(self.viewHorizontal)

        self.sagittal_button = QPushButton('Sagittal', self)
        self.sagittal_button.setToolTip('Switch to sagittal view')
        self.sagittal_button.clicked.connect(self.viewSagittal)

        self.current_view = DEFAULT_VIEW

        subgrid.addWidget(self.coronal_button,2,0,1,2)
        subgrid.addWidget(self.horizontal_button,2,2,1,2)
        subgrid.addWidget(self.sagittal_button,2,4,1,2)

        save_button = QPushButton('Save', self)
        save_button.setToolTip('Save values as CSV')
        save_button.clicked.connect(self.saveData)

        load_button = QPushButton('Load', self)
        load_button.setToolTip('Load volume data')
        load_button.clicked.connect(self.loadData)

        subgrid.addWidget(save_button,3,4)
        subgrid.addWidget(load_button,3,5)

        grid.addLayout(subgrid,2,0)

        self.current_directory = '/mnt/md0/data/opt/production'

        self.data_loaded = False

        self.selected_probe = None

        self.setLayout(grid)
        self.viewCoronal()
        self.show()

    def keyPressEvent(self, e):
        
        if e.key() == Qt.Key_A:
            self.selectProbe(self.probe_buttons[0])
        if e.key() == Qt.Key_B:
            self.selectProbe(self.probe_buttons[1])
        if e.key() == Qt.Key_C:
            self.selectProbe(self.probe_buttons[2])
        if e.key() == Qt.Key_D:
            self.selectProbe(self.probe_buttons[3])
        if e.key() == Qt.Key_E:
            self.selectProbe(self.probe_buttons[4])
        if e.key() == Qt.Key_F:
            self.selectProbe(self.probe_buttons[5])
        if e.key() == Qt.Key_1:
            self.selectProbe(self.probe_buttons[6])
        if e.key() == Qt.Key_2:
            self.selectProbe(self.probe_buttons[7])
        if e.key() == Qt.Key_3:
            self.selectProbe(self.probe_buttons[8])
        if e.key() == Qt.Key_4:
            self.selectProbe(self.probe_buttons[9])
        if e.key() == Qt.Key_5:
            self.selectProbe(self.probe_buttons[10])
        if e.key() == Qt.Key_6:
            self.selectProbe(self.probe_buttons[11])
        if e.key() == Qt.Key_Backspace:
            self.deletePoint()

    def deletePoint(self):
        
        if self.selected_probe is not None:

            if self.current_view == 0:
                matching_index = self.annotations[(self.annotations.AP == self.slider.value()) &
                                                       (self.annotations.probe_name == self.selected_probe)].index.values
            elif self.current_view == 1:
                matching_index = self.annotations[(self.annotations.DV == self.slider.value()) &
                                                       (self.annotations.probe_name == self.selected_probe)].index.values
            elif self.current_view == 2:
                matching_index = self.annotations[(self.annotations.ML == self.slider.value()) &
                                                       (self.annotations.probe_name == self.selected_probe)].index.values

            if len(matching_index) > 0:
                self.annotations = self.annotations.drop(index=matching_index)

                self.saveData()
            
                self.refreshImage()

    def clickedOnImage(self , event):

        if self.data_loaded:
            x = int(event.pos().x() * 1024 / 800)
            y = int(event.pos().y() * 1024 / 800)

            #print('X: ' + str(x))
            #print('Y: ' + str(y))

            if self.selected_probe is not None:
                #print('updating volume')

                if self.current_view == 0:
                    AP = self.slider.value()
                    DV = y
                    ML = x
                    matching_index = self.annotations[(self.annotations.AP == AP) &
                                                       (self.annotations.probe_name == 
                                                        self.selected_probe)].index.values
                elif self.current_view == 1:
                    AP = y
                    DV = self.slider.value()
                    ML = x
                    matching_index = self.annotations[(self.annotations.DV == DV) &
                                                       (self.annotations.probe_name == 
                                                        self.selected_probe)].index.values
                elif self.current_view == 2:
                    AP = 1023 - x
                    DV = y
                    ML = self.slider.value()
                    matching_index = self.annotations[(self.annotations.ML == ML) &
                                                       (self.annotations.probe_name == 
                                                        self.selected_probe)].index.values


                if len(matching_index) > 0:
                    self.annotations = self.annotations.drop(index=matching_index)

                self.annotations = self.annotations.append(pd.DataFrame(data = {'AP' : [AP],
                                    'ML' : [ML],
                                    'DV': [DV],
                                    'probe_name': [self.selected_probe]}), 
                                    ignore_index=True)

                self.saveData()

                self.refreshImage()

    def selectProbe(self, b):

        for button in self.probe_buttons:
            button.setStyleSheet("background-color: white")
        
        b.setStyleSheet("background-color: " + self.color_map[b.text()])

        self.selected_probe = b.text()

    def sliderMoved(self):

        self.slider_values[self.current_view] = self.slider.value()
        self.refreshImage()

    def viewCoronal(self):
        
        self.current_view = 0
        self.slider.setValue(self.slider_values[self.current_view])
        self.coronal_button.setStyleSheet("background-color: gray")
        self.horizontal_button.setStyleSheet("background-color: white")
        self.sagittal_button.setStyleSheet("background-color: white")
        self.refreshImage()

    def viewHorizontal(self):

        self.current_view = 1
        self.slider.setValue(self.slider_values[self.current_view])
        self.coronal_button.setStyleSheet("background-color: white")
        self.horizontal_button.setStyleSheet("background-color: gray")
        self.sagittal_button.setStyleSheet("background-color: white")
        self.refreshImage()

    def viewSagittal(self):

        self.current_view = 2
        self.slider.setValue(self.slider_values[self.current_view])
        self.coronal_button.setStyleSheet("background-color: white")
        self.horizontal_button.setStyleSheet("background-color: white")
        self.sagittal_button.setStyleSheet("background-color: gray")
        self.refreshImage()

    def refreshImage(self):

        colors = ('darkred', 'orangered', 'goldenrod', 
            'darkgreen', 'darkblue', 'blueviolet',
            'red','orange','yellow','green','blue','violet')

        if self.data_loaded:
            plane = np.take(self.volume,
                 self.slider.value(),
                 axis=self.current_view)
            if self.current_view == 2:
                plane = plane.T
            im8 = Image.fromarray(plane)            
        else:
            im8 = Image.fromarray(np.ones((1024,1024),dtype='uint8')*255)
            
        imQt = QImage(ImageQt.ImageQt(im8))
        imQt = imQt.convertToFormat(QImage.Format_RGB16)

        #print(self.current_view)
        #print(self.slider.value())
           
        if self.data_loaded:
            for idx, row in self.annotations.iterrows():

                if self.current_view == 0:
                    shouldDraw = row.AP == self.slider.value()
                    x = row.ML
                    y = row.DV
                elif self.current_view == 1:
                    shouldDraw = row.DV == self.slider.value()
                    x = row.ML
                    y = row.AP
                elif self.current_view == 2:
                    shouldDraw = row.ML == self.slider.value()
                    x = 1023 - row.AP
                    y = row.DV

                if shouldDraw:
                    color = QColor(self.color_map[row.probe_name])
                    
                    for j in range(x-10,x+10):
                        for k in range(y-10,y+10):
                            if pow(j-x,2) + pow(k-y,2) < 20:
                                imQt.setPixelColor(j,k,color)

        pxmap = QPixmap.fromImage(imQt).scaledToWidth(800).scaledToHeight(800)
        self.image.setPixmap(pxmap)

    def loadData(self):
        
        fname, filt = QFileDialog.getOpenFileName(self, 
            caption='Select volume file', 
            directory=self.current_directory,
            filter='*nc.001')

        print(fname)

        self.current_directory = os.path.dirname(fname)
        self.output_file = os.path.join(self.current_directory, 'probe_annotations.csv')

        if fname.split('.')[-1] == '001':

            self.volume = self.loadVolume(fname)
            self.data_loaded = True
            self.setWindowTitle(os.path.basename(fname))
            
            if os.path.exists(self.output_file):
                self.annotations = pd.read_csv(self.output_file, index_col=0)
            else:
                self.annotations = pd.DataFrame(columns = ['AP','ML','DV', 'probe_name'])

            self.refreshImage()

        else:
            print('invalid file')
            
    def saveData(self):
        
        if self.data_loaded:
            self.annotations.to_csv(self.output_file)

    def loadVolume(self, fname, _dtype='u1', num_slices=1023):
        
        dtype = np.dtype(_dtype)

        volume = np.fromfile(fname, dtype) # read it in

        z_size = np.sum([volume[1], volume[2] << pow(2,3)])
        x_size = np.sum([(val << pow(2,i+1)) for i, val in enumerate(volume[8:4:-1])])
        y_size = np.sum([(val << pow(2,i+1)) for i, val in enumerate(volume[12:8:-1])])
        
        fsize = np.array([z_size, x_size, y_size]).astype('int')

        volume = np.reshape(volume[13:], fsize) # remove 13-byte header and reshape
        
        print("Data loaded.")
        
        return volume


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

