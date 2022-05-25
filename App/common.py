from dataclasses import dataclass
import os, sys
import pickle
import pandas as pd; 
import math
pd.options.mode.chained_assignment = None
pd.set_option("display.precision", 2)
import ipywidgets as widgets
from IPython.display import display, HTML
from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from dmyplant2 import cred, MyPlant, Engine, cplotdef, save_json, load_json

try:
    cred()
    mp = MyPlant(0)
except Exception as err:
    print(str(err))
    sys.exit(1)

# DEFINITION OF PLOTS & OVERVIEW
def myfigures(e = None):
    def fake_cyl(dataItem):
        return [dataItem[:-1] + '01']
    func_cyl = fake_cyl if e is None else e.dataItemsCyl
    def fake_power():
        return 5000
    func_power = fake_power if e is None else math.ceil(e['Power_PowerNominal'] / 1000.0) * 1000.0
    return {
        'actors' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,func_power), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['Ignition_ITPAvg'],'ylim': [-10, 30], 'color':'rgba(255,0,255,0.4)', 'unit':'°KW'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':['Aux_PreChambDifPress'],'_ylim': [0, 3], 'color':'purple', 'unit':'-'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':['Various_Values_PressBoost'],'_ylim': [0, 3], 'color':'dodgerblue', 'unit':'bar'},
        {'col':['Various_Values_TempMixture'],'ylim': [0, 200], 'color':'orange', 'unit':'°C'},
        {'col':['Various_Values_PosThrottle','Various_Values_PosTurboBypass'],'ylim': [-10, 110], 'color':['rgba(105,105,105,0.6)','rgba(165,42,42,0.4)'], 'unit':'%'},
        ],
        'tecjet' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,func_power), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['bmep'], 'ylim':(-10,40), 'color':'orange', 'unit':'bar'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['Ignition_ITPAvg'],'ylim': [-10, 30], 'color':'limegreen', 'unit':'°KW'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':['TecJet_GasPress1'],'_ylim': [0, 3], 'color':'rgba(255,0,0,0.4)', 'unit':'mbar'},
        {'col':['TecJet_GasTemp1'],'_ylim': [0, 3], 'color':'rgba(255,0,255,0.4)', 'unit':'°C'},
        {'col':['TecJet_GasDiffPress'],'_ylim': [0, 3], 'color':'olive', 'unit':'mbar'},
        {'col':['TecJet_ValvePos1'],'ylim': [0, 200], 'color':'purple', 'unit':'%'},
        ],
        'lubrication' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,func_power), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['Hyd_PressCrankCase'],'ylim': [-100, 100], 'color':'orange', 'unit':'mbar'},
        {'col':['Hyd_PressOilDif'],'ylim': [0, 3], 'color':'black', 'unit': 'bar'},
        {'col':['Hyd_PressOil'],'ylim': [0, 10], 'color':'brown', 'unit': 'bar'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':['Hyd_TempOil','Hyd_TempCoolWat','Hyd_TempWatRetCoolOut'],'ylim': [0, 110], 'color':['#2171b5','orangered','hotpink'], 'unit':'°C'},
        ],
        'exhaust' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,func_power), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':func_cyl('Exhaust_TempCyl*'),'ylim': [300, 700], 'unit':'°C'},
        ],
        'exhaust2' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,func_power), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':func_cyl('Exhaust_TempCyl*'),'ylim': [0, 700], 'unit':'°C'},
        ],
        'valvenoise' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,func_power), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':func_cyl('Knock_Valve_Noise_Cyl*'),'ylim': [0, 12000], 'unit':'mV'},
        ],

        'ignition' : [
        {'col':['Power_SetPower','Power_PowerAct'], 'ylim':(0,func_power), 'color':['lightblue','red'], 'unit':'kW'},
        {'col':['Various_Values_SpeedAct'],'ylim': [0, 2500], 'color':'blue', 'unit':'rpm'},
        {'col':['TecJet_Lambda1'],'ylim': [0, 3], 'color':'rgba(255,165,0,0.4)', 'unit':'-'},
        {'col':func_cyl('Monic_VoltCyl*'),'ylim': [0, 100], 'unit':'kV'},
        {'col':func_cyl('Ignition_ITPCyl*'),'ylim': [0, 40], 'unit':'°KW'},
        {'col':func_cyl('Knock_KLS98_IntKnock_Cyl*'),'ylim': [-80, 10], 'unit':'%'},
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
        {'col':['oilfilling'],'_ylim':(-1000,800)},
        {'col':['degasing'],'_ylim':(-1000,800)},
        {'col':['W','A','isuccess'],'_ylim':(-1,200), 'color':['rgba(255,165,0,0.3)','rgba(255,0,0,0.3)','rgba(0,128,0,0.2)'] },
        {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.1)'] },
        #{'col':['W','A','no'],'ylim':(-1,200), 'color':['rgba(255,165,0,0.3)','rgba(255,0,0,0.3)','rgba(0,0,0,0.1)'] }
        ],
        'basic2': [
        {'col':['targetload'],'ylim':(-4000,26000) },
        {'col':['idle'],'ylim':(-100,1000), 'color':'dodgerblue' },
        {'col':['W','A','isuccess'],'ylim':(-1,200), 'color':['rgba(255,165,0,0.3)','rgba(255,0,0,0.3)','rgba(0,128,0,0.2)'] },
        {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.1)'] },
        #{'col':['W','A','no'],'ylim':(-1,200), 'color':['rgba(255,165,0,0.3)','rgba(255,0,0,0.3)','rgba(0,0,0,0.1)'] }
        ],        
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
    dfigsize = (22,10)
    fleet = None
    e = None
    lfigures = myfigures()
    plotdef, vset = cplotdef(mp, lfigures)
    fsm = None
    rdf = pd.DataFrame([])
    selected = ''
    selected_number = ''
    modes_value = ['MAN','AUTO']
    succ_value = ['undefined','success']
    alarm_warning_value = ['-']
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

