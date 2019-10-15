import numpy as np
from PIL import Image
import glob
import os
import pwd

from scipy.ndimage import gaussian_filter
from skimage.transform import resize
import pandas as pd

# %%

def create_samba_directory(samba_server, samba_share):

    proc_owner_uid = str(pwd.getpwnam(os.environ['USER']).pw_uid)
    share_string = 'smb-share:server={},share={}'.format(samba_server, samba_share)
    data_dir = os.path.join('/', 'var', 'run', 'user', proc_owner_uid, 'gvfs', share_string)

    return data_dir

# %%

def open_image(filename, rotation, x_offset, y_offset, imwidth):
    
    im = Image.open(filename)
            
    imarray = np.array(im.rotate(rotation))
    imarray = imarray[x_offset:x_offset + imwidth, y_offset:y_offset + imwidth]
    
    imarray = resize(imarray, (1024, 1024)) #* 255
    
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

# %%
def loadVolume(fname, _dtype='u1', num_slices=1023):
        
    dtype = np.dtype(_dtype)

    volume = np.fromfile(fname, dtype) # read it in

    z_size = np.sum([volume[1], volume[2] << pow(2,3)])
    x_size = np.sum([(val << pow(2,i+1)) for i, val in enumerate(volume[8:4:-1])])
    y_size = np.sum([(val << pow(2,i+1)) for i, val in enumerate(volume[12:8:-1])])
    
    fsize = np.array([z_size, x_size, y_size]).astype('int')

    volume = np.reshape(volume[13:], fsize) # remove 13-byte header and reshape
    
    return volume

# %%
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
    
    logH = np.log10(h)
    a = np.where(logH > threshold)
    
    peak = b[np.argmax(logH)]

    limit1 = b[np.min(a)]
    limit2 = b[np.max(a)]
        
    return peak, limit1, limit2

# %%



# %%
    
# check registration



info = pd.read_csv('/mnt/md0/data/opt/opt_file_info.csv')

mouse = info['Mouse'].values[120]

print(mouse)

image_types = ('trans', 'fluor')


row = info[info.Mouse == mouse].iloc[0]

plt.figure(1478)

for type_index, image_type in enumerate(image_types):
    
    print(image_type)

    remote_directory = '/mnt/' + row.Location[4:] + '/' + str(mouse)
    
    search_string = os.path.join(remote_directory, image_type, 'native', 'recon', 'imgRot__rec*.' + row.Format)
    
    images = glob.glob(search_string)
    
    images.sort()
    
    if type_index == 0:
        rot = row['Rotation 1']
    else:
        rot = row['Rotation 2']

    imarray = open_image(images[800], rot, row.X, row.Y, row.Width) + 1
    
    plt.imshow(imarray)
    # %%
    
    peak, limit1, limit2 = find_histogram_bounds(imarray)
    
    plt.subplot(2,1,type_index+1)
    plt.imshow(process_image(imarray, limit1, limit2), cmap='gray')
    plt.plot([100,100],[0,1023],color='white')
    plt.plot([924,924],[0,1023],color='white')
    plt.plot([0,1023],[200,200],color='white')
    plt.plot([0,1023],[824,824],color='white')
    
    plt.title(str(mouse) + ' - ' + image_type)
    
    #plt.axis('tight')


# %%
    
# process volumes
    
for mouse in info['Mouse'].values[98:]:
    
    #try:
    
        print(mouse)
        
        row = info[info.Mouse == mouse].iloc[0]
        
        for type_index, image_type in enumerate(image_types):
            
            print(image_type)
        
            remote_directory = '/mnt/' + row.Location[4:] + '/' + str(mouse)
    
            search_string = os.path.join(remote_directory, image_type, 'native', 'recon', 'imgRot__rec*.' + row.Format)
            
            images = glob.glob(search_string)
            
            images.sort()
            
            volume_data = np.zeros((1024, 1024, row.Width), dtype='uint8')
    
            if type_index == 0:
                rot = row['Rotation 1']
            else:
                rot = row['Rotation 2']
    
            imarray = open_image(images[500], rot, row.X, row.Y, row.Width)
            
            peak, limit1, limit2 = find_histogram_bounds(imarray)
            print('  Peak of histogram: ' + str(peak))
            
            print('  Loading images...')
            
            for slice_idx, filename in enumerate(images[:row.Width]):
                
                imarray = open_image(filename, rot, row.X, row.Y, row.Width)
                
                volume_data[:,:,slice_idx] = process_image(imarray, limit1, limit2)
                
            print("   Resizing volume...")
            volume = resize_volume(volume_data)
    
            print("   Transposing volume...")
            volumeT = transpose_volume(volume)
            
            print("   Saving volume...")
            save_volume(volumeT, 'mouse' + str(mouse),'/mnt/md0/data/opt/production/' + str(mouse), image_type)
        
    #except:
    #    print(' Error processing.')

# %%
    
# check rotation
    
