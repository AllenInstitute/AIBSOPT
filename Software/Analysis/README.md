# Software for CCFv3 registration of OPT volumes

This is a space for work-in-progress code for OPT registration.

Additional documentation and a tutorial are coming soon; for now, the code is provided "as-is," without any guarantee of support.

The files are meant to be used in the following order:

1. `preprocessing_app.py` (PyQt app) - use rotation and translation to perform rough alignment of the OPT volume
2. `opt_volume_creator.py` (script) - the alignment parameters from step 1 are used to generate a 3D volume (in Drishti format) from a series of TIFFs
3. `registration_app.py` (PyQt app) - manual selection of key points used for registration
4. `annotation_app.py` (PyQt app) - manual annotation of probe tracks
5. `volume_registration.py` (script) - use the outputs of the registration and annotation apps to extract CCF structure ids along the probe tracks
6. `align_to_physiology.py` (script) - extract physiological markers from the raw Neuropixels data
7. `refinement_app.py` (PyQt app) - adjust the structure boundaries based on physiological landmarks

## Installation (using conda)

A `requirements.txt` file is provided for creating a conda environment to run the scripts and apps

From a terminal inside the `Analysis` directory, run the following commands:

```bash
$ conda env create --file environment.yml
$ conda activate OPT
```

Once inside the conda environment, you can run the apps using, e.g. `python annotation_app.py`

## Using the preprocessing app

This app assumes you have a directory containing data for one reconstructed OPT volume with the following structure:

```
.
+-- fluor
|   +-- native
|       +-- recon
|           +-- imgRot__rec30.tif
|           +-- imgRot__rec31.tif
|           +-- imgRot__rec32.tif
|           +-- ...
|
+-- trans
    +-- native
        +-- recon
            +-- imgRot__rec30.tif
            +-- imgRot__rec31.tif
            +-- imgRot__rec32.tif
            +-- ...
``` 
To launch the app (assuming you've already created a conda environment by following the instructions above), enter the following from the `Analysis` directory:


```bash
$ conda activate OPT
$ python preprocessing_app.py
```

Once the app starts, press the "Load" button to select the directory containing the `fluor` and `trans` folders. This will load a downsampled version of the TIFF files to perform rough alignment.

### Aligning the volume

After the volume is loaded, you can navigate through it using the slider along the bottom of the image. To perform alignment of the coronal view:

1. Use the clockwise/counterclockwise rotation buttons to turn the brain upright
2. Use the arrow buttons to center the brain within the guides
3. Click the "Lock transform" button to apply these transformations to every slice

Once the coronal transform is locked, use the button at the top to switch to the horizontal view. From this view, use the rotation buttons to ensure the anterior/posterior axis is aligned with the guide. Once the axis is aligned, press the "Lock transform" button a second time.

Next, switch to the sagittal view and use the rotation buttons to align the bottom of the brain with the guide. When this step is complete, use the "Lock transform" button to apply the transformation.

Finally, switch back to the coronal view to check whether or not the brain has shifted out of the guides. If so, center it again and press "Lock transform" a final time.

After the brain is aligned along all views, press the "Save" button. This will write a `transforms.json` file to the top-level directory containing the OPT images. This file will be used to build the OPT volume in the next step.

## Using the volume creator script

**IMPORTANT:** Before you run the script, you may want to change the location where the generated volumes are stored. If so, update the value of `output_directory` in the `transforms.json` file written by the pre-processing app. If this is left blank, the volumes will be written to the top-level directory containing the OPT images.

The volume creator is run from the command line using a single argument:

```bash
$ conda activate OPT
$ python opt_volume_creator.py <path_to_transform.json>
```
This will create a directory containing the 1 GB `fluor` and `trans` volumes in [Drishti](https://github.com/nci/drishti) format. These volumes can be loaded directly into the registration and annotation apps for further processing.

**NOTE:** This step may be quite slow, especially if you're loading the images over a network connection.


