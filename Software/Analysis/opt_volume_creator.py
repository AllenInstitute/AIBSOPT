import numpy as np
from PIL import Image
import glob
import os

from scipy.ndimage import gaussian_filter
from skimage.transform import resize
import pandas as pd
import glob
from scipy.ndimage import rotate

import sys, getopt

def open_image(filename, rotation, offset1, offset2, imwidth):
    
    imarray = np.array(Image.open(filename))
    
    imarray = rotate(imarray, rotation, reshape=False, cval=200)
    
    xoffset = 300 - offset1
    yoffset = 300 - offset2
    imarray = imarray[xoffset:xoffset + imwidth, yoffset:yoffset + imwidth]
    
    imarray = resize(imarray, (1024, 1024)) * pow(2,8)
    
    return imarray

def process_image(imarray, limit1, limit2):
    
    distance = limit2 - limit1

    imarray[imarray < limit1] = limit1 # lower bound
    imarray[imarray > limit2] = limit2 # upper bound
    imarray = imarray - (limit1) # set min to 0
    imarray = imarray / (distance) # normalize between zero and one
    imarray = 1 - imarray # invert
    imarray = imarray * 255 # scale to 8-bit
    imarray = gaussian_filter(imarray,2) # smooth
    imarray = imarray.astype('uint8') # convert to unsigned int
    
    return imarray

def resize_volume(volume):

    volume2 = np.zeros((1024,1024,1023), dtype='uint8')
    
    for horzslice in range(1024):
        
        imslice = volume[horzslice,:,:]
        imslice = resize(imslice, (1024, 1024))
        imslice = imslice*255
        imslice = imslice.astype('uint8')

        volume2[horzslice,:,:] = imslice[:,:1023]
        
    return volume2
    
def create_header():

    Z = [3, 0, 0]
    X = [0, 4, 0, 0]
    Y = [0, 4, 0, 0]
    
    header = [0, 255]
    header.extend(Z)
    header.extend(X)
    header.extend(Y)
    
    header = np.array(header).astype('uint8')

    return header


def transpose_volume(volume):    

    V = np.transpose(volume[:,:,:])
    
    for i in range(0, V.shape[0]):
        V[i,:,:] = V[i,:,:].T
        
    return V
    
    
def add_header(volume):
    
    volume_flat = volume.flatten()    
    full_dataset = np.concatenate((create_header(), volume_flat))
    
    return full_dataset


def loadVolume(fname, _dtype='u1', num_slices=1023):
        
    dtype = np.dtype(_dtype)

    volume = np.fromfile(fname, dtype) # read it in

    z_size = np.sum([volume[1], volume[2] << pow(2,3)])
    x_size = np.sum([(val << pow(2,i+1)) for i, val in enumerate(volume[8:4:-1])])
    y_size = np.sum([(val << pow(2,i+1)) for i, val in enumerate(volume[12:8:-1])])
    
    fsize = np.array([z_size, x_size, y_size]).astype('int')

    volume = np.reshape(volume[13:], fsize) # remove 13-byte header and reshape
    
    return volume


def save_volume(volume, mouse, data_directory, image_type):
    
    flattened = add_header(volume)
    
    if not os.path.exists(data_directory):
        os.mkdir(data_directory)
        
    fname = data_directory + '/' + mouse + '_' + image_type + '.pvl.nc'
    
    flattened.tofile(fname + '.001')
    
    nc_file_string = """<!DOCTYPE Drishti_Header>
    <PvlDotNcFileHeader>
      <rawfile></rawfile>
      <voxeltype>unsigned char</voxeltype>
      <pvlvoxeltype>unsigned char</pvlvoxeltype>
      <gridsize>1023 1024 1024</gridsize>
      <voxelunit>micron</voxelunit>
      <voxelsize>10 10 10</voxelsize>
      <description></description>
      <slabsize>1024</slabsize>
      <rawmap>0 255 </rawmap>
      <pvlmap>0 255 </pvlmap>
    </PvlDotNcFileHeader>"""
    
    print(nc_file_string, file=open(fname, 'w+'))
    