from scipy.ndimage import rotate

image_types = ('trans', 'fluor')

info = pd.read_csv('/mnt/md0/data/opt/opt_file_info.csv')

plt.figure(147817)
plt.clf()

mouse_num = 98

for mouse in info['Mouse'].values[mouse_num:mouse_num+1]:
    
    #try:
    
        print(mouse)
        
        row = info[info.Mouse == mouse].iloc[0]
        
        for type_index, image_type in enumerate(image_types):
            
            fname = '/mnt/md0/data/opt/production/' + str(mouse) + '/mouse' + str(mouse) + '_' + image_type + '.pvl.nc.001'
            
            volume = loadVolume(fname)
            
            rotation = 1
            
            
            V = volume[:,600,:]
            Vrot = rotate(V, rotation, reshape=False, cval=254)
            
            plt.subplot(1,2,type_index + 1)
            plt.imshow(Vrot,cmap='gray')
            
            plt.plot([512,512],[0,1024],color='white')
            plt.plot([0,1024],[300,300],color='white')
            
            plt.title(mouse)
            
            # %%
            
# implement rotation
        
from scipy.ndimage import rotate

image_types = ('trans', 'fluor')

info = pd.read_csv('/mnt/md0/data/opt/opt_file_info.csv')

for mouse in info['Mouse'].values[98:]:
    
    try:
    
        print(mouse)
        
        row = info[info.Mouse == mouse].iloc[0]
        
        for type_index, image_type in enumerate(image_types):
            
            print('  ' + image_type)
            
            fname = '/mnt/md0/data/opt/production/' + str(mouse) + '/mouse' + str(mouse) + '_' + image_type + '.pvl.nc.001'
            
            volume = loadVolume(fname)
            
            new_volume = np.zeros((volume.shape),dtype='u1')
            
            rotation = row['Rotation 3']
            
            for i in range(1024):
                new_volume[:,i,:] = rotate(volume[:,i,:], rotation, reshape=False, cval=200)
            
            save_volume(new_volume, 'mouse' + str(mouse),'/mnt/md0/data/opt/production/' + str(mouse), image_type)
            
    except:
        print('Error processing.')
        
# %% 
        
template = loadVolume('/mnt/md0/data/opt/template_brain/template_fluor.pvl.nc.001')
    
    # %%
# check rotation 2
    
from scipy.ndimage import rotate

image_types = ('trans', 'fluor')

info = pd.read_csv('/mnt/md0/data/opt/opt_file_info.csv')

plt.figure(147817)
plt.clf()

mouse_num = 119

plt.subplot(1,2,1)
plt.imshow(template[:,:,600], cmap='gray')

plt.xlim([0,1024])
plt.ylim([0,1024])

plt.plot([110,390],[0,1024],color='white',linewidth=3.0)
plt.plot([750,750],[0,1024],color='white',linewidth=3.0)

for mouse in info['Mouse'].values[mouse_num:mouse_num+1]:
    
    #try:
    
        print(mouse)
        
        row = info[info.Mouse == mouse].iloc[0]
        
        #for type_index, image_type in enumerate(image_types):
            
        fname = '/mnt/md0/data/opt/production/' + str(mouse) + '/mouse' + str(mouse) + '_' + 'trans' + '.pvl.nc.001'
        
        volume = loadVolume(fname)
        
        rotation = 4
        
        
        V = volume[:,:,600]
        Vrot = rotate(V, rotation, reshape=False, cval=200)
        
        plt.subplot(1,2,2)
        plt.imshow(Vrot,cmap='gray')
        
        plt.title(mouse)
        plt.xlim([0,1024])
        plt.ylim([0,1024])
        
        plt.plot([110,390],[0,1024],color='white',linewidth=3.0)
        plt.plot([750,750],[0,1024],color='white',linewidth=3.0)
            
# %%
        
# implement rotation
    
import pandas as pd
        
from scipy.ndimage import rotate

image_types = ('trans', 'fluor')

info = pd.read_csv('/mnt/md0/data/opt/opt_file_info.csv')

for mouse in info['Mouse'].values[98:]:
    
    try:
    
        print(mouse)
        
        row = info[info.Mouse == mouse].iloc[0]
        
        for type_index, image_type in enumerate(image_types):
            
            print('  ' + image_type)
            
            fname = '/mnt/md0/data/opt/production/' + str(mouse) + '/mouse' + str(mouse) + '_' + image_type + '.pvl.nc.001'
            
            volume = loadVolume(fname)
            
            new_volume = np.zeros((volume.shape),dtype='u1')
            
            rotation = row['Rotation 4']
            
            for i in range(1024):
                new_volume[:,:,i] = rotate(volume[:,:,i], rotation, reshape=False, cval=200)
            
            save_volume(new_volume, 'mouse' + str(mouse),'/mnt/md0/data/opt/production/' + str(mouse), image_type)
            
    #        stop
            
    except:
         print('Error processing.')