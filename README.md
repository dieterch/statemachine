FSM App

 - Myplant Finite State Machine

# Setup
## Install Miniconda

- download & install https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
- Search for 'miniconda' in Windows Start Menu and open 'Anaconda Prompt (miniconda3)'. 
- pin it to the taskbar

## Install dMyplant4 & statemachine 
- download https://github.com/DieterChvatal/dmyplant4/archive/refs/tags/v0.0.4.zip
- download https://github.com/DieterChvatal/statemachine/archive/refs/tags/v0.0.1.zip
- Create Scripts Folder **mkdir %userprofile%\Documents\Scripts**
- Change to Scripts Folder **cd %userprofile%\Documents\Scripts**
- Create a batchfile by **notepad conda-install.bat**
u
copy the following content into this file: 

```
@echo off
echo "Install FSM App via conda"
echo "Dieter Chvatal    05/2022
echo "========================="
unzip
call conda install -k -y -c conda-forge "arrow==1.0.3" pandas matplotlib bokeh scipy IPython jupyterlab ipywidgets ipyfilechooser ipyregulartable voila pyarrow pytables nodejs
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

open Anaconda Prompt and change to %userprofile%\Scripts
execute conda-install.bat
