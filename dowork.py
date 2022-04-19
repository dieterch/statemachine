import pandas as pd; pd.options.mode.chained_assignment = None # default warn => SettingWithCopyWarning
import numpy as np
import arrow
import bokeh
import time
from bokeh.models import Span, Text, Label
from IPython.display import HTML, display
from dmyplant2 import dbokeh_chart, bokeh_show, add_dbokeh_vlines, add_dbokeh_hlines
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)

import plotly.graph_objects as go
import plotly.io as pio

pio.templates.default='simple_white'
pio.renderers.default = "notebook"


pdef = ['Power_PowerAct','Hyd_PressOil','Hyd_PressOilDif','Hyd_TempOil','TecJet_Lambda1','TecJet_GasDiffPress','Exhaust_TempCylMin','Exhaust_TempCylMax']


def _add_plotly_trace(i, rec, data, pdata, playout, pside='right', panchor='free', pposition=0.0):
    ax_suffix = str(i+1) if i > 0 else ''
    short_axname = 'y' + ax_suffix; long_axname = 'yaxis' + ax_suffix
    ttl = ', '.join([name.split('_')[-1] for name in rec['col']])
    playout[long_axname] = {
        'title':f"{ttl} [{rec['unit']}]",
        'anchor':panchor,
        'overlaying':'y',
        'side':pside,
        'position':pposition,
        'title_standoff': 4,
        'showgrid':True,
        'fixedrange':True}
    if 'ylim' in rec:
        playout[long_axname].update({'range': rec['ylim']})
    if 'color' in rec:
        if isinstance(rec['color'], list):
            playout[long_axname].update({'color': 'black'})
            for i, dname in enumerate(rec['col']):
                pdata.append(go.Scattergl(x=data['datetime'], y=data[dname], line_color=rec['color'][i] ,name=dname, yaxis=short_axname))
        else:
            playout[long_axname].update({'color': rec['color']})
            pdata.append(go.Scattergl(x=data['datetime'], y=data[rec['col'][0]], line_color=rec['color'] ,name=rec['col'][0], yaxis=short_axname))
    else:
        pdata.append(go.Scattergl(x=data['datetime'], y=data[rec['col'][0]] ,name=rec['col'][0], yaxis=short_axname))

def plot_plotly(
        fsm,
        data,
        startversuch,
        vset, 
        ddset,
        dfigsize=(16,8)
    ):
    
    dpi = 66; pwidth = dfigsize[0] * dpi; pheight = dfigsize[1] * dpi
    ax_width = 75
    asp = ax_width / pwidth

    pdata = []
    playout = {
        'title_text': f"{fsm._e} -- Start {startversuch['no']} {startversuch['mode']} | {'SUCCESS' if startversuch['success'] else 'FAILED'} | {startversuch['starttime'].round('S')}",
        'hovermode':"x unified",
        'hoverlabel':{
            'bgcolor': 'rgba(240,240,240,0.8)',
            'font_family': 'Courier',
            'font_size':12,
            'namelength': -1
        },
        'showlegend':True,
        'legend': { 'yanchor':'top', 
                    'y':0.99,'xanchor':'left', 
                    'x':0.01,'bgcolor': 
                    'rgba(255,255,255,0.4)'
        },
        'xaxis':{ 
            'domain':[0.0,min(1.0,1.0-(len(ddset)-2)*asp)],
            'showgrid':True
        },
        'width':pwidth,
        'height':pheight,
        'margin':{
            'l':50,
            'r':50,
            'b':50,
            't':50,
            'pad':4
        }   
    }

    # add scatter traces and axis
    _add_plotly_trace(0, ddset[0], data, pdata, playout, panchor='x', pside='left')
    if len(ddset) > 1:
        for i,graph in enumerate(ddset[1:]):
            _add_plotly_trace(i+1, graph, data, pdata, playout, panchor='free', pside='left', pposition=float(1-asp*i))

    #t0 = time.time()
    # Trick für Hover - eine Linie mit Alpha = 0, also unsichtbar hält das hovertemplate
    data['hover'] = 60
    pdata.append(go.Scattergl(x=data['datetime'],y=data['hover'], line_color='rgba(255,255,255,0)', name="",yaxis=f"y{len(pdata)+1}"))
    playout[f"yaxis{len(pdata)}"] = {'title':'','anchor':'free','overlaying':'y','side':'right','position':1.0,'range':(0,100),
                                    'title_standoff': 4,'showgrid':False,'showline':False,'fixedrange':True,'color':'rgba(255,255,255,0)'}
    fig2 = go.Figure(data=pdata, layout=playout)
    datlist=[e for rec in ddset for e in rec['col']]
    customdata=np.array(data[datlist])
    hovertemplate = ('<br>'.join([f"{e.split('_')[-1]:>14} %{{customdata[{datlist.index(e)}]:7.2f}} [{rec['unit']}]" for rec in ddset for e in rec['col']]) + '<extra></extra>')
    fig2.update_traces(customdata=customdata, hovertemplate=hovertemplate)
    #t1 = time.time()
    #print(f"Dauer Berechnung Hovertemplate: {t1-t0}")

    return fig2


