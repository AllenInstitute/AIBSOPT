# -*- coding: utf-8 -*-
"""
Created on Fri Sep 07 17:48:41 2018

@author: ScanningLabAnalysis
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jun 07 15:46:51 2018

@author: rustyn
"""

import tifffile
import os
import numpy as np
#import skimage.filters as filt


def genBkgdImg(bkgdImage):

    with tifffile.TiffFile(bkgdImage) as tif:
        bkgd = tif.asarray().astype('float')
        # Convert to float for division and scale
        bkgd = (bkgd - np.amin(bkgd))/(np.amax(bkgd) - np.amin(bkgd))
            
    return bkgd

def stackToOPTPlanes(inputFile, outputFolder, doBackground = False, bkgdDict = {}, includeDownsample = False):
    
    with tifffile.TiffFile(inputFile) as tif:
        for k in range(len(tif.pages)):
            saveName = 'imgRot_' + format(int(k), '04d') + '.tif'
            
            img = tif.pages[k].asarray()
            
            if doBackground:
                
                if str.find(inputFile, 'fluor'):
                    bkgd = bkgdDict['fluor']
                else:
                    bkgd = bkgdDict['trans']
                
                startType = img.dtype
                # Assuming always an integer datatype
                maxForType = np.iinfo(startType).max
                
                # Frame flattening
                
                subImg = img - bkgd.T
                img = (maxForType*((subImg - np.amin(subImg))/(np.amax(subImg) - np.amin(subImg)))).astype(startType)
            
            
            imgToSave = img[:, range(0, img.shape[1], 4)]
            imgToSave = imgToSave[range(0, img.shape[0], 4), :]
            
            if not os.path.isdir(os.path.split(outputFolder)[0]):
                os.mkdir(os.path.split(outputFolder)[0])
            
            if not os.path.isdir(outputFolder):
                os.mkdir(outputFolder)
            
            if not os.path.isdir(os.path.join(outputFolder, 'native')):
                os.mkdir(os.path.join(outputFolder, 'native'))
                
            if not os.path.isdir(os.path.join(outputFolder, 'native', 'recon')):
                os.mkdir(os.path.join(outputFolder, 'native', 'recon'))
            
            tifffile.imsave(os.path.join(outputFolder, 'native', saveName), img.T)
            
                
            if includeDownsample:
                if not os.path.isdir(os.path.join(outputFolder, 'downsample')):
                    os.mkdir(os.path.join(outputFolder, 'downsample'))
                    
                if not os.path.isdir(os.path.join(outputFolder, 'downsample', 'recon')):
                    os.mkdir(os.path.join(outputFolder, 'downsample', 'recon'))
                    
                tifffile.imsave(os.path.join(outputFolder, 'downsample', saveName), imgToSave.T)
                
            
            
    return True
            
def copyDummyReconFile(dummyReconLogFile, outputFolder):
            
    if not dummyReconLogFile in os.listdir(os.path.join(outputFolder, 'native')):
        os.system('copy ' + dummyReconLogFile + ' ' +  os.path.join(outputFolder, 'native', 'imgRot_.log'))
        
    return True

def genBkgdFigDict(bkgdFileDict):
    
    bkgdDict = {'trans': genBackgroundFig(bkgdFileDict['trans'], 3),
                'fluor': genBackgroundFig(bkgdFileDict['fluor'], 3)}
    
    return bkgdDict

def genBackgroundFig(backgroundImage, blurSigma):
    
    bkgd = tifffile.TiffFile(backgroundImage).asarray().astype(float)
    
    subImg = filt.gaussian(bkgd.T, sigma = 8)
    
    return subImg

def parseInputFolder(inputFolder):
    
    wk = os.walk(inputFolder)
    dirList = next(wk)[1]
    
    fileList = []
    
    for k in range(len(dirList)):
    
        num = str.split(dirList[k], '.')[0]
        
        if num[0:5].isdigit():
            
            detailList = []
            detailList.append(dirList[k])
            
            # String is numbers only in first 6 characters
            # Taken as mouse ID number and assumed to be valid
        
            detailList.append(num[0:6]) # Add mouse ID to folder constructor list
            
            
            if num.endswith('fluor'):
                # is fluorescent channel
                
                detailList.append('fluor')
                
            else:
                # is transmission channel
                
                detailList.append('trans')
            
            detailList.append('MMStack_Pos-1.ome.tif')  # Append default filename to list
        
        else:
            continue
        
                

        fileList.append(detailList)
        
    return fileList
        
        
def main():
    
    inputFolder = r'F:\dyiOPT\20191014'
    outputFolder = r'D:\Data\diyOPT\20191014'
    
    alignmentOnly = False
    
    dummyReconLogFile = r'C:\Users\ScanningLabAnalysis\Documents\Python\diyOPT\imgRot_.log'
    
    doBackgroundSub = False
    bkgdImages = {'trans': r'G:\diyOPT\20181113\bfFlat\MMStack_Pos0.ome.tif', 
                  'fluor': r'G:\diyOPT\20181113\fluorflat\MMStack_Pos0.ome.tif'}
    
    if doBackgroundSub:
        bkgdDict = genBkgdFigDict(bkgdImages)
    else:
        bkgdDict = {}
        
    fileList = parseInputFolder(inputFolder)
    
    for f in fileList:
        
        inputFile = os.path.join(inputFolder, f[0], f[-1])
        outPath = os.path.join(outputFolder, f[1], f[2])
        
        if os.path.isfile(inputFile):
    
            out1 = stackToOPTPlanes(inputFile, outPath, doBackground = doBackgroundSub, bkgdDict = bkgdDict)
            
            if out1 and not alignmentOnly:
                
                out2 = copyDummyReconFile(dummyReconLogFile, outPath)
                
                if out2:
                    
                    print('Successfully deplaned ' + inputFile)
                 
            else:
                print("Exited stack deleaving for input " + inputFile)
                
        else:
            print('Path ' + os.path.join(inputFolder, f[0]) + ' does not contain valid stack file.')

if __name__ == "__main__":
    main()
        
