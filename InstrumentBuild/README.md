Components and assembly for AIBSOPT

# CAD
	Includes STEP file of instrument assembly with all physical components and instrument rendering.  
	
	.\CAD\toMachine includes individual STEP files and drawings of parts to machine:
		- Extended motor shaft (BearingShaft.step, BearingShaftClamp.step, diyOPTShaftExplode Drawing v0.pdf). Make 1 assembly from aluminum. 
		- Motor mount (Nema17OPTmotorMountv2 v2.step and .pdf). Make 1 from aluminum. 
		- Sample holder puck (sampleHolderPuck.pdf and .step).  Make 1-4 from *magnetic* stainless steel.
		- Specimen chamber (specimenChamberBuildNotes.txt):
			DIY - slideSpecimenChamber drawing v1.pdf
			----OR----
			Purchase Hellma 50 mm large cuvette (Sigma-Aldrich part Z805750), machine OPTCuvetteBase.step, assemble CuvetteStandAssembly.step
			
		
	.\CAD\DriverBoard
		- Files to laser cut mount for optMotorButtonBoard to Imperial optical table.  Cut from acrylic and use standard PCB stand-offs to mount PCB.
		
	.\CAD\laserLaunch
		- Assemblies and build details on adding laser illumination to OPT.  Includes laser combiner + launch w/ speckle reducer and fiber coupling, enclosure, and laser illuminator.
		
	
# PCB Files

	.\EAGLE : Schematic for Arduino motor shield and remote button board for instrument control.
		- optMotorDriver BOM.txt includes parts required for assembly and links to order PCB
		- Can upload .brd files to favorite PCB fab service to order
		- Mount to optical table with .\CAD\DriverBoard part

# Notes on assembly and alignment:

Final resolution of instrument is primarily dependent on alignment of all images in the rotation stack. The rotation axis *MUST* be aligned to camera optical axis, with no roll or pitch.  Yaw is actually well-tolerated.  Roll (camera rotating around optical axis/rotational axis tilted left or right) and pitch (aka nod, rotation axis tilted towards or away from camera) manifest as misalignment in the collected image stack and blur or double-image artifacts in the reconstructions.  

Steps for aligning the roll and pitch axes follow those well-described in https://doi.org/10.1371/journal.pone.0073491.  An object, such as a small ball bearing or tip of a hypodermic needle mounted on the sample holder using glue and/or magnets, provides a good fiducial marker.  This item or a feature on it should be able to be localized in images to sub-pixel precision.  Tracking this feature through the stack should produce a straight line parallel to one axis of the camera.  Any tilt is evidence of roll; elliptical character evidence of pitch.  The .\Software\DataProcessing\assessTestObject.py script is helpful in this step.

Adjustments can be made through small movements of the XY stage and motor.  This assembly should rest equally on all four of the shaft collars on the 1/2" mounting posts.  Typically the screws in the post holders are left open so that the posts freely drop to the proper position.  Shims made from shim stock or a cleaned and dissected soda can make small adjustments to the stage tip or tilt for testing alignment.  If a good position is found, this can be set in place by tightening the post holder screws with the shims in place, removing the shims, then lowering the shaft collars hard against the post holders before tightening the collar screws.  Then when the stage is lifted out and returned, it should return to the same position defined by the shaft collars against the top of the post holders.

Additional care must be taken to have specimen remain within camera field of view while rotating and remain in focus.  Both are straightforward to deal with using the adjusters on the XY stage.  The depth of focus can be increased using the built-in aperture iris on the telecentric lens.  Best to have this be close to the full depth of the specimen without overly darkening the images.  In practice the lost sharpness in the images is negligable compared to the blur induced by mis-alignment.



