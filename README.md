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


#### Applying the volume renderer to above implementation

Use the above raycaster implementation and implement it on ```/MouseBrain/``` dataset which is the subset taken from the http://sciviscontest.ieeevis.org/2013/VisContest/index.html.


Produce an insightful visualization of this data. The [paper](http://sciviscontest.ieeevis.org/2013/VisContest/index.html) that describes the dataset provides quite some inspiration. The challenges need to be tackle is:

- Visualize multiple volume data sets of the energy simultaneously.
- Perform volume rendering on the annotation data, which is a labeled volume data set. Each voxel has a label that is the ID of a particular neural structure.
- Combine the rendering of the energy volume data and the annotation volume data.


### Setup

- Install [Python 3.6](https://www.python.org/downloads/release/python-368), Make sure you mark the option “Add Python 3.6 to PATH”. Then click “Install now”.
- Creating a virtual environment : 
  1. Open PyCharm.
  2. If this is the first time you open it, you will see some windows to configure the IDE and open it.
  3. Find the folder with the repo code and open it
  4. Go to File > Settings. In the new window, just type project interpreter
  5. The project will be configured to use the global python interpreter, which need to change. Click over the gear icon that is at the right edge of the window and then “Add...”.
  6. The Virtualenv Environment will be the default option. Make sure that the location matches the path of your repo (plus the folder for the virtual  environment, in this case venv), and that the base interpreter is correctly set to Python 3.6. Just click OK and you will be done. Now the virtual environment will be ready.
- Installing Project Dependencies
  1. Numpy : ```pip install numpy```
  2. PyOpenGL : ```pip install PyOpenGL==3.1.3rc1```
  3. wxPython : ```pip install wxPython```
  4. ITK : ```pip install itk```
- Running the project
  1. Click “Add Configuration...” at the top-right corner of the window in pycharm.
  2. It will pop up another window. Click the “+” button and then select Python.
  3. Now, in Script path click the folder icon and select, within your project, the file gui/Application.py. Fill some name for the configuration and make sure that Python interpreter is the one located in your virtual environment (venv folder).
  4. Click OK and your project is ready to be run by clicking the Play button at the top-right corner


### Implementation

#### Ray Casting Implementation

##### Trilinear Interpolation

Trilinear interpolation is a method of multivariate interpolation on a 3-D regular grid. It approximates the value of a function at an intermediate point (x,y,z) within the local axial rectangular prism linearly, using function data on the lattice points. To find the projection of a voxel, take the trilinear interpolation. From below figure it can be observed that the Direct voxel rendering method has less structural details as compared to the Trilinear method of calculation under slicing, signal indeed gets smoothened as expected.

![tri](/img/tri.png)

```Direct retrieval vs. Trilinear Interpolation. The orange data set has been kept side by side withthe respective orientation for said methods```









