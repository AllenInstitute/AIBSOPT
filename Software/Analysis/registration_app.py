"""
This app allows a user to browse through an OPT volume and add key points used for 3D volume registration.

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
NUM_LANDMARK_SLICES = 12
NUM_LANDMARKS_PER_SLICE = 32
BUTTONS_PER_COLUMN = 8
IMG_WIDTH = 700

class App(QWidget):
 
    def __init__(self):
        super().__init__()
        self.title = 'OPT Annotation'
        self.left = 100
        self.top = 100
        self.width = 1800
        self.height = IMG_WIDTH
        self.initUI()
     
    def initUI(self):
        
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        grid = QGridLayout()

        self.image = QLabel()
        self.image.setObjectName("image")
        self.image.mousePressEvent = self.clickedOnImage
        im8 = Image.fromarray(np.ones((IMG_WIDTH,IMG_WIDTH),dtype='uint8')*255)
        imQt = QImage(ImageQt.ImageQt(im8))
        imQt.convertToFormat(QImage.Format_ARGB32)
        self.image.setPixmap(QPixmap.fromImage(imQt))
        grid.addWidget(self.image, 0, 4, 4, 4)
        
        self.template = QLabel()
        self.template.setObjectName("template")
        self.template.setPixmap(QPixmap.fromImage(imQt))
        grid.addWidget(self.template, 0, 0, 4, 4)

        self.slider1 = QSlider(Qt.Horizontal)
        self.slider1.setMinimum(0)
        self.slider1.setMaximum(1022)
        self.slider1.setValue(DEFAULT_SLICE)
        self.slider1.setTickPosition(QSlider.TicksBelow)
        self.slider1.setTickInterval(100)
        self.slider1.valueChanged.connect(self.imageSliderMoved)
        grid.addWidget(self.slider1, 4, 4, 1, 4)
        
        self.slider2 = QSlider(Qt.Horizontal)
        self.slider2.setMinimum(0)
        self.slider2.setMaximum(1022)
        self.slider2.setValue(DEFAULT_SLICE)
        self.slider2.setTickPosition(QSlider.TicksBelow)
        self.slider2.setTickInterval(100)
        self.slider2.valueChanged.connect(self.templateSliderMoved)
        grid.addWidget(self.slider2, 4, 0, 1, 4)

        subgrid = QGridLayout()

        self.landmark_buttons = [QPushButton(str(i+1)) for i in range(NUM_LANDMARKS_PER_SLICE)]

        for i, button in enumerate(self.landmark_buttons):
            button.setToolTip('Landmark ' + button.text())
            if i > 0:
                button.setStyleSheet("background-color: white")
            else:
                button.setStyleSheet("background-color: pink")
            button.clicked.connect(partial(self.selectLandmark, button))
            subgrid.addWidget(button,int(i % BUTTONS_PER_COLUMN), int(np.floor(i/BUTTONS_PER_COLUMN)))
            
        self.landmarkSlider = QSlider(Qt.Horizontal)
        self.landmarkSlider.setMinimum(0)
        self.landmarkSlider.setMaximum(NUM_LANDMARK_SLICES - 1)
        self.landmarkSlider.setValue(0)
        self.landmarkSlider.setTickPosition(QSlider.TicksBelow)
        self.landmarkSlider.setTickInterval(1)
        self.landmarkSlider.valueChanged.connect(self.landmarkSliderMoved)

        subgrid2 = QGridLayout()
        
        save_button = QPushButton('Save', self)
        save_button.setToolTip('Save values as CSV')
        save_button.clicked.connect(self.saveData)

        load_button = QPushButton('Load', self)
        load_button.setToolTip('Load volume data')
        load_button.clicked.connect(self.loadData)

        subgrid2.addWidget(self.landmarkSlider, 0,0,1,2)
        subgrid2.addWidget(save_button,1,0)
        subgrid2.addWidget(load_button,1,1)
        
        grid.addLayout(subgrid,1,8,1,2)
        grid.addLayout(subgrid2,2,8,1,2)

        self.current_directory = '/mnt/md0/data/opt/production'
        template_path = '/mnt/md0/data/opt/template_brain/template_fluor.pvl.nc.001'
        self.template_annotations = np.load('/mnt/md0/data/opt/template_brain/landmark_annotations.npy')

        self.data_loaded = False
        
        self.template_volume = self.loadVolume(template_path)
        self.refreshTemplate()

        self.selected_landmark = 0
        self.landmarkSlice = 0
        self.landmarkIndex = 0

        self.setLayout(grid)
        self.show()

    def keyPressEvent(self, e):
        
        if e.key() == Qt.Key_Backspace:
            self.deletePoint()
        elif e.key() == Qt.Key_D:
            self.moveForward()
        elif e.key() == Qt.Key_A:
            self.moveBackward()

    def deletePoint(self):
        
        if self.selected_landmark is not None:

            self.annotations[self.landmarkIndex, :] = -1
            self.saveData()
            self.refreshImage()

    def clickedOnImage(self , event):

        x = event.pos().x()
        y = event.pos().y()

        if self.selected_landmark is not None and self.data_loaded:

            keypoint = np.array([x * 1024 / IMG_WIDTH, y * 1024 / IMG_WIDTH, self.slider1.value()])
            
            self.annotations[self.landmarkIndex, : ] = keypoint
            
            self.saveData()
            
        self.refreshImage()

    def landmarkSliderMoved(self):
        
        self.landmarkSlice = self.landmarkSlider.value()
        self.landmarkIndex = self.selected_landmark + self.landmarkSlice * NUM_LANDMARKS_PER_SLICE
        
        self.goToAnnotation()

    def selectLandmark(self, b):

        for button in self.landmark_buttons:
            button.setStyleSheet("background-color: white")
        
        b.setStyleSheet("background-color: pink")

        self.selected_landmark = int(b.text()) - 1
        
        self.landmarkIndex = self.selected_landmark + self.landmarkSlice * NUM_LANDMARKS_PER_SLICE
        
        self.goToAnnotation()
        
    def moveForward(self):
        
        self.landmarkIndex += 1
        
        if self.landmarkIndex == NUM_LANDMARKS_PER_SLICE * NUM_LANDMARK_SLICES:
            self.landmarkIndex -= 1
            
        self.move()
        
    def moveBackward(self):
        self.landmarkIndex -= 1
        
        if self.landmarkIndex == -1:
            self.landmarkIndex = 0
            
        self.move()
        
    def move(self):
        
        self.landmarkSlice = int(np.floor(self.landmarkIndex / NUM_LANDMARKS_PER_SLICE))
        
        self.landmarkSlider.blockSignals(True)
        self.landmarkSlider.setValue(self.landmarkSlice)
        self.landmarkSlider.blockSignals(False)
        
        buttonIndex = (self.landmarkIndex) % NUM_LANDMARKS_PER_SLICE
     
        self.selectLandmark(self.landmark_buttons[buttonIndex])
        
    def goToAnnotation(self):
        
        template_slice = self.template_annotations[self.landmarkIndex, 2]
        self.slider2.setValue(template_slice)
        
        self.refreshTemplate()
        
        if self.data_loaded:
            image_slice = self.annotations[self.landmarkIndex, 2]
            
            if image_slice > -1:
                self.slider1.setValue(image_slice)
                
                self.refreshImage()

    def imageSliderMoved(self):

        self.refreshImage()
        
    def templateSliderMoved(self):

        self.refreshTemplate()
        
    def refreshTemplate(self):

        im8 = Image.fromarray(self.template_volume[self.slider2.value(),:,:])            
        imQt = QImage(ImageQt.ImageQt(im8))
        imQt = imQt.convertToFormat(QImage.Format_RGB16)
            
        if True:
            for i in range(0,self.template_annotations.shape[0]):
                z = int(self.template_annotations[i,2])
                
                if z == self.slider2.value():
                    x = int(self.template_annotations[i,0])
                    y = int(self.template_annotations[i,1])
                    
                    if i == self.landmarkIndex:
                        color = QColor('magenta')
                    else:
                        color = QColor('pink')
                    
                    if x > -1 and y > -1:
                    
                        for j in range(x-15,x+15):
                            for k in range(y-15,y+15):
                                if pow(j-x,2) + pow(k-y,2) < 30:
                                    imQt.setPixelColor(j,k,color)

        pxmap = QPixmap.fromImage(imQt).scaledToWidth(IMG_WIDTH).scaledToHeight(IMG_WIDTH)
        self.template.setPixmap(pxmap)

    def refreshImage(self):

        if self.data_loaded:
            im8 = Image.fromarray(self.volume[self.slider1.value(),:,:])            
        else:
            im8 = Image.fromarray(np.ones((1024,1024),dtype='uint8')*255)
            
        imQt = QImage(ImageQt.ImageQt(im8))
        imQt = imQt.convertToFormat(QImage.Format_RGB16)
            
        if self.data_loaded:
            for i in range(0,self.annotations.shape[0]):
                z = int(self.annotations[i,2])
                
                if z == self.slider1.value():
                    x = int(self.annotations[i,0])
                    y = int(self.annotations[i,1])
                    
                    if i == self.landmarkIndex:
                        color = QColor('magenta')
                    else:
                        color = QColor('pink')
                    
                    if x > -1 and y > -1:
                    
                        for j in range(x-15,x+15):
                            for k in range(y-15,y+15):
                                if pow(j-x,2) + pow(k-y,2) < 30:
                                    imQt.setPixelColor(j,k,color)

        pxmap = QPixmap.fromImage(imQt).scaledToWidth(IMG_WIDTH).scaledToHeight(IMG_WIDTH)
        self.image.setPixmap(pxmap)

    def loadData(self):
        
        fname, filt = QFileDialog.getOpenFileName(self, 
            caption='Select volume file', 
            directory=self.current_directory,
            filter='*nc.001')

        print(fname)

        self.current_directory = os.path.dirname(fname)
        self.output_file = os.path.join(self.current_directory, 'landmark_annotations.npy')

        if fname.split('.')[-1] == '001':

            self.volume = self.loadVolume(fname)
            self.data_loaded = True
            self.setWindowTitle(os.path.basename(fname))
            
            if os.path.exists(self.output_file):
                self.annotations = np.load(self.output_file)
            else:
                self.annotations = np.zeros((NUM_LANDMARK_SLICES * NUM_LANDMARKS_PER_SLICE,3 )) - 1
            self.refreshImage()

        else:
            print('invalid file')
            
    def saveData(self):
        
        if self.data_loaded:
            np.save(self.output_file, self.annotations)

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

