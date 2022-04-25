import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
import numpy as np
import traceback
from datetime import datetime, date
import ipywidgets as widgets
from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from IPython.display import display
from dmyplant2 import (
    cred, MyPlant, FSMOperator, startstopFSM, cplotdef, load_data, get_cycle_data2, get_cycle_data3, count_columns, 
    FSM_splot, FSM_add_Notations, disp_alarms, disp_warnings, FSM_add_Alarms,
    FSM_add_Warnings, bokeh_show, cvset
)
from bokeh.io import push_notebook #, show, output_notebook
from App.common import loading_bar, V, myfigures, mp
from App import tab2

#########################################
# tab4
#########################################
tab4_out = widgets.Output()
pfigsize=(18,10)


def calc_time_range(sv):
    tns = pd.to_datetime((sv['starttime'].timestamp() + time_range.value[0]/100.0 * (sv['endtime']-sv['starttime']).seconds), unit='s')
    tne = pd.to_datetime((sv['starttime'].timestamp() + time_range.value[1]/100.0 * (sv['endtime']-sv['starttime']).seconds), unit='s')
    return tns, tne


def update_fig(x=0, lfigures=V.lfigures, plotselection=V.plotdef, vset=V.vset, plot_range=(0,100), debug=False, fsm=V.fsm):
    rdfs = V.rdf[V.rdf.no == x]
    if not rdfs.empty:

        with tab4_out:
            tab4_out.clear_output()
            display(loading_bar)

        startversuch = rdfs.iloc[0]
        print(f'Please Wait, loading data for Start No. {startversuch.no}')
        try:
            #data = get_cycle_data3(fsm, startversuch, cycletime=1, silent=True, p_data=vset, t_range=plot_range)
            data = get_cycle_data2(fsm, startversuch, cycletime=1, silent=True, p_data=vset, t_range=plot_range)
            #data['power_diff'] = pd.Series(np.gradient(data['Power_PowerAct']))
            tab4_out.clear_output()
            # PLotter
            ftitle = f"{fsm._e} ----- Start {startversuch['no']} {startversuch['mode']} | {'SUCCESS' if startversuch['success'] else 'FAILED'} | {startversuch['starttime'].round('S')}"
            fig_handles = []
            for doplot in plotselection:
                dset = lfigures[doplot]
                ltitle = f"{ftitle} | {doplot}"
                if count_columns(dset) > 12: # no legend, if too many lines.
                    fig = FSM_splot(fsm, startversuch, data, dset, title=ltitle, legend=False, figsize=pfigsize)
                else:
                    fig = FSM_splot(fsm, startversuch, data, dset, title=ltitle, figsize=pfigsize)

                fig = FSM_add_Notations(fig, fsm, startversuch)
                disp_alarms(startversuch)
                disp_warnings(startversuch)
                fig = FSM_add_Alarms(fig, fsm, startversuch)
                fig = FSM_add_Warnings(fig, fsm, startversuch)
                fig_handles.append(bokeh_show(fig, notebook_handle=True))
            for h in fig_handles:
                push_notebook(handle=h)

            print()
            print("messages leading to state change:")    
            print("-----------------------------------")
            for i, v in enumerate(fsm.runlogdetail(startversuch, statechanges_only=True)):
                print(f"{i:3} {v}")
            print(f"\nall messages during start attempt No.:{startversuch['no']:4d} leading to state change:")
            print("---------------------------------------------------------------------")
            for i, v in enumerate(fsm.runlogdetail(startversuch, statechanges_only=False)):
                print(f"{i:3} {v}")
                
        except Exception as err:
            tab4_out.clear_output()
            print('Error: ', str(err))
            if debug:
                print(traceback.format_exc())
    else:
        print(f"Error: Start No {x} is not in results.")

@tab4_out.capture(clear_output=True)
def show_plots(but):
    update_fig(x=sno.value, lfigures=V.lfigures, plotselection=plotselection.value, vset=V.vset, plot_range=time_range.value, fsm=V.fsm)

