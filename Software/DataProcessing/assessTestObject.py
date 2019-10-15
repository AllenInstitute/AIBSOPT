# -*- coding: utf-8 -*-
"""
Created on Thu Aug 08 14:20:57 2019

@author: Rusty Nicovich - Allen Institute for Bran Science
"""

import os
import re
import cv2
import numpy as np
import matplotlib.pyplot as plt
import tifffile
from matplotlib.patches import Ellipse


def optFeatureDetector(img, featureType = 'corner', subPixel = False):
    # Take an image and return centroids for all features detected in image
    
    if featureType == 'corner':
        # binarize
        binImg = (img < ((np.amax(img) - np.amin(img))/2 + np.amin(img))).astype('float32')
            
        # Detect corner
        dst = cv2.cornerHarris(binImg,12,5,0.04)
    
        dst = cv2.dilate(dst,None)
        
        # Scale so background is 0.  Peak is 255.  Any values < bkgd are negative.
        dstScale = 255*((dst - np.median(dst))/(np.amax(dst) - np.median(dst)))
        
#        ret, dstBin = cv2.threshold(dst,(0.1*np.amax(dstScale)),255,0)
        dstBin = 255*np.uint8(dstScale > (0.1*np.amax(dstScale)))
        
        # find centroids
        ret, labels, stats, centroids = cv2.connectedComponentsWithStats(dstBin)
        
        if subPixel:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
            centroids = cv2.cornerSubPix(dstScale,np.float32(centroids),(12,12),(-1,-1),criteria)
        
    return centroids, dstScale

def ellipse(R, xCenter, yCenter, majAxis, minAxis, phi, flattenResult = False):
  
    xx = xCenter + majAxis*np.cos(R)*np.cos(phi) - minAxis*np.sin(R)*np.sin(phi)
    yy = yCenter + majAxis*np.cos(R)*np.sin(phi) + minAxis*np.sin(R)*np.cos(phi)
    
    
    if flattenResult:
        
        return np.ravel(np.array([xx.astype('float'), yy.astype('float')]))
    else:
        return [xx, yy]
    
def fitEllipseCorrected(cont):
# https://stackoverflow.com/questions/39693869/fitting-an-ellipse-to-a-set-of-data-points-in-python
    x=cont[:,0]
    y=cont[:,1]

    x=x[:,None]
    y=y[:,None]

    D=np.hstack([x*x,x*y,y*y,x,y,np.ones(x.shape)])
    S=np.dot(D.T,D)
    C=np.zeros([6,6])
    C[0,2]=C[2,0]=2
    C[1,1]=-1
    E,V=np.linalg.eig(np.dot(np.linalg.inv(S),C))

