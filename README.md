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
- Create a batchfile **notepad conda-install.bat**
- copy the following content into this file: 
```
@echo off
echo "Install FSM App via conda"
echo "Dieter Chvatal    05/2022
echo "========================="
SETLOCAL
ENDLOCAL & call conda create --name FSM -y
ENDLOCAL & call conda activate FSM
ENDLOCAL & call conda install --name FSM -k -y tqdm IPython
ENDLOCAL & call conda install -k -y -c conda-forge "arrow==1.0.3" pandas matplotlib bokeh scipy jupyterlab ipywidgets ipyfilechooser ipyregulartable ipympl voila pyarrow pytables nodejs git
git clone https://github.com/DieterChvatal/dmyplant4.git
git clone https://github.com/DieterChvatal/statemachine.git
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
- execute the batchfile **conda-install.bat**
- create a Windows Link and copy the following into "Speicherort":
```
%userprofile%\miniconda3\pythonw.exe %userprofile%\miniconda3\cwp.py %userprofile%\miniconda3\envs\FSM %userprofile%\miniconda3\envs\FSM\pythonw.exe %userprofile%\miniconda3\envs\FSM\Scripts\jupyter-lab-script.py "%USERPROFILE%/Documents\Scripts"
```
- alternatively create a batchfile "go.bat" in your %USERPROFILE% folder:
```
@echo off
@echo ==============================================
@echo Statemachine (c) Dieter.Chvatal@innio.com 2022
@echo ==============================================
cd "%USERPROFILE%/Documents\Scripts\statemachine"
jupyter lab
```
- open jupyter lab
- ok to Build - then wait some minutes until the message completed is visible - choose reload & restart
- open statemachine/App.ipynb Jupyter Lab
- execute the first cell and enter your myplant credentials
- then click on the "voila" button and select "simple" in the status line
- please be patient at the first search, installed fleet data is downloaded in the background.
- alternatively go to localhost:8888/voila

 