def find_histogram_bounds(imarray, threshold = 3.0):
    
    h,b = np.histogram(imarray.flatten(), bins=range(1,255))
    
    print(h)
    
    logH = np.log10(h)
    a = np.where(logH > threshold)
    
    peak = b[np.argmax(logH)]

    limit1 = b[np.min(a)]
    limit2 = b[np.max(a)]
        
    return peak, limit1, limit2

# %%
  


def process_volume(input_directory, 
                   output_directory,
                   mouse,
                   rot1, rot2, rot3, offset1, offset2,
                   imwidth=1488):
    
    print(input_directory)
    print(output_directory)
    image_types = ('fluor', 'trans')

    for type_index, image_type in enumerate(image_types):
        
        print(image_type)

        search_string = os.path.join(input_directory,
                                     image_type,
                                     'native', 
                                     'recon', 'imgRot__rec*.tif')
        
        images = glob.glob(search_string)
        images.sort()
        
        volume_data = np.zeros((1024, 1024, imwidth), dtype='uint8')
        
        print(images[500])

        imarray = open_image(images[500], rot1, offset1, offset2, imwidth)
        
        peak, limit1, limit2 = find_histogram_bounds(imarray)
        print('  Peak of histogram: ' + str(peak))
        
        print('  Loading images...')
        
        for slice_idx, filename in enumerate(images[:imwidth]):
            
            imarray = open_image(filename, rot1, offset1, offset2, imwidth)
            
            volume_data[:,:,slice_idx] = process_image(imarray, limit1, limit2)
            
        print("   Resizing volume...")
        volume = resize_volume(volume_data)

        print("   Transposing volume...")
        volumeT = transpose_volume(volume)
        
        print("   Saving volume...")
        save_volume(volumeT, 'mouse' + str(mouse),
                    os.path.join(output_directory, str(mouse)), image_type)
    

    # implement rotation 2

    for type_index, image_type in enumerate(image_types):
        
        print('  ' + image_type)
        
        print('   Applying second rotation')
        
        fname = os.path.join(output_directory,  str(mouse), 'mouse' + str(mouse) + '_' + image_type + '.pvl.nc.001')
        
        volume = loadVolume(fname)
        
        new_volume = np.zeros((volume.shape),dtype='u1')
        
        for i in range(1024):
            new_volume[:,i,:] = rotate(volume[:,i,:], rot2, reshape=False, cval=200)
        
        save_volume(new_volume, 'mouse' + str(mouse),
                    os.path.join(output_directory, str(mouse)),
                    image_type)
    
    # implement rotation 3

    for type_index, image_type in enumerate(image_types):
        
        print('  ' + image_type)
        
        print('   Applying third rotation')
        
        fname = os.path.join(output_directory,  str(mouse), 'mouse' + str(mouse) + '_' + image_type + '.pvl.nc.001')
        
        volume = loadVolume(fname)
        
        new_volume = np.zeros((volume.shape),dtype='u1')
        
        for i in range(1024):
            new_volume[:,:,i] = rotate(volume[:,:,i], rot3, reshape=False, cval=200)
        
        save_volume(new_volume, 'mouse' + str(mouse),
                    os.path.join(output_directory, str(mouse)),
                    image_type)
        
    print('DONE.')
    
# %%
            

def main(argv):
    
   if len(argv) > 1:
       print('ERROR: Only one input argument allowed (path to transforms.json file)')
   elif len(argv) < 1:
       print('ERROR: Required input argument (path to transforms.json file)')
   else:
       
       import json
       
       dictionary = json.load(open(argv[0]))
       
       if len(dictionary['output_directory']) == 0:
           dictionary['output_directory'] = dictionary['location']
       
       process_volume(dictionary['location'], 
                   dictionary['output_directory'],
                   dictionary['mouse'],
                   dictionary['rot1'],
                   dictionary['rot2'],
                   dictionary['rot3'],
                   dictionary['offset1'],
                   dictionary['offset2'])

if __name__ == "__main__":
   main(sys.argv[1:])    
         
    