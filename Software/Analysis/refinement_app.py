"""

This app allows a user to compare CCF structure boundaries with physiological landmarks and update them accordingly.

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
import re

import os

OFFSET_MAP = {'probeA': 120, 'probeB': 346, 'probeC': 572, 'probeD' : 798,
                     'probeE': 1024, 'probeF': 1250}
INDEX_MAP = {'probeA': 0, 'probeB': 1, 'probeC': 2, 'probeD' : 3,
                     'probeE': 4, 'probeF': 5}

structure_tree = pd.read_csv('/mnt/md0/data/opt/template_brain/ccf_structure_tree_2017.csv')

def findBorders(structure_ids):
    
    borders = np.where(np.diff(structure_ids) != 0)[0]
    jumps = np.concatenate((np.array([5]),np.diff(borders)))
    borders = borders[jumps > 3]
    
    return borders


class BoundaryButtons():
    
    def __init__(self, probe, parent):
        self.probe = probe
        self.parent = parent
        self.buttons = []
        
    def createButtons(self):
        
        for i in range(50):
            button = QPushButton(str(i), self.parent)
            button.setGeometry(-100,20+i*50,50,15)
            button.clicked.connect(partial(self.buttonClicked, button))
            
            self.buttons.append(button)
            
    def updateBoundaries(self, structure_ids, border_locs):

        borders = findBorders(structure_ids)
  
        for i, border in enumerate(borders):
            
            try:
                name = structure_tree[structure_tree.index == structure_ids[border]]['acronym'].iloc[0]
            except IndexError:
                name = 'none'
            
            numbers = re.findall(r'\d+', name)
            
            if len(numbers) > 0 and name[:2] != 'CA':
                name = '/'.join(numbers)
                
            name = name.split('-')[0]
                
            self.buttons[i].setText(name)
            self.buttons[i].setObjectName(str(border))
            self.buttons[i].move(OFFSET_MAP[self.probe], border_locs[border] + 3)
            
        self.parent.show()
        
    def buttonClicked(self, button):
        
        self.parent.selectBoundary(self.probe, button.objectName())
        

class App(QWidget):
 
    def __init__(self):
        super().__init__()
        self.title = 'OPT Annotation'
        self.left = 300
        self.top = 100
        self.width = 1600
        self.height = 800
        self.initUI()
     
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        grid = QGridLayout()
        
        self.probes = ('probeA', 'probeB', 'probeC', 'probeD', 'probeE', 'probeF')
        
        self.probe_images = [QLabel(i) for i in self.probes]
        
        im8 = Image.fromarray(np.ones((800,100),dtype='uint8')*230)
        imQt = QImage(ImageQt.ImageQt(im8))
        imQt.convertToFormat(QImage.Format_ARGB32)

        for i, image in enumerate(self.probe_images):
            image.setObjectName(self.probes[i])
            image.mousePressEvent = partial(self.clickedOnImage, image)
            image.setPixmap(QPixmap.fromImage(imQt))
            grid.addWidget(image,0,i*2)
            
        self.boundary_buttons = [BoundaryButtons(i,self) for i in self.probes]
        
        subgrid = QGridLayout()

        save_button = QPushButton('Save', self)
        save_button.setToolTip('Save values as CSV')
        save_button.clicked.connect(self.saveData)

        load_button = QPushButton('Load', self)
        load_button.setToolTip('Load volume data')
        load_button.clicked.connect(self.loadData)

        subgrid.addWidget(save_button,2,2)
        subgrid.addWidget(load_button,2,3)

        grid.addLayout(subgrid,0,13)

        self.current_directory = '/mnt/md0/data/opt/production'

        self.data_loaded = False

        self.selected_probe = None

        self.setLayout(grid)
        
        for buttons in self.boundary_buttons:
            buttons.createButtons()
            
        self.selected_probe = None
        self.selected_boundary = -1
            
        self.show()
        
    def keyPressEvent(self, e):
        
        if e.key() == Qt.Key_Backspace:
            self.deleteAnchorPoint()

    def clickedOnImage(self , image, event):

        x = event.pos().x()
        y = event.pos().y()

        if x < 100 and image.objectName() == self.selected_probe:
            
            self.anchor_points[self.selected_boundary, INDEX_MAP[self.selected_probe]] = int(y / 2)
            #print(y)

        self.refreshImage(self.selected_probe)

    def deleteAnchorPoint(self):
        
        self.anchor_points[self.selected_boundary, INDEX_MAP[self.selected_probe]] = -1
        self.refreshImage(self.selected_probe)

    def refreshImage(self, probe_to_refresh = None):

        if self.data_loaded:
            
            for i, probe in enumerate(self.probes):
                
                if (probe == probe_to_refresh or probe_to_refresh == None):
                    
                    structure_ids = self.df[self.df['probe'] == probe]['structure_id'].values
                    
                    if len(structure_ids) > 0:
                
                        scale_factor = 6.0
    
                        anchor_inds = np.where(self.anchor_points[:,i] > -1)[0]
                        anchor_locs = self.anchor_points[anchor_inds,i]
                        
                        border_locs = np.arange(self.anchor_points.shape[0])
                        
                        for ii, ind in enumerate(anchor_inds):
                            if ii == 0:
                                border_locs = border_locs - border_locs[ind] + anchor_locs[ii]
                            else:
                                scaling = (anchor_locs[ii] - anchor_locs[ii-1]) / (anchor_inds[ii] - anchor_inds[ii-1])
     
                                border_locs[anchor_inds[ii-1]:anchor_inds[ii]] = \
                                    (border_locs[anchor_inds[ii-1]:anchor_inds[ii]] - border_locs[anchor_inds[ii-1]]) * scaling + \
                                    border_locs[anchor_inds[ii-1]]
                                border_locs[anchor_inds[ii]:] = border_locs[anchor_inds[ii]:] - border_locs[anchor_inds[ii]] + anchor_locs[ii]
                                   
                                
                        imQt = self.images[i].copy()
                        
                        #print(imQt.height())
                        
                        if imQt.height() == 2400:
                            
                            self.boundary_buttons[i].updateBoundaries(structure_ids, border_locs*2)
                            channels = 384 - (border_locs * scale_factor / 2400 * 384)
                            
                            self.df.loc[self.df.probe == probe, 'channels'] = channels
                            
                            border_locs = border_locs*scale_factor 
   
                            borders = findBorders(structure_ids)
        
                            for j, border in enumerate(borders):
                                
                                y = int(border_locs[border]) #+ 5
                                
                                if probe == self.selected_probe and border == self.selected_boundary:
                                    color = QColor(20,200,60)
                                    d = 6
                                else:
                                    if border in anchor_inds:
                                        color = QColor(20,200,60)
                                    else:
                                        color = QColor(10,10,10)
                                    d = 3
                
                                if y < (2400 - d) and y > 0:
                                    for x in range(0,300):
                                        for dy in range(0,d):
                                            imQt.setPixelColor(x,y+dy,color)
                                        
                            self.probe_images[i].setPixmap(QPixmap.fromImage(imQt).scaledToWidth(100).scaledToHeight(800))
            
    def selectBoundary(self, probe, border_index):
        
        self.selected_probe = probe
        self.selected_boundary = int(border_index)
        
        self.refreshImage(probe)

    def loadData(self):
        
        fname, filt = QFileDialog.getOpenFileName(self, 
            caption='Select ccf coordinates file', 
            directory=self.current_directory,
            filter='*.csv')

        print(fname)

        self.current_directory = os.path.dirname(fname)
        self.output_file = os.path.join(self.current_directory, 'final_ccf_coordinates.csv')
        self.anchor_points_file = os.path.join(self.current_directory, 'coordinate_anchor_points.npy')

        if fname.split('.')[-1] == 'csv':

            self.setWindowTitle(os.path.dirname(fname))
            self.df = pd.read_csv(fname)
            self.df['channels'] = 0
            
            self.images = [QImage(self.current_directory + '/images/physiology_' + i + '.png') for i in self.probes]
            
            self.anchor_points = np.zeros((572,6)) - 1
            
            self.data_loaded = True
            self.refreshImage()
            
    def saveData(self):
        
        if self.data_loaded:
            self.df.to_csv(self.output_file)
            np.save(self.anchor_points_file, self.anchor_points)
            print('Saved data to ' + self.output_file)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

