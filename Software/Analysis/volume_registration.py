import vtk

import numpy as np
import pandas as pd

def loadVolume(fname, _dtype='u1', num_slices=1023):
        
    dtype = np.dtype(_dtype)

    volume = np.fromfile(fname, dtype) # read it in
    
    print(volume[:13])
    
    z_size = np.sum([volume[1], volume[2] << pow(2,3)])
    x_size = np.sum([(val << pow(2,i+1)) for i, val in enumerate(volume[8:4:-1])])
    y_size = np.sum([(val << pow(2,i+1)) for i, val in enumerate(volume[12:8:-1])])
    
    fsize = np.array([z_size, x_size, y_size]).astype('int')

    print(fsize)

    volume = np.reshape(volume[13:], fsize) # remove 13-byte header and reshape
    
    return volume

# %%

prefix = '/mnt/md0/data/opt/production/'

mouse = '421529'

scan_type = 'fluor'

fname = prefix + mouse  + '/probe_annotations.npy'
probe_annotations = np.load(fname)

volume = loadVolume(prefix + mouse + '/mouse' + mouse + '_' + scan_type + '.pvl.nc.001')
template = loadVolume('/mnt/md0/data/opt/template_brain/template_fluor.pvl.nc.001')
labels = np.load('/mnt/md0/data/opt/annotation_volume_10um_by_index.npy')

source_landmarks = np.load(prefix + mouse + '/landmark_annotations.npy')
target_landmarks = np.load('/mnt/md0/data/opt/template_brain/landmark_annotations.npy')

source_landmarks = source_landmarks[:,np.array([2,0,1])]
target_landmarks = target_landmarks[:,np.array([2,0,1])]

structure_tree = pd.read_csv('/mnt/md0/data/opt/template_brain/ccf_structure_tree_2017.csv')

output_file = prefix + mouse + '/initial_ccf_coordinates.csv'

# STEP 1: define transform

transform = vtk.vtkThinPlateSplineTransform()

source_points = vtk.vtkPoints()
target_points = vtk.vtkPoints()

for x in [0,1024]:
    for y in [0,1024]:
        for z in [0,1023]:
            source_points.InsertNextPoint([z,x,y])
            target_points.InsertNextPoint([z,x,y])

for i in range(source_landmarks.shape[0]):
    if source_landmarks[i,0] > -1 and target_landmarks[i,0] > -1:
        source_points.InsertNextPoint(source_landmarks[i,:])
    
for i in range(target_landmarks.shape[0]):
    if source_landmarks[i,0] > -1 and target_landmarks[i,0] > -1:
        target_points.InsertNextPoint(target_landmarks[i,:])

transform.SetBasisToR() # for 3D transform
transform.SetSourceLandmarks(source_points)
transform.SetTargetLandmarks(target_points)
transform.Update()
# %%

from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

import matplotlib.pyplot as plt
import numpy as np

from scipy.spatial.distance import euclidean

fig = plt.figure(2)
plt.clf()
ax = fig.add_subplot(111, projection='3d')

ok_points = source_landmarks[:,0] > 0

ax.scatter(source_landmarks[ok_points,0],source_landmarks[ok_points,1],source_landmarks[ok_points,2],s=4,c='tan')

distances = []

for i in np.where(ok_points)[0]:
    distances.append( euclidean(source_landmarks[i,:], target_landmarks[i,:]))
    
    ax.plot3D([source_landmarks[i,0],target_landmarks[i,0]],
             [ source_landmarks[i,1],target_landmarks[i,1]],
               [source_landmarks[i,2],target_landmarks[i,2]]
              ,'-k',alpha=0.35)

plt.axis('square')

# %%

colors = ('red', 'orange', 'brown', 'green', 'blue', 'purple')

probes = ('probeA', 'probeB', 'probeC', 'probeD', 'probeE', 'probeF')


plt.figure(147142)
plt.clf()

plt.figure(147143)
plt.clf()


output_figures = True


origin = np.array([-35, 42, 217],dtype='int')
scaling = np.array([1160/1023,  1140/940, 800/590])

df_columns = ['probe','structure_id', 'A/P','D/V','M/L']