def status(tbname ,text=''):
    with tabs_out:
        tabs_out.clear_output()
        print(f'{tbname}{" - " if text != "" else ""}{text}')

def disp_alwr(row, key):
    rec = row[key]
    style = '''<style>
        table, 
        td, 
        th {
            border: 0px solid grey;
            border-collapse: collapse;
            padding: 0px 14px 0px 2px; 
            margin: 0px;
            font-size:0.7rem;
            /* min-width: 100px; */
        }
    </style>'''
    ll = []
    for m in rec:
        ll.append({
            'sno': row['no'],
            'datetime':pd.to_datetime(int(m['msg']['timestamp'])*1e6).strftime('%Y-%m-%d %H:%M:%S'),
            'state': m['state'],
            'number': m['msg']['name'],
            'type': 'Alarm' if m['msg']['severity'] == 800 else 'Warning',
            'severity': m['msg']['severity'],
            'message': m['msg']['message']
        })
    if len(rec) > 0:
        display(HTML(style + pd.DataFrame(ll).to_html(index=False, header=False)))

def display_fmt(df):
    display(df[['starttime'] + V.fsm.results['run2_content']['startstop']]                    
                        .style
                        .set_table_styles([
                            {'selector':'table,td,th', 'props': 'font-size: 0.7rem; '}
                        ])
                        .hide()
                        .format(
                    precision=2,
                    na_rep='-',
                    formatter={
                        'starttime': "{:%Y-%m-%d %H:%M:%S %z}",
                        'startpreparation': "{:.0f}",                        
                        'starter': "{:.1f}",
                        'speedup': "{:.1f}",
                        'idle': "{:.1f}",
                        'synchronize': "{:.1f}",
                        'loadramp': "{:.0f}",
                        'cumstarttime': "{:.0f}",
                        'targetload': "{:.0f}",
                        'ramprate':"{:.2f}",
                        'maxload': "{:.0f}",
                        'targetoperation': "{:.0f}",
                        'rampdown': "{:.1f}",
                        'coolrun': "{:.1f}",
                        'runout': lambda x: f"{x:0.1f}"
                    }
                ))