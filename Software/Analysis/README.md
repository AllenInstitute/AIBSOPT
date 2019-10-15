# Software for CCFv3 registration of OPT volumes

This is a space for work-in-progress code for OPT registration.

Documentation and a tutorial are coming soon; for now, the code is provided "as-is," without any guarantee of support.

The files are meant to be used in the following order:

1. `opt_volume_creator.py` (script) - takes the reconstructed volume as input and performs a manual rough alignment to the CCF template brain
2. `registration_app.py` (PyQt app) - manual selection of key points used for registration
3. `annotation_app.py` (PyQt app) - manual annotation of probe tracks
4. `volume_registration.py` (script) - use the outputs of the registration and annotation apps to extract CCF structure ids along the probe tracks
5. `align_to_physiology.py` (script) - extract physiological markers from the raw Neuropixels data
6. `refinement_app.py` (PyQt app) - adjust the structure boundaries based on physiological landmarks
