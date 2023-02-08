FSM App

 - Myplant Finite State Machine

# Setup
## Install Miniconda

- download & install https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
- Search for 'miniconda' in Windows Start Menu and open 'Anaconda Prompt (miniconda3)'. 
- pin it to the taskbar

## Install dMyplant4 & statemachine
- Open 'Anaconda Prompt (miniconda3)'
- Create Scripts Folder **mkdir %userprofile%\Documents\Scripts**
- Change to Scripts Folder **cd %userprofile%\Documents\Scripts**
- conda create --name FSM -y
- conda activate FSM
- conda install -k -c conda-forge IPython
.... install the following packages like before
arrow 
tqdm 
pandas 
matplotlib 
bokeh 
scipy 
jupyterlab 
ipywidgets 
ipyfilechooser 
ipyregulartable 
ipympl 
voila 
pyarrow 
pytables 
nodejs 
git

## then download the following git's
git clone https://github.com/DieterChvatal/dmyplant4.git
git clone https://github.com/DieterChvatal/statemachine.git

cd statemachine
jupyter trust App.ipynb
cd ..
cd dmyplant4
REM python setup.py develop --uninstall
python setup.py develop
# you might see several "package missing  errors, just keep installing until this commanf runs through

- create a batchfile "go.bat" in your %USERPROFILE% folder:
```
@echo off
@echo ==============================================
@echo Statemachine (c) Dieter.Chvatal@innio.com 2022
@echo ==============================================
cd "%USERPROFILE%/Documents\Scripts\statemachine"
SETLOCAL
call conda activate FSM
jupyter lab
ENDLOCAL
```
- open jupyter lab
- ok to Build - then wait some minutes until the message completed is visible - choose reload & restart
- open statemachine/App.ipynb Jupyter Lab
- execute the first cell and enter your myplant credentials
- then click on the "voila" button and select "simple" in the status line
- please be patient at the first search, installed fleet data is downloaded in the background.
- alternatively go to localhost:8888/voila

 