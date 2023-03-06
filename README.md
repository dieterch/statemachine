FSM App

 - Myplant Finite State Machine

# Setup
## Install Miniconda
- download & install https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
- Search for 'miniconda' in Windows Start Menu and open 'Anaconda Prompt (miniconda3)'. 
- pin it to the taskbar

## Install dMyplant4 & statemachine
- Open 'Anaconda Prompt (miniconda3)'

## Update conda to the latest version
- conda update conda

- Create Scripts Folder **mkdir %userprofile%\Documents\Scripts**
- Change to Scripts Folder **cd %userprofile%\Documents\Scripts**

am MAC:
- create a file "statemachine.txt" in your %userprofile%\Documents\Scripts folder by copy & paste:
```
# This file may be used to create an environment using:
# $ conda create --name <env> --file <this file>
# platform: win-64
arrow
bokeh=2.4.3
git
hdf5
ipyfilechooser
ipykernel
ipympl
ipyregulartable
ipython
ipywidgets
jupyterlab
matplotlib
mkl
nodejs
pandas
pyarrow
pytables
python
scipy
tabulate
tqdm
voila
```

- conda create --name FSM -y -k -c conda-forge --file statemachine.txt
- conda activate FSM

## then download the following git's
- git clone https://github.com/DieterChvatal/dmyplant4.git
- git clone https://github.com/DieterChvatal/statemachine.git

- cd statemachine
- jupyter trust App.ipynb
- cd ..
- cd dmyplant4
## install the package in its place ...
- python setup.py develop --uninstall
- python setup.py develop
## you might see several "package missing  errors, just keep installing until this commanf runs through

- open jupyter lab
- ok to Build - then wait some minutes until the message completed is visible - choose reload & restart
- open statemachine/App.ipynb Jupyter Lab
- execute the first cell and enter your myplant credentials
- then click on the "voila" button and select "simple" in the status line
- please be patient at the first search, installed fleet data is downloaded in the background.
- alternatively go to localhost:8888/voila

- create a batchfile "go.bat" in your %USERPROFILE% folder:
```
@echo off
@echo ==============================================
@echo Statemachine (c) Dieter.Chvatal@innio.com 2022
@echo ==============================================
cd "%USERPROFILE%/Documents\Scripts\statemachine"
SETLOCAL
call %USERPROFILE%/miniconda3\condabin\conda.bat activate FSM
jupyter lab
ENDLOCAL
```
## to start statemachine open an anaconda prompt and run "go" 
