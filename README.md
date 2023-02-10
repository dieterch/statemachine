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
- run conda update conda

- Create Scripts Folder **mkdir %userprofile%\Documents\Scripts**
- Change to Scripts Folder **cd %userprofile%\Documents\Scripts**

- create a file "statemachine.txt" in your %userprofile%\Documents\Scripts folder by copy & paste:
```
# This file may be used to create an environment using:
# $ conda create --name <env> --file <this file>
# platform: win-64
anyio=3.6.2=pyhd8ed1ab_0
argon2-cffi=21.3.0=pyhd8ed1ab_0
argon2-cffi-bindings=21.2.0=py310he2412df_2
arrow=1.2.3=pyhd8ed1ab_0
arrow-cpp=8.0.0=py310h38b8b19_0
asttokens=2.2.1=pyhd8ed1ab_0
attrs=22.2.0=pyh71513ae_0
aws-c-common=0.4.57=ha925a31_1
aws-c-event-stream=0.1.6=hd77b12b_5
aws-checksums=0.1.9=ha925a31_0
aws-sdk-cpp=1.8.185=hd77b12b_0
babel=2.11.0=pyhd8ed1ab_0
backcall=0.2.0=pyh9f0ad1d_0
backports=1.0=pyhd8ed1ab_3
backports.functools_lru_cache=1.6.4=pyhd8ed1ab_0
beautifulsoup4=4.11.2=pyha770c72_0
blas=1.0=mkl
bleach=6.0.0=pyhd8ed1ab_0
blosc=1.21.3=h6c2663c_0
bokeh=2.4.3=pyhd8ed1ab_3
boost-cpp=1.78.0=h5b4e17d_0
bottleneck=1.3.5=py310h9128911_0
brotli=1.0.9=h8ffe710_7
brotli-bin=1.0.9=h8ffe710_7
brotlipy=0.7.0=py310he2412df_1004
bzip2=1.0.8=he774522_0
c-ares=1.18.1=h8ffe710_0
ca-certificates=2022.12.7=h5b45459_0
certifi=2022.12.7=pyhd8ed1ab_0
cffi=1.15.1=py310hcbf9ad4_0
charset-normalizer=2.1.1=pyhd8ed1ab_0
colorama=0.4.6=pyhd8ed1ab_0
cryptography=37.0.4=py310ha857299_0
cycler=0.11.0=pyhd8ed1ab_0
debugpy=1.5.1=py310hd77b12b_0
decorator=5.1.1=pyhd8ed1ab_0
defusedxml=0.7.1=pyhd8ed1ab_0
entrypoints=0.4=pyhd8ed1ab_0
executing=1.2.0=pyhd8ed1ab_0
flit-core=3.8.0=pyhd8ed1ab_0
fonttools=4.25.0=pyhd3eb1b0_0
freetype=2.10.4=h546665d_1
gflags=2.2.2=ha925a31_1004
git=2.39.1=h57928b3_0
glog=0.6.0=h4797de2_0
hdf5=1.10.6=nompi_h5268f04_1114
icu=64.2=he025d50_1
idna=3.4=pyhd8ed1ab_0
importlib-metadata=6.0.0=pyha770c72_0
importlib_metadata=6.0.0=hd8ed1ab_0
importlib_resources=5.10.2=pyhd8ed1ab_0
intel-openmp=2023.0.0=h57928b3_25922
ipyfilechooser=0.6.0=pyhd8ed1ab_0
ipykernel=6.15.0=pyh025b116_0
ipympl=0.9.2=pyhd8ed1ab_0
ipyregulartable=0.2.1=pyhd8ed1ab_0
ipython=8.9.0=pyh08f2357_0
ipython_genutils=0.2.0=py_1
ipywidgets=8.0.4=pyhd8ed1ab_0
jedi=0.18.2=pyhd8ed1ab_0
jinja2=3.1.2=pyhd8ed1ab_1
jpeg=9e=h8ffe710_2
json5=0.9.5=pyh9f0ad1d_0
jsonschema=4.17.3=pyhd8ed1ab_0
jupyter_client=7.4.1=pyhd8ed1ab_0
jupyter_core=5.2.0=py310h5588dad_0
jupyter_server=1.23.5=pyhd8ed1ab_0
jupyterlab=3.5.3=pyhd8ed1ab_0
jupyterlab_pygments=0.2.2=pyhd8ed1ab_0
jupyterlab_server=2.19.0=pyhd8ed1ab_0
jupyterlab_widgets=3.0.5=pyhd8ed1ab_0
kiwisolver=1.4.4=py310h476a331_0
libblas=3.9.0=12_win64_mkl
libbrotlicommon=1.0.9=h8ffe710_7
libbrotlidec=1.0.9=h8ffe710_7
libbrotlienc=1.0.9=h8ffe710_7
libcblas=3.9.0=12_win64_mkl
libcurl=7.87.0=h86230a5_0
libffi=3.4.2=hd77b12b_6
liblapack=3.9.0=12_win64_mkl
libpng=1.6.37=h2a8f88b_0
libprotobuf=3.20.3=h23ce68f_0
libsodium=1.0.18=h8d14728_1
libssh2=1.10.0=h680486a_2
libthrift=0.15.0=h636ae23_0
libtiff=4.0.9=h36446d0_1002
libwebp=1.2.4=h8ffe710_0
libwebp-base=1.2.4=h8ffe710_0
lz4-c=1.9.4=hcfcfb64_0
lzo=2.10=he774522_1000
m2w64-gcc-libgfortran=5.3.0=6
m2w64-gcc-libs=5.3.0=7
m2w64-gcc-libs-core=5.3.0=7
m2w64-gmp=6.1.0=2
m2w64-libwinpthread-git=5.0.0.4634.697f757=2
markupsafe=2.1.1=py310h2bbff1b_0
matplotlib=3.5.3=py310h5588dad_2
matplotlib-base=3.5.3=py310h79a7439_0
matplotlib-inline=0.1.6=pyhd8ed1ab_0
mistune=2.0.5=pyhd8ed1ab_0
mkl=2021.4.0=h0e2418a_729
mkl-service=2.4.0=py310hcf6e17e_0
mock=5.0.1=pyhd8ed1ab_0
msys2-conda-epoch=20160418=1
munkres=1.1.4=pyh9f0ad1d_0
nbclassic=0.5.1=pyhd8ed1ab_0
nbclient=0.7.2=pyhd8ed1ab_0
nbconvert=7.2.9=pyhd8ed1ab_0
nbconvert-core=7.2.9=pyhd8ed1ab_0
nbconvert-pandoc=7.2.9=pyhd8ed1ab_0
nbformat=5.7.3=pyhd8ed1ab_0
nest-asyncio=1.5.6=pyhd8ed1ab_0
nodejs=18.12.1=h57928b3_0
notebook=6.5.2=pyha770c72_1
notebook-shim=0.2.2=pyhd8ed1ab_0
numexpr=2.8.4=py310hd213c9f_0
numpy=1.22.3=py310hed7ac4c_2
openssl=1.1.1t=hcfcfb64_0
packaging=23.0=pyhd8ed1ab_0
pandas=1.5.2=py310h4ed8f06_0
pandoc=2.19.2=h57928b3_1
pandocfilters=1.5.0=pyhd8ed1ab_0
parso=0.8.3=pyhd8ed1ab_0
pickleshare=0.7.5=py_1003
pillow=9.3.0=py310hdc2b20a_1
pip=22.3.1=py310haa95532_0
pkgutil-resolve-name=1.3.10=pyhd8ed1ab_0
platformdirs=3.0.0=pyhd8ed1ab_0
prometheus_client=0.16.0=pyhd8ed1ab_0
prompt-toolkit=3.0.36=pyha770c72_0
psutil=5.9.0=py310h2bbff1b_0
pure_eval=0.2.2=pyhd8ed1ab_0
pyarrow=8.0.0=py310h26aae1b_0
pycparser=2.21=pyhd8ed1ab_0
pygments=2.14.0=pyhd8ed1ab_0
pyopenssl=22.0.0=pyhd8ed1ab_1
pyparsing=3.0.9=pyhd8ed1ab_0
pyqt=5.9.2=py310hd77b12b_6
pyrsistent=0.18.0=py310h2bbff1b_0
pysocks=1.7.1=pyh0701188_6
pytables=3.7.0=py310h388bc9b_1
python=3.10.9=h966fe2a_0
python-dateutil=2.8.2=pyhd8ed1ab_0
python-fastjsonschema=2.16.2=pyhd8ed1ab_0
python_abi=3.10=2_cp310
pytz=2022.7.1=pyhd8ed1ab_0
pywin32=305=py310h2bbff1b_0
pywinpty=2.0.2=py310h5da7b33_0
pyyaml=6.0=py310he2412df_4
pyzmq=23.2.0=py310hd77b12b_0
qt=5.9.7=h506e8af_3
re2=2022.04.01=h0e60522_0
requests=2.28.2=pyhd8ed1ab_0
scipy=1.8.1=py310h7c00807_2
send2trash=1.8.0=pyhd8ed1ab_0
setuptools=65.6.3=py310haa95532_0
sip=4.19.13=py310hd77b12b_0
six=1.16.0=pyh6c4a22f_0
snappy=1.1.9=hfb803bf_2
sniffio=1.3.0=pyhd8ed1ab_0
soupsieve=2.3.2.post1=pyhd8ed1ab_0
sqlite=3.40.1=h2bbff1b_0
stack_data=0.6.2=pyhd8ed1ab_0
tbb=2021.6.0=h59b6b97_1
terminado=0.15.0=py310h5588dad_0
tinycss2=1.2.1=pyhd8ed1ab_0
tk=8.6.12=h2bbff1b_0
tomli=2.0.1=pyhd8ed1ab_0
tornado=6.2=py310he2412df_0
tqdm=4.64.1=pyhd8ed1ab_0
traitlets=5.9.0=pyhd8ed1ab_0
typing-extensions=4.4.0=hd8ed1ab_0
typing_extensions=4.4.0=pyha770c72_0
tzdata=2022g=h04d1e81_0
ucrt=10.0.22621.0=h57928b3_0
urllib3=1.26.14=pyhd8ed1ab_0
utf8proc=2.6.1=h2bbff1b_0
vc=14.2=h21ff451_1
voila=0.4.0=pyhd8ed1ab_0
vs2015_runtime=14.34.31931=h4c5c07a_10
wcwidth=0.2.6=pyhd8ed1ab_0
webencodings=0.5.1=py_1
websocket-client=1.5.1=pyhd8ed1ab_0
websockets=10.4=py310h8d17308_1
wheel=0.37.1=pyhd3eb1b0_0
widgetsnbextension=4.0.5=pyhd8ed1ab_0
win_inet_pton=1.1.0=pyhd8ed1ab_6
wincertstore=0.2=py310haa95532_2
winpty=0.4.3=4
xz=5.2.10=h8cc25b3_1
yaml=0.2.5=h8ffe710_2
zeromq=4.3.4=h0e60522_1
zipp=3.13.0=pyhd8ed1ab_0
zlib=1.2.13=h8cc25b3_0
zstd=1.5.2=h19a0ad4_0
```
- conda create --name FSM -y -k -c conda-forge --file statemachine.txt
- conda activate FSM

## then download the following git's
git clone https://github.com/DieterChvatal/dmyplant4.git
git clone https://github.com/DieterChvatal/statemachine.git

cd statemachine
jupyter trust App.ipynb
cd ..
cd dmyplant4
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
