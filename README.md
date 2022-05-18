FSM App

 - Myplant Finite State Machine

# Setup
## Install Miniconda

- download & install https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
- Search for 'miniconda' in Windows Start Menu and open 'Anaconda Prompt (miniconda3)'. 
- pin it to the taskbar

## Install dMyplant4 & statemachine
- go to https://github.com/DieterChvatal
- download dmyplant4-master.zip
- download statemachine-master.zip
- Open 'Anaconda Prompt (miniconda3)'
- Create Scripts Folder **mkdir %userprofile%\Documents\Scripts**
- Change to Scripts Folder **cd %userprofile%\Documents\Scripts**
- Create a batchfile **notepad conda-install.bat**
- copy the following content into this file: 
```
@echo off
echo "Install FSM App via conda"
echo "Dieter Chvatal    05/2022
echo "========================="
call conda install -k -y -c conda-forge "arrow==1.0.3" pandas matplotlib bokeh scipy IPython jupyterlab ipywidgets ipyfilechooser ipyregulartable ipympl voila pyarrow pytables nodejs git
call python -m unzip.py
cd statemachine
jupyter trust App.ipynb
cd ..
cd dmyplant4
REM python setup.py develop --uninstall
python setup.py develop
cd ..
echo "======================"
echo "installation completed"
```
- Create a python file **notepad unzip.py**
copy the following content into this file
```
import zipfile, os

with zipfile.ZipFile(os.path.expandvars("%userprofile%") + "\\Downloads\\dmyplant4-master.zip", 'r') as zip_ref:
    zip_ref.extractall(os.path.expandvars("%userprofile%") + "\\Documents\\Scripts")
os.rename(os.path.expandvars("%userprofile%") + "\\Documents\\Scripts\\dmyplant4-master", os.path.expandvars("%userprofile%") + "\\Documents\\Scripts\\dmyplant4")

with zipfile.ZipFile(os.path.expandvars("%userprofile%") + "\\Downloads\\statemachine-master.zip", 'r') as zip_ref:
    zip_ref.extractall(os.path.expandvars("%userprofile%") + "\\Documents\\Scripts")
os.rename(os.path.expandvars("%userprofile%") + "\\Documents\\Scripts\\statemachine-master", os.path.expandvars("%userprofile%") + "\\Documents\\Scripts\statemachine")
```
- execute the batchfile **conda-install.bat**
- create a Windows Link and copy the following into "Speicherort":
```
%userprofile%\miniconda3\python.exe %userprofile%\miniconda3\cwp.py %userprofile%\miniconda3 %userprofile%\miniconda3\python.exe %userprofile%\miniconda3\Scripts\jupyter-lab-script.py "%USERPROFILE%/"
```

Double Click on the Link and enjoy :-)

