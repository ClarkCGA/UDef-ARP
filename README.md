
# Unplanned Deforestation Allocated Risk Modeling and Mapping Procedure (UDef-ARP)

UDef-ARP was developed by Clark Labs, in collaboration with TerraCarbon, to facilitate implementation of Verra’s VT0007 Unplanned Deforestation Allocation Tool (UDef-AT). It is used in conjunction with a raster-capable GIS for input data preparation and output display. Tools are provided for the development of models using the Calibration Period and subsequent testing during the Confirmation Period. Based on these evaluations, the selected procedure uses the full Historical Reference Period to build a model and prediction for the Validity Period. The final output is a map expressed in hectares/pixel/year of expected forest loss.

## Requirement
- [Python](https://www.python.org/) 3.9+
- [gdel](https://github.com/OSGeo/gdal) 3.7.2+

## Conda Environment Set Up

### Step 1: Download Anaconda
Download and install the latest version of Anaconda: https://www.anaconda.com/download

### Step 2: Create a Virtual Environment
Open up Anaconda Prompt. Use the yaml file and this command line to create your own virtual environment.

```
conda env create -f UDef-ARP_conda_env.yml
```
Activate the environment you just created.
```
conda activate udefarp
```
## Before You Start
### Step 1: Clone or Download the UDef-ARP Folder
Clone the repository or download the folder to your local directory.

### Step 2: Open the GUI
#### 1. Use your Python IDE to Open
Use any Python IDE to open UDef-ARP.py file

#### 2. Use Anaconda Prompt to Open
After activating your environment, change the directory to the folder directory.
```
cd your_folder_directory
```
Open UDef-ARP.py file
```
Python UDef-ARP.py
```
### Step 3: Project Your Data
Define or Reproject your data projection to equal area projection.