#    if method==1:
#        n=numpy.argmax(numpy.abs(E))
#    else:
#        
    n=np.argmax(E)
    a=V[:,n]

    #-------------------Fit ellipse-------------------
    b,c,d,f,g,a=a[1]/2., a[2], a[3]/2., a[4]/2., a[5], a[0]
    num=b*b-a*c
    cx=(c*d-b*f)/num
    cy=(a*f-b*d)/num

    angle=0.5*np.arctan(2*b/(a-c))*180/np.pi
    up = 2*(a*f*f+c*d*d+g*b*b-2*b*d*f-a*c*g)
    down1=(b*b-a*c)*( (c-a)*np.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
    down2=(b*b-a*c)*( (a-c)*np.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
    a=np.sqrt(abs(up/down1))
    b=np.sqrt(abs(up/down2))

    #---------------------Get path---------------------
    ell=Ellipse((cx,cy),a*2.,b*2.,angle)
    ell_coord=ell.get_verts()

    params=[cx,cy,a,b,angle]

    return params,ell_coord


def main(imgFolder, imgStep, detectionType, subpixelFitting):
    # Main method of feature detection
    # Takes input folder path, parameters for fitting
    # Returns filtered image enhancing features and localized positions of features

    # Get list of files. Is defined by imgRot_XXXX.tif, where XXXX is position in image series.
    # Is a folder with a list of files
    onlyFiles = [f for f in os.listdir(imgFolder) if os.path.isfile(os.path.join(imgFolder, f)) and re.search('imgRot_\d{4}.tif', f)]
    
    if len(onlyFiles) is 0:
        onlyFiles = [f for f in os.listdir(imgFolder) if os.path.isfile(os.path.join(imgFolder, f)) and re.search('\W+ome.tif', f)]
    
    # Is a single MicroManager ome.tiff file
    if len(onlyFiles) == 1:
        isSeries = False
        numPlanes = len(tifffile.TiffFile(os.path.join(imgFolder, onlyFiles[0])).pages)
    else:
        isSeries = True
        numPlanes = len(onlyFiles)
    
    
    cornerList = np.array([])
    dstAccum = np.array([])
    imgAccum = np.array([])
    #
    angleStep = 2*np.pi/numPlanes
    
    
    for k in range(0, numPlanes, imgStep):
    #for k in range(0, 200, imgStep):
        
        print('Analyzing plane {}'.format(k))
        
        
        
        # Load file
        if isSeries:
            f = onlyFiles[k]
            with tifffile.TiffFile(os.path.join(imgFolder, f)) as tif:
                img = tif.asarray()
        else:
            img = np.rot90(tifffile.imread(os.path.join(imgFolder, onlyFiles[0]), key=k), -1)
            
        if invertImg:
            img = np.flipud(img)
            
    
        centroids, dst = optFeatureDetector(img, subPixel = subpixelFitting, featureType = detectionType)
        
        centroids = np.hstack((centroids, angleStep*k*np.ones((len(centroids), 1))))
        
        
        # Add feature transform image to accumulation image
        if len(dstAccum) == 0:
            dstAccum = np.array(dst)
            imgAccum = np.array(img.astype('float32'))
        else:
            dstAccum = dstAccum + dst
            imgAccum = imgAccum + img.astype('float32')
        
        # Keep feature points corresponding to desired feature
        # Exclude all points with Y values outside of pointRange
        # If pointRange not specified, assume desired feature is lowest point in image (closest to bottom of FOV)
        
        if len(pointRange)  == 2:
            
            # Keep points in this range.
            
            keepPoint = centroids[(centroids[:,1] > np.amin(pointRange)) & (centroids[:,1] < np.amax(pointRange)),:]
            
            
            if len(cornerList) == 0:
                cornerList = np.array(keepPoint)
            else:
                cornerList = np.append(cornerList, keepPoint, axis = 0)
            
            
        elif len(pointRange) == 0:
        
            # Point is the centroid farthest down in the image
    
            if len(cornerList) == 0:
                cornerList = np.array(centroids[centroids[:,1] == np.amax(centroids[:,1]), :])
            else:
                cornerList = np.append(cornerList, centroids[centroids[:,1] == np.amax(centroids[:,1]), :], axis = 0)
                
        else:
            raise('Point range not supported')

    return dstAccum, cornerList

# Print output
def printOutput(ellipseParams, cornerList, suggestCorrections):
    
    center = ellipseParams[0:2]
    axes = ellipseParams[2:4]
    phi = ellipseParams[4]
    
    print('---------------------------------')
    print('Ellipse fitting results:')
    print("Center = {}".format(center)) # this value can be anything.  ideally is close to center of FOV in X
    print("Angle of rotation = {}".format(phi)) # Should be as close to 0 as possible.
    print("Axes lenghts = {}".format(axes)) # First value can be anything, but should be close to half of FOV size.  Second value should be as close to 0 as possible.
     
    # StdDev of all should be between std dev of any pair of parts.
    # If mean value A > mean value B, means A portion is below B portion of rotation
    
    # Next set assumes pin starts on far left (operator looking at sample along optical axis)
    # Pin rotates away from camera at first half of measurement.
    # Front-back measurements. 
    print('---------------------------------')
    print('Front-back measurements:')
    print('StdDev = {}'.format( np.std(cornerList[:,1])))
    print('Std first half = {}'.format( np.std(cornerList[:int(len(cornerList)/2), 1])))
    print('Mean first half = {}'.format( np.mean(cornerList[:int(len(cornerList)/2), 1])))
    print('Std secnd half = {}'.format(np.std(cornerList[int(len(cornerList)/2):, 1])))
    print('Mean secnd half = {}'.format(np.mean(cornerList[int(len(cornerList)/2):, 1])))
    
    # Left-right measurements. 
    print('---------------------------------')
    print('Left-right measurements:')
    print('Std first quad = {}'.format(np.std(cornerList[int(len(cornerList)/8):2*int(len(cornerList)/8), 1])))
    print('Mean first quad = {}'.format( np.mean(cornerList[int(len(cornerList)/8):2*int(len(cornerList)/8), 1])))
    print('Std third quad = {}'.format(np.std(cornerList[5*int(len(cornerList)/8):6*int(len(cornerList)/8), 1])))
    print('Mean third quad = {}'.format(np.mean(cornerList[5*int(len(cornerList)/8):6*int(len(cornerList)/8), 1])))
    print('---------------------------------')
    
    
    if suggestCorrections['output']:
        # Calculate amounts to offset mounting to correct measured position errors
        leftRight = suggestCorrections['stageCorners'][0]*np.tan(phi)
        
        # Projection of circle onto plane yielding ellipse is r cos \theta, where r is radius of circle
        # Assume major axis is radius of circle
        projTheta = (np.pi/2) - np.arccos(axes[1]/axes[0])
        frontBack = suggestCorrections['stageCorners'][1]*np.tan(projTheta)
        
        if suggestCorrections['rotatesTowards'] == 'back':
           print('Raise front {} mm relative to back.'.format(frontBack))
        
        elif suggestCorrections['rotatesTowards'] == 'front':
           print('Raise back {} mm relative to front.'.format(frontBack))
        else:
            print('Variable rotateTowards can have values \'front\' or \'back\'')
            
        if suggestCorrections['specimenStartSide'] == 'left':
            print('Raise left {} mm relative to right.'.format(leftRight))
        elif suggestCorrections['specimenStartSide'] == 'right':
            print('Raise right {} mm relative to left.'.format(leftRight))
        else:
            print('Variable specimenStartSize can have values \'right\' or \'left\'') 
            
        print('---------------------------------')
        
def plotOutput(dstAccum, cornerList, elipFit):
    # Make plots    
    plt.cla()
    plt.imshow(dstAccum)
    plt.plot(cornerList[:,0], cornerList[:,1], 'wx')
    
#    R = np.arange(0,2*np.pi, 0.01)
    #elipFit = ellipse(R, center[0], center[1], axes[0], axes[1], phi)
    
    plt.plot(elipFit[:,0], elipFit[:,1], 'w-')
    plt.show()
    

#%%

if __name__ == "__main__":
    #imgFolder = r'C:\Users\ScanningLabAnalysis\Desktop\New OPT\100000\Trans\native'
    
    # Path to folder with image stack or images
#    imgFolder = r'C:\Users\ScanningLabAnalysis\Desktop\NewOPT\CurrentOPT\000001\trans\native'
    imgFolder = r'F:\dyiOPT\20190909\476974'
    
    invertImg = True # Flip image up-down if on prototype system to match production system 
                     # Typical orientation is object to detect closer to bottom of FOV,
                     # mounting plate at top
    
    pointRange = [1600, 1650] # Retain points only in this y range.  Leave empty to pick 'lowest' point
    
    imgStep = 11 # interval between images to sample. 
    
    detectionType = 'corner' # 'corner' will look for sharp corner, such as point on object
                             # To do : 'bead' for contrasting bead in specimen
    
    subpixelFitting = True
    
    # Parameters for adjustment suggestions
    suggestCorrections = {}
    suggestCorrections['output'] = True # Should suggestions for alignment corrections be made?
    suggestCorrections['stageCorners'] = [124.5, 76.2] # L-R, Back-Front dimensions of mounting positions of stage.  
                                                      # Here for Thorlabs XYT1]
                                                      # In mm
    suggestCorrections['rotatesTowards'] = 'back' # 'back' or 'front'.  From perspective of camera, which way does sample rotate first in image series.
                                                  # If looking from top, objective lens on left, pointing to right, specimen starts at 12 o'clock position and rotates clockwise, this is 'back'
    suggestCorrections['specimenStartSide'] = 'left' # From camera perpsective
    
    #%%
    # Detect features and return filtered image, detected points
    dstAccum, cornerList = main(imgFolder, imgStep, detectionType, subpixelFitting)
    
    #%% Fit point to ellipse 
    
    #center, axes, phi = fitEllipse(cornerList[:,0], cornerList[:,1])
    params, elipFit = fitEllipseCorrected(cornerList[:,0:2])
    printOutput(params, cornerList, suggestCorrections)
    plotOutput(dstAccum, cornerList, elipFit)










