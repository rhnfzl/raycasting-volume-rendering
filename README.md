# Volume Rendering

## Goal

#### Ray Casting Implementation

Study the method ```render_slicer``` in the class ```RaycastRendererImplementation```, and use this as a basis to develop a raycaster that supports both Maximum Intensity Projection and compositing ray functions. We have already provided placeholder functions render_mip and ```render_compositing``` in the skeleton, and these functions will be called automatically upon pressing the corresponding buttons in the user interface. The coordinate system of the view matrix is explained in the code. Furthermore, the code already provides a transfer function editor so you can more easily specify colors and opacities to be used by the compositing ray function. Figure 1 shows reference result images for the orange dataset based on the MIP ray function (Fig. 1(a)) and the compositing ray function using the default settings of the transfer function editor (Fig. 1(b)).