def start_info(*args):
    if V.fsm is not None:
        rdf = V.fsm.starts
        if not rdf.empty:
            sv = rdf.iloc[sno.value]
            ltitle = f"||| Start No {sv['no']} {sv['starttime'].round('S')} to {sv['endtime'].round('S')}"
            summary = pd.DataFrame(sv[startstopFSM.run2filter_content]).T
            r = summary.style.set_table_styles([
                {'selector':'th,tbody','props':'font-size:0.5rem; font-weight: bold; text-align:center; background-color: #D3D3D3; ' + \
                                        'border: 0px solid black; border-collapse: collapse; margin: 0px; padding: 0px;'},
                {'selector':'td','props':'font-size:0.7rem; text-align:center; min-width: 58px;'}]
            ).format(
                precision=2,
                na_rep='-',
#                formatter={
#                    'starter': "{:.1f}",
#                    'idle': "{:.1f}",
#                    'ramprate':"{:.2f}",
#                    'runout': lambda x: f"{x:0.1f}"
#                }
            ).hide().to_html()
            links = 'links to Myplant: | '
            time_new_start, time_new_end = calc_time_range(sv)
            for doplot in plotselection.options:
                ll = V.e.myplant_workbench_link(time_new_start, time_new_end, V.e.get_dataItems(dat=cvset(mp,V.lfigures[doplot])),doplot)
                links += f'{ll} | '
            start_table.value = links + ltitle + '<br>' + r
start_info()

def start_run2(b):
    if V.fsm is not None:
        rdf = V.fsm.starts
        if not rdf.empty:
            sv = rdf.iloc[sno.value]
            V.fsm.run2_collectors_setup()
            vset, tfrom, tto = V.fsm.run2_collectors_register(sv)
            ldata = load_data(V.fsm, cycletime=1, tts_from=tfrom, tts_to=tto, silent=True, p_data=vset, p_forceReload=False, p_suffix='_individual', debug=False)
            V.fsm.results = V.fsm.run2_collectors_collect(sv, V.fsm.results, ldata)
            phases = list(V.fsm.results['starts'][sno]['startstoptiming'].keys())
            V.fsm.self.startstopHandler._harvest_timings(V.fsm.results['starts'][sno], phases, V.fsm.results)
            start_info() 

###############
# tab4 widgets
###############

sno = widgets.IntText(
    description='StartNo: ',
    layout=widgets.Layout(width='236px'))

sno_slider = widgets.IntSlider(0, 0, 5 , 1,
    description = 'StartNo:',
    layout=widgets.Layout(width='516px'))
mylink = widgets.jslink((sno, 'value'), (sno_slider, 'value'))
sno.observe(start_info, 'value')

tshowplots = widgets.Button(description='Plots',disabled=False, button_style='primary')
tshowplots.on_click(show_plots)

b_run2 = widgets.Button(description='run2',disabled=False, tooltip='Run2 Results for the selected start', button_style='primary')
b_run2.on_click(start_run2)

plotselection = widgets.SelectMultiple( 
    options=list(myfigures().keys()), 
    value=list(myfigures().keys())[:], 
    rows=min(len(myfigures()),3), 
    disabled=False,
    description='Al & War:')
start_table = widgets.HTML()

time_range = widgets.IntRangeSlider(
    value=[0, 100],
    min=0,
    max=100,
    step=1,
    description='Range (%):',
    disabled=False,
    #continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d',
    layout=widgets.Layout(width='603px')
)
time_range.observe(start_info,'value')

_tab = VBox([
            HBox([
                VBox([
                    HBox([tab2.el, tshowplots]),
                    HBox([sno_slider, sno])
                ]),
                plotselection
            ]),
            HBox([time_range, b_run2]),
            start_table,
            tab4_out
        ]);