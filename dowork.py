import pandas as pd; pd.options.mode.chained_assignment = None # default warn => SettingWithCopyWarning
import numpy as np
import arrow
import bokeh
from bokeh.models import Span, Text, Label
from IPython.display import HTML, display
from dmyplant2 import dbokeh_chart, bokeh_show, add_dbokeh_vlines, add_dbokeh_hlines, FSMPlot_Start, detect_edge_left, detect_edge_right
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)

import plotly.graph_objects as go
import plotly.io as pio
pio.templates.default='simple_white'
pio.renderers.default = "notebook"

def plot_now(
        fsm,
        data,
        startversuch,
        vset, 
        dset,
        dfigsize=(16,8)
    ):

    # vset = []
    # for rec in dset:
    #     for d in rec['col']:
    #         vset.append(d) 
    # vset = list(set(vset))

    fig = FSMPlot_Start(fsm, startversuch, data, vset, dset, figsize=dfigsize); 
    #fsm run 2 results
    lcol='blue'
    pl, _ = detect_edge_left(data, 'Power_PowerAct', startversuch)
    pr, _ = detect_edge_right(data, 'Power_PowerAct', startversuch)
    sl, _ = detect_edge_left(data, 'Various_Values_SpeedAct', startversuch)
    sr, _ = detect_edge_right(data, 'Various_Values_SpeedAct', startversuch)
    add_dbokeh_vlines([sl.loc], fig,line_color=lcol, line_dash='solid', line_alpha=0.4)
    add_dbokeh_vlines([sr.loc], fig,line_color=lcol, line_dash='solid', line_alpha=0.4)
    add_dbokeh_vlines([pl.loc], fig,line_color=lcol, line_dash='solid', line_alpha=0.4)
    add_dbokeh_vlines([pr.loc], fig,line_color=lcol, line_dash='solid', line_alpha=0.4)

    #pp(startversuch['timing']) # ['timings']['start_loadramp'])
    if 'loadramp' in startversuch['timing']:
        add_dbokeh_vlines([startversuch['timing']['loadramp'][-1]['end']], fig,line_color='green', line_dash='solid', line_alpha=0.4, line_width=4)

    return fig


def plot_plotly(
        fsm,
        data,
        startversuch,
        vset, 
        ddset,
        dfigsize=(16,8)
    ):
    
    dpi = 66
    pwidth = dfigsize[0] * dpi
    pheight = dfigsize[1] * dpi

    #pwidth = 1200
    #pheight = 800 
    ax_width = 75
    asp = ax_width / pwidth

    pdata = [ go.Scattergl(x=data['datetime'], y=data[ddset[0]['col'][0]], line_color=ddset[0]['color'] ,name=ddset[0]['col'][0], yaxis=f"y") ] if 'color' in ddset[0] else \
            [ go.Scattergl(x=data['datetime'], y=data[ddset[0]['col'][0]] ,name=ddset[0]['col'][0], yaxis=f"y") ]

    playout = {
        'hovermode':"x unified",
        'hoverlabel':{
            'bgcolor': 'rgba(240,240,240,0.75)',
            'font_family': 'Courier',
            'namelength': -1
        },
        'showlegend':True,
        'legend': { 'yanchor':'top', 'y':0.99,'xanchor':'left', 'x':0.01,'bgcolor': 'rgba(255,255,255,0.4)'},
        'title_text': f"{fsm._e} -- Start {startversuch['no']} {startversuch['mode']} | {'SUCCESS' if startversuch['success'] else 'FAILED'} | {startversuch['starttime'].round('S')}",
        'width':pwidth,
        'height':pheight,
        'xaxis':{ 
            'domain':[0.0,1-(len(ddset)-2)*asp],
            'showgrid':True
        },
        'yaxis':{
            'title':f"{ddset[0]['col'][0].split('_')[-1]} [{ddset[0]['unit']}]",
            'anchor':'x','overlaying':'y','side':'left','position':0.0,
            'title_standoff': 4,
            'showgrid':True,
            'fixedrange':True
        }
    }
    if 'ylim' in ddset[0]:
            playout['yaxis'].update({'range': ddset[0]['ylim']})
    if 'color' in ddset[0]:
            playout['yaxis'].update({'color': ddset[0]['color']})

    if len(ddset) > 1:
        for i,graph in enumerate(ddset[1:]):
            yaxisname = f'yaxis{i+2}'
            playout[yaxisname] = {
                'title':f"{graph['col'][0].split('_')[-1]} [{graph['unit']}]",
                'anchor':'free','overlaying':'y','side':'right','position':(1-asp*i),
                'title_standoff': 4,
                'showgrid':True,
                'fixedrange':True}
            if 'ylim' in graph: playout[yaxisname].update({'range':graph['ylim']})
            if 'color' in graph:
                playout[yaxisname].update({'color':graph['color']})
                pdata.append( go.Scattergl(x=data['datetime'], y=data[graph['col'][0]], line_color=graph['color'], name=graph['col'][0], yaxis=f"y{i+2}"))
            else:
                pdata.append( go.Scattergl(x=data['datetime'], y=data[graph['col'][0]], name=graph['col'][0], yaxis=f"y{i+2}"))


    data['hover'] = 60
    pdata.append(go.Scattergl(x=data['datetime'],y=data['hover'], line_color='rgba(255,255,255,0)', name="",yaxis=f"y{len(pdata)+1}"))
    playout[f"yaxis{len(pdata)}"] = {'title':'','anchor':'free','overlaying':'y','side':'right','position':1.0,'range':(0,100),
                                    'title_standoff': 4,'showgrid':False,'fixedrange':True,'color':'rgba(255,255,255,0)'}

    customdata=[tuple(x) for x in data[[n['col'][0] for n in ddset]].to_numpy()]
    hovertemplate = ('<br>'.join([f"{n['col'][0].split('_')[-1]:>14} %{{customdata[{i}]:7.2f}} [{n['unit']}]" for i, n in enumerate(ddset)]) + '<extra></extra>')

    fig2 = go.Figure(data=pdata, layout=playout)
    fig2.update_traces(customdata=customdata, hovertemplate=hovertemplate)
    return fig2