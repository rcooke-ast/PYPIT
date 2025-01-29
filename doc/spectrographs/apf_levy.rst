.. highlight:: rest

********
APF Levy
********


Overview
========

This file summarizes the APF high resolution spectrometer,
called the Levy after the donors. The spectrometer
is a cross-dispersed echelle spectrograph with a fixed
position for the all of the dispersive elements.
The only important characteristics from a data 
reduction perspective are the length the slit,
which can be either 3 or 8 arc-seconds, and the
binning used on the the detector which cab be
either 1x1 or 2x2.


Flat Fielding
-------------

For the flat fields, the pipeline selects the iamges 
named as WideFlats. These are the flat fields taken
with the 8 arc-second long and 2 arc-second wide slit.


Slit tracing
------------

Files labeled as narrow flats are only used for the
slit tracing for data taken with the 3 arc-second long
slit.

The WideFlat images should also be used for slit tracing 
for data taken with the 8 arc-second long slit.

**Note**: The WideFlat images will not be automatically
assigned as a Trace images for the 8 arc-second long slit
configuration. 

This must be done manually by the user by editing the
PypeIt file.

Wavelength Calibration
----------------------

The wavelength calibration is done using ThAr lamps, which
are also used to compute the Tilt frames.

Iodine cell observations are not used for the wavelength
calibration. To correctly use the iodine cell requires 
specialized software which is not supported by PypeIt.

Object detection
----------------

The sky subtraction is turned off during the object 
detection step. The pixel sampling is coarse, with 
the pixels having a size of 0.4" in the spatial 
direction. Typical object sizes are a full-width
at half maximum of  4 pixels  in the spectrum while a 3 
arc-second long slit has only 8 pixels in the spatial 
direction.

For faint objects observed with the 8 arc-second long
slit, turning on the sky subtraction in the object 
detection step may be helpful.
