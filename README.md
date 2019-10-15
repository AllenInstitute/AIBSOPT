Optical projection tomography microscope for isotropic imaging of intact, cleared mouse brains.  Designed specifically for imaging probe tracks in mouse brains following Neuropixels recordings. 

Instrument described is very low cost (~$6k US), straightforward to assemble out of mostly commercially-available parts, and with little need for maintenance or alignment.

Images acquired by this instrument can be reconstructed using free NRecon software (SkyScan via Bruker) and aligned to Allen Institute for Brain Science Common Coordinate Framework. Detecting probe tracks in these images allows registration of multiple experiments into a common spatial framework for comparing results across experiments. 

Repository contents:
- 412792_fluorSubset.gif - stack of reconstructed images from portion of mouse brain showing multiple Neuropixels tracks
- .\InstrumentBuild : 
    - Parts list
    - .\CAD : CAD design for instrument
    - .\EAGLE : Schematic for motor control shield.
    
- .\Software : 
    - .\InstrumentSoftware :  
      - .\Arduino\diyOPT : Sketch for motor driver board
      - .\MicroManager : Config file and acquisition script for data acquisition
    - .\DataProcessing : 
        - Python code to generate files + folders for NRecon reconstructions
        - Python utilities to aid in alignment using images of a test object on instrument
    - .\Analysis : Code for post-reconstruction volume registration and probe tracing 
- .\Protocols : 
  - Standard operating protocol for sample mounting, instrument operation, and reconstruction with NRecon.
