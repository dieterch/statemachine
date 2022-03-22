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


def _add_plotly_trace(i, rec, data, pdata, playout, pside='right', panchor='free', pposition=0.0):
    ax_suffix = str(i+1) if i > 0 else ''
    short_axname = 'y' + ax_suffix; long_axname = 'yaxis' + ax_suffix
    playout[long_axname] = {
        'title':f"{rec['col'][0].split('_')[-1]} [{rec['unit']}]",
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
        playout[long_axname].update({'color': rec['color']})
        pdata.append(go.Scattergl(x=data['datetime'], y=data[rec['col'][0]], line_color=rec['color'] ,name=rec['col'][0], yaxis=short_axname))
    else:
        pdata.appen(go.Scattergl(x=data['datetime'], y=data[rec['col'][0]] ,name=rec['col'][0], yaxis=short_axname))

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
    ax_width = 75
    asp = ax_width / pwidth

    pdata = []
    playout = {
        'hovermode':"x unified",
        'hoverlabel':{
            'bgcolor': 'rgba(240,240,240,0.8)',
            'font_family': 'Courier',
            'namelength': -1
        },
        'showlegend':True,
        'legend': { 'yanchor':'top', 'y':0.99,'xanchor':'left', 'x':0.01,'bgcolor': 'rgba(255,255,255,0.4)'},
        'title_text': f"{fsm._e} -- Start {startversuch['no']} {startversuch['mode']} | {'SUCCESS' if startversuch['success'] else 'FAILED'} | {startversuch['starttime'].round('S')}",
        'width':pwidth,
        'height':pheight,
        'xaxis':{ 
            'domain':[0.0,1.0-(len(ddset)-2)*asp],
            'showgrid':True
        },
    }

    _add_plotly_trace(0, ddset[0], data, pdata, playout, panchor='x', pside='left')
    if len(ddset) > 1:
        for i,graph in enumerate(ddset[1:]):
            _add_plotly_trace(i+1, graph, data, pdata, playout, panchor='free', pside='right', pposition=float(1-asp*i))

    data['hover'] = 60
    pdata.append(go.Scattergl(x=data['datetime'],y=data['hover'], line_color='rgba(255,255,255,0)', name="",yaxis=f"y{len(pdata)+1}"))
    playout[f"yaxis{len(pdata)}"] = {'title':'','anchor':'free','overlaying':'y','side':'right','position':1.0,'range':(0,100),
                                    'title_standoff': 4,'showgrid':False,'fixedrange':True,'color':'rgba(255,255,255,0)'}

    customdata=[tuple(x) for x in data[[n['col'][0] for n in ddset]].to_numpy()]
    #customdata=np.array(data)
    hovertemplate = ('<br>'.join([f"{n['col'][0].split('_')[-1]:>14} %{{customdata[{i}]:7.2f}} [{n['unit']}]" for i, n in enumerate(ddset)]) + '<extra></extra>')

    fig2 = go.Figure(data=pdata, layout=playout)
    fig2.update_traces(customdata=customdata, hovertemplate=hovertemplate)
    return fig2