"""
This app allows a user to browse through an OPT volume and add key points used for 3D volume registration.

"""

import sys
from functools import partial
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QFileDialog, QSlider, QLabel
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtGui import QIcon, QKeyEvent, QImage, QPixmap, QColor, QPainter, QPen
from PyQt5.QtCore import pyqtSlot, Qt

from PIL import Image, ImageQt

import numpy as np
import pandas as pd
from scipy.ndimage import rotate, shift

import warnings

import os

NEW_OPT = False

DOWNSAMPLE_FACTOR = 8
IMG_WIDTH = 700
DEFAULT_SLICE = 100

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'OPT Preprocessing'
        self.left = 100
        self.top = 100
        self.width = 1100
        self.height = IMG_WIDTH

        self.currentAxis = 0
        self.rotations = [0,0,0]
        self.currentSlice = [DEFAULT_SLICE, DEFAULT_SLICE, DEFAULT_SLICE]
        self.xshift = [0,0,0]
        self.yshift = [0,0,0]

        self.initUI()

    def initUI(self):

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        grid = QGridLayout()

        self.image = QLabel()
        self.image.setObjectName("image")
        #self.image.mousePressEvent = self.clickedOnImage

        ##im8 = Image.fromarray(np.ones((IMG_WIDTH,IMG_WIDTH),dtype='uint8')*255)
        #imQt = QImage(ImageQt.ImageQt(im8))
        #imQt.convertToFormat(QImage.Format_ARGB32)
        #self.image.setPixmap(QPixmap.fromImage(imQt))

        grid.addWidget(self.image, 0, 0, 4, 4)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(self.currentSlice[self.currentAxis])
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.valueChanged.connect(self.sliderMoved)
        grid.addWidget(self.slider, 4, 0, 1, 4)

        rotate_button_clockwise = QPushButton('', self)
        rotate_button_clockwise.setToolTip('Rotate volume clockwise')
        rotate_button_clockwise.clicked.connect(self.rotateClockwise)
        rotate_button_clockwise.setIcon(QIcon('icons/rotate_cw.png'))

        rotate_button_counterclockwise = QPushButton('', self)
        rotate_button_counterclockwise.setToolTip('Rotate volume counterclockwise')
        rotate_button_counterclockwise.clicked.connect(self.rotateCounterClockwise)
        rotate_button_counterclockwise.setIcon(QIcon('icons/rotate_ccw.png'))

        rotate_button_clockwise_x10 = QPushButton(' x10', self)
        rotate_button_clockwise_x10.setToolTip('Rotate volume clockwise (x10)')
        rotate_button_clockwise_x10.clicked.connect(self.rotateClockwise10x)
        rotate_button_clockwise_x10.setIcon(QIcon('icons/rotate_cw.png'))

        rotate_button_counterclockwise_x10 = QPushButton(' x10', self)
        rotate_button_counterclockwise_x10.setToolTip('Rotate volume counterclockwise (x10)')
        rotate_button_counterclockwise_x10.clicked.connect(self.rotateCounterClockwise10x)
        rotate_button_counterclockwise_x10.setIcon(QIcon('icons/rotate_ccw.png'))

        up_button = QPushButton('', self)
        up_button.setToolTip('Shift volume up')
        up_button.clicked.connect(self.yShiftUp)
        up_button.setIcon(QIcon('icons/up_arrow.png'))

        down_button = QPushButton('', self)
        down_button.setToolTip('Shift volume down')
        down_button.clicked.connect(self.yShiftDown)
        down_button.setIcon(QIcon('icons/down_arrow.png'))

        right_button = QPushButton('', self)
        right_button.setToolTip('Shift volume right')
        right_button.clicked.connect(self.xShiftRight)
        right_button.setIcon(QIcon('icons/right_arrow.png'))

        left_button = QPushButton('', self)
        left_button.setToolTip('Shift volume left')
        left_button.clicked.connect(self.xShiftLeft)
        left_button.setIcon(QIcon('icons/left_arrow.png'))

        view_buttonX = QPushButton('coronal', self)
        view_buttonX.setToolTip('View X axis')
        view_buttonX.clicked.connect(self.selectXAxis)

        view_buttonY = QPushButton('horizontal', self)
        view_buttonY.setToolTip('View Y axis')
        view_buttonY.clicked.connect(self.selectYAxis)

        view_buttonZ = QPushButton('sagittal', self)
        view_buttonZ.setToolTip('View Z axis')
        view_buttonZ.clicked.connect(self.selectZAxis)

        self.lock_button = QPushButton('Lock transform', self)
        self.lock_button.setToolTip('Lock transform for current axis')
        self.lock_button.clicked.connect(self.lock)
        self.lock_button.setStyleSheet("background-color: darkred")
        self.lock_button.setIcon(QIcon('icons/lock.png'))

        save_button = QPushButton('Save', self)
        save_button.setToolTip('Save transformations to JSON')
        save_button.clicked.connect(self.saveData)
        save_button.setIcon(QIcon('icons/save.png'))

        load_button = QPushButton('Load', self)
        load_button.setToolTip('Load images as volume')
        load_button.clicked.connect(self.loadData)
        load_button.setIcon(QIcon('icons/load.png'))

        subgrid = QGridLayout()

        views_grid = QGridLayout()

        views_grid.addWidget(view_buttonX,0,0)
        views_grid.addWidget(view_buttonY,0,1)
        views_grid.addWidget(view_buttonZ,0,2)

        subgrid.addLayout(views_grid, 0, 0, 1, 1)
        subgrid.addWidget(self.lock_button, 1, 0)

        rotate_grid = QGridLayout()

        rotate_grid.addWidget(rotate_button_counterclockwise_x10,0,0)
        rotate_grid.addWidget(rotate_button_counterclockwise,0,1)
        rotate_grid.addWidget(rotate_button_clockwise,0,2)
        rotate_grid.addWidget(rotate_button_clockwise_x10,0,3)

        subgrid.addLayout(rotate_grid, 2, 0, 1, 1)

        arrows_grid = QGridLayout()

        arrows_grid.addWidget(up_button,0,1)
        arrows_grid.addWidget(down_button,2,1)
        arrows_grid.addWidget(left_button,1,0)
        arrows_grid.addWidget(right_button,1,2)

        subgrid.addLayout(arrows_grid, 3, 0, 1, 1)

        save_load_grid = QGridLayout()

        save_load_grid.addWidget(save_button,0,1)
        save_load_grid.addWidget(load_button,0,0)

        subgrid.addLayout(save_load_grid, 4, 0, 1, 1)

        grid.addLayout(subgrid,0,4,2,3)

        self.data_loaded = False

        self.dictionary = {
                "location" : '',
                "mouse" : '',
                "rot1" : 0,
                "rot2" : 0,
                "rot3" : 0,
                "offset1" : 0,
                "offset2" : 0,
                "downsample_factor" : DOWNSAMPLE_FACTOR,
                "output_directory" : ''
            }

        self.setLayout(grid)
        self.refreshImage()
        self.show()

    def keyPressEvent(self, e):

        pass

        #if e.key() == Qt.Key_Backspace:
        #    self.deletePoint()
        #elif e.key() == Qt.Key_D:
        #    self.moveForward()
        #elif e.key() == Qt.Key_A:
        #    self.moveBackward()

    def xShiftRight(self):

        self.yshift[self.currentAxis] += 1
        self.refreshImage()

    def xShiftLeft(self):

        self.yshift[self.currentAxis] -= 1
        self.refreshImage()

    def yShiftUp(self):

        self.xshift[self.currentAxis] -= 1
        self.refreshImage()

    def yShiftDown(self):

        self.xshift[self.currentAxis] += 1
        self.refreshImage()

    def rotateCounterClockwise(self):

        self.rotations[self.currentAxis] += 1
        self.refreshImage()

    def rotateClockwise(self):

        self.rotations[self.currentAxis] -= 1
        self.refreshImage()

    def rotateCounterClockwise10x(self):

        self.rotations[self.currentAxis] += 10
        self.refreshImage()

    def rotateClockwise10x(self):

        self.rotations[self.currentAxis] -= 10
        self.refreshImage()

    def selectZAxis(self):
        self.currentAxis = 2
        self.updateSlider()
        self.refreshImage()

    def selectYAxis(self):
        self.currentAxis = 1
        self.updateSlider()
        self.refreshImage()

    def selectXAxis(self):
        self.currentAxis = 0
        self.updateSlider()
        self.refreshImage()

    def sliderMoved(self):

        self.currentSlice[self.currentAxis] = self.slider.value()
        self.refreshImage()

    def updateSlider(self):
        self.slider.setMaximum(self.volume.shape[self.currentAxis])
        self.slider.setValue(self.currentSlice[self.currentAxis])

    def lock(self):

        if self.data_loaded:
            print('Locking transform...')

            self.lock_button.setStyleSheet("background-color: gray")

            arrays = []

            num_slices = self.volume.shape[self.currentAxis]

            for slice_num in range(num_slices):

                printProgressBar(slice_num+1, num_slices)

                arr = np.take(self.volume, slice_num, axis=self.currentAxis)
                arr = rotate(arr, self.rotations[self.currentAxis],
                             reshape=False)

                arr = shift(arr, [self.xshift[self.currentAxis],
                               self.yshift[self.currentAxis]])
                arrays.append(arr)

            self.volume = np.stack(arrays, axis=self.currentAxis)

            keys = ['rot1','rot2','rot3']

            self.dictionary[keys[self.currentAxis]] += self.rotations[self.currentAxis]

            if self.currentAxis == 0:
                self.dictionary['offset1'] += self.xshift[self.currentAxis] * DOWNSAMPLE_FACTOR
                self.dictionary['offset2'] += self.yshift[self.currentAxis] * DOWNSAMPLE_FACTOR

            self.rotations[self.currentAxis] = 0
            self.xshift[self.currentAxis] = 0
            self.yshift[self.currentAxis] = 0

            self.lock_button.setStyleSheet("background-color: darkred")

            self.refreshImage()

    def drawVerticalLine(self, image, x, maxPts = 257, color='pink'):

        color = QColor(color)

        imageSize = np.delete(np.array(self.volume.shape), self.currentAxis)

        ypts = np.arange(0,imageSize[0])
        xpts = np.ones(ypts.shape) * x

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for i in range(len(xpts)):
                image.setPixelColor(xpts[i],ypts[i],color)

    def drawHorizontalLine(self, image, y, maxPts = 257, color='pink'):

        color = QColor(color)

        imageSize = np.delete(np.array(self.volume.shape), self.currentAxis)

        xpts = np.arange(0,imageSize[1])
        ypts = np.ones(xpts.shape) * y

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for i in range(len(xpts)):
                image.setPixelColor(xpts[i],ypts[i],color)


    def refreshImage(self):

        if self.data_loaded:
            im = np.take(self.volume,
                 self.slider.value(),
                 axis=self.currentAxis)

            im = rotate(im, self.rotations[self.currentAxis], reshape=False)

            im = shift(im, [self.xshift[self.currentAxis],
                           self.yshift[self.currentAxis]])

            im8 = Image.fromarray(im)
        else:
            im8 = Image.fromarray(np.ones((512,512),dtype='uint8')*255)

        imQt = QImage(ImageQt.ImageQt(im8))
        imQt = imQt.convertToFormat(QImage.Format_RGB16)

        if self.data_loaded: # == 0:

            if self.currentAxis == 0:
                self.drawVerticalLine(imQt, 48)
                self.drawVerticalLine(imQt, 209)
                self.drawHorizontalLine(imQt, 75)
                self.drawHorizontalLine(imQt, 182)
            elif self.currentAxis == 1:
                self.drawVerticalLine(imQt, 124)
            elif self.currentAxis == 2:
                self.drawVerticalLine(imQt, 175)

        pxmap = QPixmap.fromImage(imQt).scaledToWidth(IMG_WIDTH).scaledToHeight(IMG_WIDTH)

        self.image.setPixmap(pxmap)

    def loadData(self):

        import glob

        directory = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if len(directory) > 0: # is not None:

            self.current_directory = directory
            print(self.current_directory)

            search_string = os.path.join(self.current_directory,
                                     'trans',
                                     'native',
                                     'recon',
                                     'imgRot__rec*.' +
                                     'tif')

            images = glob.glob(search_string)
            images.sort()

            filenames = images[::DOWNSAMPLE_FACTOR]

            arrays = []

            print('Loading downsampled volume...')

            for file_idx, filename in enumerate(filenames):

                printProgressBar(file_idx+1, len(filenames))
                arr = np.array(Image.open(filename))

                if NEW_OPT:
                    arr = arr - 5000
                    arr[arr < 0] = 0

                arr = arr / pow(2,16) * 255
                arr = arr.astype('uint8')
                arr = arr * 3
                arr[arr > 255] = 255
                arrays.append(arr[0:2052:DOWNSAMPLE_FACTOR,0:2052:DOWNSAMPLE_FACTOR])

            self.volume = np.stack(arrays)

            self.dictionary['location'] = self.current_directory
            self.dictionary['mouse'] = os.path.basename(self.current_directory)

            self.updateSlider()
            self.data_loaded = True
            self.refreshImage()

    def saveData(self):

        if self.data_loaded:

            import json

            output_file = os.path.join(self.current_directory,
                                        'transforms.json')

            print('Data saved to ' + output_file)

            with open(output_file, "w") as outfile:
                json.dump(self.dictionary, outfile)



def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 0, length = 40, fill = '▒'):

    """
    Call in a loop to create terminal progress bar

    Code from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console

    Inputs:
    -------
    iteration - Int
        Current iteration
    total - Int
        Total iterations
    prefix - Str (optional)
        Prefix string
    suffix - Str (optional)
        Suffix string
    decimals - Int (optional)
        Positive number of decimals in percent complete
    length - Int (optional)
        Character length of bar
    fill - Str (optional)
        Bar fill character

    Outputs:
    --------
    None

    """

    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '░' * (length - filledLength)
    sys.stdout.write('\r%s %s %s%% %s' % (prefix, bar, percent, suffix))
    sys.stdout.flush()

    if iteration == total:
        print()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

