from dataclasses import dataclass
import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
import ipywidgets as widgets
from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from dmyplant2 import cred, MyPlant, Engine, cplotdef, save_json, load_json

cred()
mp = MyPlant(300)

# DEFINITION OF PLOTS & OVERVIEW
def myfigures(e = None):
    def fake_e(dataItem):
        return [dataItem[:-1] + '01']
    func = fake_e if e is None else e.dataItemsCyl
    return {
        'actors' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,5000), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['Ignition_ITPAvg'],'ylim': [-10, 30], 'color':'rgba(255,0,255,0.4)', 'unit':'°KW'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':['Various_Values_PosThrottle','Various_Values_PosTurboBypass'],'ylim': [-10, 110], 'color':['rgba(105,105,105,0.6)','rgba(165,42,42,0.4)'], 'unit':'%'},
        ],
        'tecjet' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,5000), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['bmep'], 'ylim':(-10,40), 'color':'orange', 'unit':'bar'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['Ignition_ITPAvg'],'ylim': [-10, 30], 'color':'olivedrab', 'unit':'°KW'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':['TecJet_GasPress1'],'_ylim': [0, 3], 'color':'rgba(255,0,0,0.4)', 'unit':'mbar'},
        {'col':['TecJet_GasTemp1'],'_ylim': [0, 3], 'color':'rgba(255,0,255,0.4)', 'unit':'°C'},
        {'col':['TecJet_GasDiffPress'],'_ylim': [0, 3], 'color':'rgba(0,255,0,0.4)', 'unit':'mbar'},
        ],
        'lubrication' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,5000), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['Hyd_PressCrankCase'],'ylim': [-100, 100], 'color':'orange', 'unit':'mbar'},
        {'col':['Hyd_PressOilDif'],'ylim': [0, 3], 'color':'black', 'unit': 'bar'},
        {'col':['Hyd_PressOil'],'ylim': [0, 10], 'color':'brown', 'unit': 'bar'},
        {'col':['Hyd_TempOil','Hyd_TempCoolWat','Hyd_TempWatRetCoolOut'],'ylim': [0, 110], 'color':['#2171b5','orangered','hotpink'], 'unit':'°C'},
        ],
        'exhaust' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,5000), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':func('Exhaust_TempCyl*'),'ylim': [400, 700], 'unit':'°C'},
        {'col':func('Knock_Valve_Noise_Cyl*'),'ylim': [0, 12000], 'unit':'mV'},
        ],
        'ignition' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,5000), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':func('Monic_VoltCyl*'),'ylim': [0, 100], 'unit':'kV'},
        {'col':func('Ignition_ITPCyl*'),'ylim': [0, 40], 'unit':'°KW'},
        {'col':func('Knock_KLS98_IntKnock_Cyl*'),'ylim': [-80, 10], 'unit':'%'},
        ],    
    }

def overview_figure():
    return {
        'basic': [
        {'col':['cumstarttime'],'_ylim':(-600,800), 'color':'darkblue'},
        {'col':['runout'],'_ylim':(0,100) },
        {'col':['targetload'],'_ylim':(-4000,26000) },
        {'col':['ramprate'],'_ylim':(-5,7)},
        {'col':['loadramp'],'_ylim':(-150,900), 'color':'red'},
        {'col':['speedup'],'_ylim':(-100,200), 'color':'orange'},
        {'col':['synchronize'],'_ylim':(-20,400)},
        {'col':['startpreparation'],'_ylim':(-1000,800)},
        {'col':['W','A','isuccess'],'_ylim':(-1,200), 'color':['rgba(255,165,0,0.3)','rgba(255,0,0,0.3)','rgba(0,128,0,0.2)'] },
        {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.1)'] },
        #{'col':['W','A','no'],'ylim':(-1,200), 'color':['rgba(255,165,0,0.3)','rgba(255,0,0,0.3)','rgba(0,0,0,0.1)'] }
        ]
    }

#with open('/opt/notebooks/assets/Misterious_mist.gif', 'rb') as f:
with open('./assets/Misterious_mist.gif', 'rb') as f:
    img = f.read()    
loading_bar = widgets.Image(
    value=img
)

qfn = './engines.pkl'
query_list_fn = './query_list.json'

def init_query_list():
    return ['Forsa Hartmoor','BMW Landshut']

def get_query_list_pkl():
    if os.path.exists(qfn):
        with open(qfn, 'rb') as handle:
            query_list = pickle.load(handle)
    else:  
        query_list = init_query_list()
    return query_list

def get_query_list():
    if os.path.exists(query_list_fn):
        query_list=load_json(query_list_fn)
    else:  
        query_list = init_query_list()
    return query_list

def save_query_list(query_list):
    query_list = [q for q in query_list if not q in ['312','316','320','412','416','420','424','612','616','620','624','920']]
    save_json(query_list_fn,query_list)    

@dataclass
class V:
    hh = '350px' # window height
    dfigsize = (18,10)
    fleet = None
    e = None
    lfigures = myfigures()
    plotdef, vset = cplotdef(mp, lfigures)
    fsm = None
    rdf = pd.DataFrame([])
    selected = ''
    selected_number = ''
    modes_value = []
    succ_value = []
    alarm_warning_value = []
    query_list = []

def init_globals():
    V.e = None
    V.lfigures = myfigures()
    V.plotdef, V.vset = cplotdef(mp, V.lfigures)
    V.fsm = None
    V.rdf = pd.DataFrame([])
    V.query_list = get_query_list()

# el = Text(
#     value='-', description='selected:', disabled=True, 
#     layout=Layout(width='603px'))

init_globals()
tabs_out = widgets.Output()
tabs_html = widgets.HTML(
    value='',
    Layout=widgets.Layout(
        overflow='scroll',
        border ='1px solid black',
        width  ='auto',
        height ='auto',
        flex_flow = "column wrap",
        align_items = "flex-start",
        display='flex')
)