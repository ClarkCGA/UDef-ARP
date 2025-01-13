
# Unplanned Deforestation Allocated Risk Modeling and Mapping Procedure (UDef-ARP)

UDef-ARP was developed by Clark Labs, in collaboration with TerraCarbon, to facilitate implementation of the Verra tool, [VT0007 Unplanned Deforestation Allocation (UDef-A)](https://verra.org/wp-content/uploads/2024/02/VT0007-Unplanned-Deforestation-Allocation-v1.0.pdf). It is used in conjunction with a raster-capable GIS for input data preparation and output display. Tools are provided for the development of models using the Calibration Period (CAL) and subsequent testing during the Confirmation Period (CNF). Based on these evaluations, the selected procedure uses the full Historical Reference Period (HRP) to build a model and prediction for the Validity Period (VP). The final output is a map expressed in hectares/pixel/year of expected forest loss.
<p align="center">
  <img src="data/stage.PNG" alt="Fitting and Prediction Phases and Chronology of the Testing and Application Stages, sourced from the VT0007 report">
Fitting and Prediction Phases and Chronology of the Testing and Application
Stages (VT0007)
</p>
UDef-ARP provides the basis for developing a benchmark model as well as tools for comparative testing against alternative empirical models. The benchmark is intentionally simple – it requires only two inputs, distance from the forest edge (non-forest) and a map of administrative divisions that are fully nested within the jurisdiction. Based on these, it uses a relative frequency approach to determine the density of expected deforestation. In testing, this was found to provide a strong benchmark. However, it is intended that users incorporate more sophisticated empirical models, which may be used in UDef-A if they can be shown to be superior to the benchmark for both the fitted model in the Calibration Period and the prediction model in the Confirmation Period. Note that the manner in which alternative models are incorporated and tested is very specifically defined by the UDef-A protocol. UDef-ARP facilitates this testing process.

#### Some important points:
1. At present, UDef-ARP only supports Windows platforms.
2. A Windows installer is available as an alternative to working with the Python code.
3. At present, only limited bulletproofing has been done. Please read the UDef-A document carefully regarding required inputs.
4. UDef-ARP is still under development. Frequent updates are expected.

## Requirements
### Operating System
The UDef-ARP is currently operational exclusively on Windows systems.

### Dependencies
- [Python](https://www.python.org/) 3.9+
- [GDAL](https://github.com/OSGeo/gdal) 3.7.2+
- [PyQt5](https://pypi.org/project/PyQt5/)
- [NumPy](https://github.com/numpy/numpy)
- [pandas](https://github.com/pandas-dev/pandas)
- [GeoPandas](https://github.com/geopandas/geopandas)
- [SciPy](https://github.com/scipy/scipy)
- [Shapely](https://github.com/shapely/shapely)
- [Matplotlib](https://github.com/matplotlib/matplotlib)

### Hardward Requirements
UDef-ARP was created with open source tools. In the current version, all raster inputs are stored in RAM during processing. Therefore, large jurisdictions will require substantial RAM allocations (e.g., 64Gb). The interface was developed in Qt 5. A minimum screen resolution of 1920 x 1080 (HD) is required. A 4K resolution is recommended.

## Conda Environment Setup

### Step 1: Download Anaconda
Download and install the latest version of Anaconda from https://www.anaconda.com/download

### Step 2: Create a Virtual Environment
Open the Anaconda Prompt. Use the YAML file with the following command to create your virtual environment:

```
conda env create -f UDef-ARP_conda_env.yml
```
Activate the environment you just created:
```
conda activate udefarp
```
## Before You Start
### Step 1: Clone or Download the UDef-ARP Folder
Clone the repository or download the folder to your local directory.

### Step 2: Open the GUI
#### 1. Use your Python IDE to Open
Open the UDef-ARP.py file using any Python IDE.

#### 2. Use Anaconda Prompt to Open
After activating your environment, change the directory to the folder directory:
```
cd your_folder_directory
```
Then, open the UDef-ARP.py file:
```
Python UDef-ARP.py
```
### Step 3: Prepare Your Data
UDef-ARP accepts raster map data is either a Geotiff “.tif” or TerrSet “.rst” (binary flat raster ) format. Similarly, outputs can be in either format. **All map data are required to be on an Equal Area Projection**. All map inputs must be co-registered and have the same resolution and the same number of rows and columns.

<p align="center">
  <img src="data/intro_screen.png" alt="GUI Image">
</p>

## COPYRIGHT AND LICENSE
©2023-2024 Clark Labs. This software is free to use and distribute under the terms of the GNU-GLP license.