def plotly_verstehen(fsm, startversuch, data):

    playout = {
        'hovermode':"x unified",
        'showlegend':True,
        'legend': { 'yanchor':'top', 'y':0.99,'xanchor':'left', 'x':0.01,'bgcolor': 'rgba(255,255,255,0.4)'},
        'title_text': f"{fsm._e} -- Start {startversuch['no']} {startversuch['mode']} | {'SUCCESS' if startversuch['success'] else 'FAILED'} | {startversuch['starttime'].round('S')}",
        'width':1000,
        'height':600,
        'hoverlabel':{
            'bgcolor': 'rgba(240,240,240,0.7)',
            'font_family': 'Courier',
            'namelength': -1,
            },
        'xaxis':{ 'domain':[0,0.85]},
        'yaxis':{
            'title':'PowerAct, SpeedAct',
            #'color':"#1f77b4",
            'color':"black",
            'anchor':"x",
            'overlaying':"y",'side':"left",'position':0.0,
            'title_standoff': 4,
            'range':(0,5000),
            },
        'yaxis2':{
            'title':"PressOil",
            'color':"#d62728",
            'anchor':"free",'overlaying':"free",'side':"right",'position':0.85,
            'title_standoff': 4,
            'range':(0,10),
            'showgrid':True,
            'showline':True
            },
        'yaxis3':{
            'title':"TempOil",
            'color':"#9467bd",
            'anchor':"free",'overlaying':"y",'side':"right",'position':0.95,
            'title_standoff': 4,
            'range':(0,100),
            },
        # 'yaxis4':{
        #     'title':"SpeedAct",
        #     'color':"#ff7f0e",
        #     'anchor':"free",
        #     'overlaying':'y','side':"right",'position':0.7,
        #     'range':(0,2000),
        #     },
        'yaxis4':{
            'title':"",
            'color':"#ffffff",
            'anchor':"free",
            'overlaying':'y','side':"right",'position':1.0,
            'title_standoff': 4,
            'range':(0,100),
            'showline':False,
            'nticks':0
            },
    }

    data['hover'] = 60

    pdata = [
        go.Scattergl(x=data['datetime'],y=data['Power_PowerAct'], name='PowerAct',yaxis="y"), #Power_PowerAct
        go.Scattergl(x=data['datetime'],y=data['Various_Values_SpeedAct'], name="SpeedAct",yaxis="y"),
        go.Scattergl(x=data['datetime'],y=data['Hyd_PressOil'],name="PressOil",yaxis="y2"),
        go.Scattergl(x=data['datetime'],y=data['Hyd_TempOil'],name="TempOil",yaxis="y3"),
        go.Scattergl(x=data['datetime'],y=data['hover'], line_color='rgba(255,255,255,0)', name="",yaxis="y4"),
    ]

    #customdata=np.stack((data['Power_PowerAct'], data['Various_Values_SpeedAct']), axis=-1)
    subdata=data[['Power_PowerAct','Various_Values_SpeedAct','Hyd_PressOil','Hyd_TempOil']]
    customdata=[tuple(x) for x in subdata.to_numpy()]
    hovertemplate = ("Power:    %{customdata[0]:5.0f} [kW]<br>" +
                    "Speed:    %{customdata[1]:5.0f} [rpm]<br>" +
                    "Oilpress: %{customdata[2]:5.2f} [bar]<br>" +
                    "Oiltemp:  %{customdata[3]:5.1f} [°C]<br>" +
                    "<extra></extra>")

    fig3 = go.Figure(data=pdata,layout=playout)
    fig3.update_traces(customdata=customdata, hovertemplate=hovertemplate)
    fig3.show()
