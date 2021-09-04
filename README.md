# Volume Rendering using Ray Casting

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


#### Applying the volume renderer to above implementation to Mouse Brain

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

##### Maximum Intensity Projection Ray Function

Maximum intensity projection (MIP) is a method for 3D image rendering that projects in the visualisation plane, i.e., That pixel of the resulting image in the slicer renderer corresponds to a voxel located in a plane containing the volume data. To implement MIP, cast each ray in a direction that is normal to the plane, through each pixel of the image. The view vector defines the direction. The idea then is to measure the ray for each pixel, equally on both sides of the plane, using multiples of this vector and the maximum voxel value is captured. So, for a pixel p, the MIP function first computes the maximum scalar value along the ray r of p, and then maps this value via the chosen transfer function f to the color of pixel p. Using the parameterised ray notation, can be expressed in the MIP ray function as:


![eqi1](https://latex.codecogs.com/gif.latex?I\left(&space;p\right)&space;=f\left(&space;\max&space;_{t\in&space;\left[&space;0,T\right]&space;}s\left(&space;t\right)&space;\right))

![tri](/img/vlr.png)

``` Volume rendering of the orange dataset using MIP as ray function from different angles```

From above the figure it can be observed that the partial waxy skin (the peel) part of the orange with a dotted outer circle. The endocarp part of the Orange is visible with the precise segmentation of the juice sacs. Changing the orientation gives the 3D sides of the Orange. Although it fails to convey depth information, it can be see only what the maximum intensity along a ray is, but not at what position (depth) along the ray that value occurs.



##### Compositing Ray Function

Compositing ray function can be implemented in the same way as MIP, except that it do not take the maximum value from the ray samples. It maps each sample to an RGBA colour value first using a dedicated transfer function. Then calculate the output of pixels by applying the recursive equation to the ray sample array, starting from behind the volume (back to front).

![eqi2](https://latex.codecogs.com/gif.latex?C_{i}=\tau&space;_{i}c_{i}&plus;\left(&space;1-\tau_{i}\right)&space;C_{i-1})

Here, ![eqi3](https://latex.codecogs.com/gif.latex?c_i) refers to the current voxel colour (determined by the transfer function), ![eqi4](https://latex.codecogs.com/gif.latex?\tau_i) to the current opacity value and ![eqi5](https://latex.codecogs.com/gif.latex?c_i) to the current value of the output. For implementing above equation, each colour channel is considered separately using the sample colour of the voxel and transparency from the following relation:

![eqi6](https://latex.codecogs.com/gif.latex?voxel\_color&space;=&space;voxel\_color&space;&plus;&space;sample\_color&space;*&space;sample\_color&space;*&space;comp\_transparancy)

![crorange](/img/crorange.png)

```Volume rendering of the orange dataset using compositing a ray function with the provideddefault transfer function from different angles```

Above figure shows the different angles of Orange for the default transfer function, compared to MIP the visibility inside the endocarp is lost but the texture is much more expressed, the exocarp and mesocarp is vaguely visible.


#### Mouse Brain Implementation and Results

##### Mouse Brain

The data set tracks the level of gene expression for approx 2000 genes in a 3D mouse brain from embryonic stages through adulthood. These expression levels are recorded within annotated 3D regions that change size and shape (and even divide) during development. The following implementations were performed:

- Implements MIP on volumes.
- Renders multiple energy volumes.

##### Rendering Multiple Volume

The figures below are for every annotation, all the energies have been rendered. Every annotation has been visualised from three different angles. The implemented technique enables simultaneous visualisation of all the volumes at once. However, understanding of the resulting image must be vigilant, because colours can be harmonised, to avoid it the average colour is taken when two volumes overlap a voxel. This problem can be solved if only one or a few volumes of energy is the priority.

![mousebrain](/img/mvmousebrain.png)

```Volume rendering of the energy volumes of the mouse brain using compositing as ray function and the transfer function```

Every energy file refers to a sample, which is the RNA sequence crossbred to a tissue specimen, but a probe typically only covers a subset of the entire gene sequence. As a consequence, as seen in below figure, there may be multiple probes, and therefore multiple volumes of energy, for a single gene at a specific annotation. Transthyretin gene in annotation 5 is one of the example from the given sample.

![mousebrain](/img/testmvmousebrain.png)

```Transthyretin gene in the mouse brain(100051791 - magenta, 100055110 - green, 100051792 - cyan```



#### Conclusion


The repo have utilised some rendering techniques for the given goal. While implementation it was realised that various strategies need to be chosen according to the problem at hand, and a lot of testing is needed, as well as an understanding of the data which is being used, is required. The biggest difficulties were the lack of computational resources which can be overcome by using a more resource-efficient programming language (mabe Java) or the efficient framework which is being used for this project.
