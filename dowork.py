import pandas as pd; pd.options.mode.chained_assignment = None # default warn => SettingWithCopyWarning
import numpy as np
import arrow
import bokeh
from bokeh.models import Span, Text, Label
from IPython.display import HTML, display
from dmyplant2 import dbokeh_chart, bokeh_show, add_dbokeh_vlines, add_dbokeh_hlines, FSMPlot_Start, detect_edge_left, detect_edge_right
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)

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