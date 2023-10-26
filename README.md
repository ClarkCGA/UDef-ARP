
# Unplanned Deforestation Allocated Risk Modeling and Mapping Procedure (UDef-ARP)

UDef-ARP provides a benchmark for the modeling and mapping of deforestation risk. The result is a map of allocated risk that is expressed in units of hectares/pixel. Project proponents are invited to submit alternative maps of allocated risk, if it can be shown that the alternative exceeds the skill of the benchmark for both the model fit during the Calibration Period (CAL) and the model prediction during the Confirmation Period (CNF). Otherwise, the benchmark should be used for the final application. The application stage uses the Historical Reference Period (HRP) for the fit of the model and the Validity Period (VP) for the final prediction. 

Developed by Clark Labs and TerraCarbon for Verra.


## Requirement
- [Python](https://www.python.org/) 3.9+
- [gdel](https://github.com/OSGeo/gdal) 3.7.2+
- [numpy](https://github.com/numpy/numpy) 
- [PyQt5](https://pypi.org/project/PyQt5/#:~:text=PyQt5%20is%20a%20comprehensive%20set,platforms%20including%20iOS%20and%20Android.) 

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
### Step 1: Dowload the UDef-ARP Folder
Download the folder to your local directory.

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