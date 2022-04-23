import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
from datetime import datetime, date
import ipywidgets as widgets
from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from IPython.display import display
from dmyplant2 import cred, MyPlant
from dmyplant2 import FSMOperator #, Engine, cplotdef
from App import tab1
from App.common import loading_bar, V

#########################################
# tab2
#########################################
tab2_out = widgets.Output()

def fsm_loadmessages(b):
    with tab2_out:
        tab2_out.clear_output()
        print('.. loading messages.')
        display(loading_bar)
        try:
            V.fsm = FSMOperator(V.e, p_from=t1.value, p_to=t2.value)
            tab2_out.clear_output()
            b_runfsm.button_style='primary'
            b_runfsm.disabled = False
            if not V.fsm.exists:
                b_loadfsm.disabled = True
                b_loadfsm.button_style = ''
            else:
                b_loadfsm.disabled = False
                b_loadfsm.button_style = 'primary'
        except Exception as err:
            tab2_out.clear_output()
            print('Error: ',str(err))

#@tab2_out.capture(clear_output=True)
def fsm_run(b):
    motor = V.fleet.iloc[int(tab1.selno.value)]
    with tab2_out:
        tab2_out.clear_output()
        if V.fsm is not None:
            print()
            V.fsm.run0(enforce=True, silent=False, debug=False)
            V.fsm.run1(silent=False, successtime=300, debug=False) # run Finite State Machine
            V.fsm.run2(silent = False)
            V.fsm.store()
            V.rdf = V.fsm.starts
            print()
            print(f"Starts: {V.rdf.shape[0]}") 
            print(f"Successful: {V.rdf[V.rdf['success'] == 'success'].shape[0]}, Failed: {V.rdf[V.rdf['success'] == 'failed'].shape[0]}, Undefined: {V.rdf[V.rdf['success'] == 'undefined'].shape[0]}")
            print(f"Starting reliability raw: {V.rdf[V.rdf['success'] == 'success'].shape[0]/(V.rdf.shape[0])*100.0:3.1f}% ")
            print(f"Starting reliability: {V.rdf[V.rdf['success'] == 'success'].shape[0]/(V.rdf.shape[0]-V.rdf[V.rdf['success'] == 'undefined'].shape[0])*100.0:3.1f}% ")


def fsm_load(b):
    with tab2_out:
        tab2_out.clear_output()
        print('Please Wait, loading FSM Results')
        display(loading_bar)
        V.fsm.restore()
        tab2_out.clear_output()
        V.rdf = V.fsm.starts
        print()
        if 'save_date' in V.fsm.results:
            print(f"{'Results Date:':>25} {V.fsm.results['save_date'].strftime('%d.%m.%Y')}")
        print(f"{'Time Range:':>25} {V.fsm.results['first_message'].strftime('%d.%m.%Y')} - {V.fsm.results['last_message'].strftime('%d.%m.%Y')}")
        print(f"{'Starts:':>25} {V.rdf.shape[0]}") 
        print(f"{'Successful:':>25} {V.rdf[V.rdf['success'] == 'success'].shape[0]}")
        print(f"{'Failed:':>25} {V.rdf[V.rdf['success'] == 'failed'].shape[0]}")
        print(f"{'Undefined:':>25} {V.rdf[V.rdf['success'] == 'undefined'].shape[0]}")
        print(f"{'Starting reliability raw:':>25} {V.rdf[V.rdf['success'] == 'success'].shape[0]/(V.rdf.shape[0])*100.0:3.1f}% ")
        print(f"{'Starting reliability:':>25} {V.rdf[V.rdf['success'] == 'success'].shape[0]/(V.rdf.shape[0]-V.rdf[V.rdf['success'] == 'undefined'].shape[0])*100.0:3.1f}% ")

###############
# tab2 widgets
###############
el = Text(
    value='-', description='selected:', disabled=True, 
    layout=Layout(width='603px'))
t1 = widgets.DatePicker( 
    value=pd.to_datetime('2022-01-01'), 
    description='From: ',disabled=False)
t2 = widgets.DatePicker( 
    value = date.today(), 
    description='To:',disabled=False)

b_loadmessages = Button(
    description='load Messages',
    disabled=False, 
    button_style='primary')
b_loadmessages.on_click(fsm_loadmessages)

b_runfsm = widgets.Button(
    description='Run FSM',
    disabled=True, 
    button_style='')
b_runfsm.on_click(fsm_run)

b_loadfsm = widgets.Button(
    description='Load FSM',
    disabled=True, 
    button_style='')
b_loadfsm.on_click(fsm_load)
_tab = VBox([HBox([VBox([el,HBox([t1,t2])]),VBox([b_loadmessages,b_runfsm,b_loadfsm])]),tab2_out])