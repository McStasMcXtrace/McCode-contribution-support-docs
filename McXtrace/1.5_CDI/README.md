# An example of using McXtrace for ray tracing CDI

<code>ManMandrill_CDI.instr</code> constitutes an example of using McXtrace to simulate Coherent
Diffraction Imaging. A completely coherent beam is allowed to impinge on a a Phase/Absorption object.
The objects itself consists of a mathematical plane which absorbs according to the gray scale in an
image of a baboon, wherea the pahse is advanced by the gray scale value of the image "Man with Lute".

Both images may be found in the Masks directory.

Also supplied is a specialized component <code>Complex_Mask</code> which is a variant of the ```Mask``` component. This is where the images get convoluted in the beam.

Please not that to change the number of pixels in the detector, it is at present necessary to change the <code>#define NX 200</code> and <code>#define NY 200</code>-lines in the instrument file, and recompile the instrument.

This methodology should enable you to reproduce the simulations reported by Fevola et.al. in:
http://journals.iucr.org/s/issues/2020/01/00/fv5111/index.html
