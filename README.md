# Volume Rendering

## Goal

#### Ray Casting Implementation

To study the method ```render_slicer``` in the class ```RaycastRendererImplementation```, and use this as a basis to develop a raycaster that supports both Maximum Intensity Projection and compositing ray functions. Functions ```render_mip``` and ```render_compositing``` in the skeleton has to be implemented, and these functions will be called automatically upon pressing the corresponding buttons in the user interface. The coordinate system of the view matrix is explained in the code. Furthermore, the code already has a transfer function editor it can be more easy to specify colors and opacities to be used by the compositing ray function. 

![mip](/img/mip.png)

Above figure shows reference result images for the orange dataset based on the MIP ray function.

![mip](/img/crf.png)

and the compositing ray function using the default settings of the transfer function editor.

In conclusion,

- Implement the following functionalities:
  1. Tri-linear interpolation of samples along the viewing ray.
  2. MIP and compositing ray functions.
- and to demonstrate the MIP and compositing ray functions work as intended using the orange dataset.