df = pd.DataFrame(columns = df_columns)

fig = plt.figure(147142)
ax1 = fig.add_subplot(111, projection='3d')

for i in range(0,6):
    
    x = probe_annotations[:,0,i]
    y = probe_annotations[:,1,i]
    
    z = np.where(x > -1)[0]

    x = x[x > -1]
    y = y[y > -1]
    
    if len(z) > 0:
    
        data = np.vstack((z,y,x)).T
        datamean = data.mean(axis=0)
        D = data - datamean
        m1 = np.min(D[:,1]) * 2
        m2 = np.max(D[:,1]) * 2
        uu,dd,vv = np.linalg.svd(D)

        linepts = vv[0] * np.mgrid[-200:200:0.7][:,np.newaxis]
        linepts += datamean
        
        if linepts[-1,1] - linepts[0,1] < 0:
            linepts = np.flipud(linepts)
         
        ax1.scatter(y,-x,-z,c=colors[i], s=5, alpha=0.95)
        ax1.plot3D(linepts[:,1],-linepts[:,2],-linepts[:,0],color=colors[i], alpha=0.5)
        
        intensity_values = np.zeros((linepts.shape[0],40))
        structure_ids = np.zeros((linepts.shape[0],))
        ccf_coordinates = np.zeros((linepts.shape[0],3))
        
        for j in range(linepts.shape[0]):
            
            z2,x2,y2 = transform.TransformFloatPoint(linepts[j,np.array([0,2,1])])
            
            ccf_coordinate = (np.array([1023-z2,x2,y2]) - origin) * scaling
            ccf_coordinate = ccf_coordinate[np.array([0,2,1])]
            
            ccf_coordinate_mm = ccf_coordinate * 0.01
            
            ccf_coordinates[j,:] = ccf_coordinate_mm
            
            try:
                structure_ids[j] = int(labels[int(ccf_coordinate[0]),int(ccf_coordinate[1]),int(ccf_coordinate[2])]) - 1
            except IndexError:
                structure_ids[j] = -1
            
            for k in range(-20,20):
                try:
                    intensity_values[j,k+20] = volume[int(linepts[j,0]),int(linepts[j,1]+k),int(linepts[j,2]+k)]
                except IndexError:
                    pass
                
        data = {'probe': [probes[i]]*linepts.shape[0], 
                'structure_id': structure_ids.astype('int'), 
                'A/P' : np.around(ccf_coordinates[:,0],3), 
                'D/V' : np.around(ccf_coordinates[:,1],3), 
                'M/L' : np.around(ccf_coordinates[:,2],3) 
                }

        probe_df = pd.DataFrame(data)
    
        df = pd.concat((df, probe_df) ,ignore_index=True)
        
        plt.figure(147143)
        plt.subplot(1,12,i*2+1)
        plt.imshow(intensity_values, cmap='gray',aspect='auto')
        plt.plot([20,20],[0,j],'-r')
        plt.axis('off')
        
        if output_figures:
            fig = plt.figure(frameon=False)
            fig.set_size_inches(1,8)
            
            ax = plt.Axes(fig, [0., 0., 1., 1.])
            ax.set_axis_off()
            fig.add_axes(ax)
            
            ax.imshow(intensity_values, cmap='gray',aspect='auto')
            fig.savefig('/mnt/md0/data/opt/production/' + mouse + '/images/histology_' + probes[i] + '.png', dpi=300)    
            
            plt.close(fig)
                
        borders = np.where(np.abs(np.diff(structure_ids)) > 0)[0]
        jumps = np.concatenate((np.array([5]),np.diff(borders)))
        borders = borders[jumps > 6]
        
        for border in borders[::1]:
            plt.plot([0,40],[border,border],'-',color='white',alpha=0.5)
            
        plt.subplot(1,12,i*2+2)
        for border in borders[::1]:
            plt.text(0,j-border-1,structure_tree[structure_tree.index == structure_ids[border-1]]['acronym'].iloc[0])
            
        plt.text(0,0,structure_tree[structure_tree.index == structure_ids[-1]]['acronym'].iloc[0])
        plt.ylim([0,j+1])
        plt.axis('off')
        
df.to_csv(output_file)

 