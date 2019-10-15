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

        subgrid = QGridLayout()

        self.probes = ('A', 'B', 'C', 'D', 'E', 'F')
        
        self.probe_map = {'Probe A': 0, 'Probe B': 1, 'Probe C': 2, 'Probe D' : 3,
                     'Probe E': 4, 'Probe F': 5}

        self.probe_buttons = [QPushButton('Probe ' + i) for i in self.probes]

        for i, button in enumerate(self.probe_buttons):
            button.setToolTip('Annotate ' + button.text())
            button.clicked.connect(partial(self.selectProbe, button))
            subgrid.addWidget(button,0,i)

        save_button = QPushButton('Save', self)
        save_button.setToolTip('Save values as CSV')
        save_button.clicked.connect(self.saveData)

        load_button = QPushButton('Load', self)
        load_button.setToolTip('Load volume data')
        load_button.clicked.connect(self.loadData)

        subgrid.addWidget(save_button,2,2)
        subgrid.addWidget(load_button,2,3)

        grid.addLayout(subgrid,2,0)

        self.current_directory = '/mnt/md0/data/opt/production'

        self.data_loaded = False

        self.annotations = np.zeros((1023,2,6)) - 1
        self.selected_probe = None

        self.setLayout(grid)
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
        if e.key() == Qt.Key_Backspace:
            self.deletePoint()

    def deletePoint(self):
        
        if self.selected_probe is not None:

            self.annotations[self.slider.value(), 0, self.probe_map[self.selected_probe]] = -1
            self.annotations[self.slider.value(), 1, self.probe_map[self.selected_probe]] = -1
            
            self.saveData()
            
            self.refreshImage()

    def clickedOnImage(self , event):

        x = event.pos().x()
        y = event.pos().y()

        if self.selected_probe is not None:

            self.annotations[self.slider.value(), 0, self.probe_map[self.selected_probe]] = x * 1024 / 800
            self.annotations[self.slider.value(), 1, self.probe_map[self.selected_probe]] = y * 1024 / 800
            
            self.saveData()

        self.refreshImage()

    def selectProbe(self, b):

        color_map = {'Probe A': 'darkred', 'Probe B': 'orangered', 'Probe C': 'goldenrod', 'Probe D' : 'darkgreen',
                     'Probe E': 'darkblue', 'Probe F': 'blueviolet'}

        for button in self.probe_buttons:
            button.setStyleSheet("background-color: white")
        
        b.setStyleSheet("background-color: " + color_map[b.text()])

        self.selected_probe = b.text()

    def sliderMoved(self):

        self.refreshImage()

    def refreshImage(self):

        colors = ('darkred', 'orangered', 'goldenrod', 'darkgreen', 'darkblue', 'blueviolet')

        if self.data_loaded:
            im8 = Image.fromarray(self.volume[self.slider.value(),:,:])            
            #imQt.convertToFormat(QImage.Format_RGB16
        else:
            im8 = Image.fromarray(np.ones((1024,1024),dtype='uint8')*255)
            
        imQt = QImage(ImageQt.ImageQt(im8))
        imQt = imQt.convertToFormat(QImage.Format_RGB16)
            
        for i in range(0,6):
            x = int(self.annotations[self.slider.value(), 0, i])
            y = int(self.annotations[self.slider.value(), 1, i])
            color = QColor(colors[i])
            
            if x > -1 and y > -1:
            
                for j in range(x-10,x+10):
                    for k in range(y-10,y+10):
                        if pow(j-x,2) + pow(k-y,2) < 20:
                            imQt.setPixelColor(j,k,color)

        pxmap =QPixmap.fromImage(imQt).scaledToWidth(800).scaledToHeight(800)
        self.image.setPixmap(pxmap)

    def loadData(self):
        
        fname, filt = QFileDialog.getOpenFileName(self, 
            caption='Select volume file', 
            directory=self.current_directory,
            filter='*nc.001')

        print(fname)

        self.current_directory = os.path.dirname(fname)
        self.output_file = os.path.join(self.current_directory, 'probe_annotations.npy')

        if fname.split('.')[-1] == '001':

            self.volume = self.loadVolume(fname)
            self.data_loaded = True
            self.setWindowTitle(os.path.basename(fname))
            
            if os.path.exists(self.output_file):
                self.annotations = np.load(self.output_file)
            else:
                self.annotations = np.zeros((1023,2,6)) - 1
            self.refreshImage()

        else:
            print('invalid file')
            
    def saveData(self):
        
        if self.data_loaded:
            
            np.save(self.output_file, self.annotations)
            #print("Saved annotations to " + self.output_file + ".")

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

