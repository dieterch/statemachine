import os
import sys
import pickle
from turtle import width
import pandas as pd; pd.options.mode.chained_assignment = None
from datetime import datetime, date, timedelta
import ipywidgets as widgets
from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from IPython.display import display
from dmyplant2 import cred, MyPlant, Engine, FSMOperator, get_size
from App import tab1
from App.common import loading_bar, V, mp, tabs_out, tabs_html

#########################################
# tab2
#########################################
class Tab():
    def __init__(self):

        self.title = '2. messages & FSM'
        self.tab2_out = widgets.Output()
        self.run2_chkbox = widgets.Checkbox(
                value=False,
                description='FSM Run2',
                disabled=False,
                indent=False,
                layout=widgets.Layout(width='100px'))

        self.run2_refresh_chkbox = widgets.Checkbox(
                value=False,
                description='R2 Refresh',
                disabled=False,
                indent=False,
                layout=widgets.Layout(width='100px'))

        self.single_runs_chkbox = widgets.Checkbox(
                value=False,
                description='single Runs',
                disabled=False,
                indent=False,
                layout=widgets.Layout(width='100px'))
        self.single_runs_chkbox.observe(self.do_single_runs, 'value')

        self.tab2_selected_engine = widgets.Text(
            value='-', description='selected:', disabled=True, 
            layout=Layout(width='603px'))

        self.t1 = widgets.DatePicker( 
            value=pd.to_datetime('2022-01-01'), 
            description='From: ',disabled=False)
        
        self.t2 = widgets.DatePicker( 
            value = date.today(), 
            description='To:',disabled=False)

        self.load_message_text = 'load Messages'
        self.b_loadmessages = Button(
            description=self.load_message_text,
            disabled=True, 
            button_style='primary')
        self.b_loadmessages.on_click(self.fsm_loadmessages)

        self.b_runfsm = widgets.Button(
            description='Run All FSMs',
            disabled=True, 
            button_style='primary')
        self.b_runfsm.on_click(self.fsm_run)

        self.b_resultsfsm = widgets.Button(
            description='Results',
            disabled=True, 
            button_style='primary')
        self.b_resultsfsm.on_click(self.fsm_results)

        self.b_runfsm0 = widgets.Button(
            description='Run FSM0',
            disabled=True, 
            button_style='',
            layout=widgets.Layout(display='none'))
        self.b_runfsm0.on_click(self.fsm_run0)

        self.b_runfsm1 = widgets.Button(
            description='Run FSM1',
            disabled=True, 
            button_style='',
            layout=widgets.Layout(display='none'))
        self.b_runfsm1.on_click(self.fsm_run1)

        self.b_runfsm2 = widgets.Button(
            description='Run FSM2',
            disabled=True, 
            button_style='',
            layout=widgets.Layout(display='none'))
        self.b_runfsm2.on_click(self.fsm_run2)

        self.b_savefsm = widgets.Button(
            description='Save FSM',
            disabled=True, 
            button_style='primary')
        self.b_savefsm.on_click(self.fsm_save) 

    @property
    def tab(self):
        return VBox([
            HBox([
                VBox([
                    self.tab2_selected_engine,
                    HBox([self.t1,self.t2]),
                    self.tab2_out
                ]),
                VBox([
                    self.run2_chkbox,
                    self.run2_refresh_chkbox,
                    self.single_runs_chkbox
                ]),
                VBox([
                    self.b_loadmessages,
                    self.b_runfsm,
                    self.b_resultsfsm,
                    self.b_runfsm0,
                    self.b_runfsm1,
                    self.b_runfsm2,
                    self.b_savefsm,
                ])
            ])
        ],layout=widgets.Layout(min_height=V.hh))
        

    def selected(self):
        self.check_buttons()
        with tabs_out:
            tabs_out.clear_output()
            print('tab2')
            tabs_html.value = ''
            if V.fleet is not None:
                if not V.fleet.empty:
                    if V.selected != '':
                        self.b_loadmessages.description = self.load_message_text
                        tabs_out.clear_output()
                        print(f'tab2 - ⌛ loading Myplant Engine Data for "{V.selected}" ...')
                        V.e=Engine.from_fleet(mp, V.fleet.iloc[int(V.selected_number)])
                        self.tab2_selected_engine.value = V.selected
                        self.t1.value = pd.to_datetime(V.e['Commissioning Date'])
                        self.check_buttons()
                        tabs_out.clear_output()
                        print('tab2')
                    else:
                        self.tab2_selected_engine.value = ''
                        self.t1.value = None
                        V.fsm = None
                else:
                    self.tab2_selected_engine.value = ''
            else: # engine was loaded from file
                self.tab2_selected_engine.value = V.selected
                self.b_loadmessages.description = 'append new messages'
                self.check_buttons()
                
        with self.tab2_out:        
            self.tab2_out.clear_output()
            self.check_buttons()
                    
    def fsm_loadmessages(self,b):
        with tabs_out:
            tabs_out.clear_output()
            print('tab2 - ⌛ loading messages.')
            #display(loading_bar)
            try:
                V.fsm = FSMOperator(V.e, p_from=self.t1.value, p_to=self.t2.value)
                tabs_out.clear_output()
                self.check_buttons()
            except Exception as err:
                tabs_out.clear_output()
                print('Error: ',str(err))

    def do_single_runs(self, *args):
        if self.single_runs_chkbox.value:
            self.b_runfsm0.layout.display = 'block'
            self.b_runfsm1.layout.display = 'block'
            self.b_runfsm2.layout.display = 'block'
        else:
            self.b_runfsm0.layout.display = 'none'
            self.b_runfsm1.layout.display = 'none'
            self.b_runfsm2.layout.display = 'none'

    #@tab2_out.capture(clear_output=True)
    def fsm_run(self,b):
        motor = V.fleet.iloc[int(V.selected_number)]
        with self.tab2_out:
            self.tab2_out.clear_output()
            if V.fsm is not None:
                print()
                V.fsm.run0(enforce=True, silent=False, debug=False)
                #print(f"fsm Operator Memory Consumption: {get_size(V.fsm.__dict__)/(1024*1024):8.1f} MB")
                V.fsm.run1(silent=False, successtime=300, debug=False) # run Finite State Machine
                #print(f"fsm Operator Memory Consumption: {get_size(V.fsm.__dict__)/(1024*1024):8.1f} MB")
                if self.run2_chkbox.value:
                    V.fsm.run2(silent = False, p_refresh=self.run2_refresh_chkbox.value)
                    #print(f"fsm Operator Memory Consumption: {get_size(V.fsm.__dict__)/(1024*1024):8.1f} MB")
                V.rdf = V.fsm.starts
                self.check_buttons()

    def print_result(self):
            print()
            print(f"Starts: {V.rdf.shape[0]}") 
            print(f"Runs: {V.fsm.runs_completed}")
            print(f"Successful: {V.rdf[V.rdf['success'] == 'success'].shape[0]}," + 
                  f" Failed: {V.rdf[V.rdf['success'] == 'failed'].shape[0]}, Undefined: {V.rdf[V.rdf['success'] == 'undefined'].shape[0]}")
            print(f"Starting reliability raw: {V.rdf[V.rdf['success'] == 'success'].shape[0]/(V.rdf.shape[0])*100.0:3.1f}% ")
            print(f"Starting reliability: {V.rdf[V.rdf['success'] == 'success'].shape[0]/(V.rdf.shape[0]-V.rdf[V.rdf['success'] == 'undefined'].shape[0])*100.0:3.1f}% ")


    def fsm_results(self,b):
        with self.tab2_out:
            if V.fsm is not None:
                V.rdf = V.fsm.starts
                if len(V.rdf) > 0:
                    self.print_result()
                if len(V.fsm.results['run2_failed']) > 0:
                    with tabs_out:
                        tabs_out.clear_output()
                        print()
                        print('unsucessful run2 data:')
                        print('---------------------------------')
                        #display(pd.DataFrame(V.fsm.results['run2_failed'])[V.fsm.startstopHandler.run2filter_content].style.hide())
                        dfilter = [k for k in V.fsm.results['run2_content']['startstop'] if k in V.fsm.results['run2_failed'][0]]
                        #display(pd.DataFrame(V.fsm.results['run2_failed'])[V.fsm.results['run2_content']['startstop']].style.hide())
                        display(pd.DataFrame(V.fsm.results['run2_failed'])[dfilter].style.hide())

    def fsm_run0(self,b):
        #motor = V.fleet.iloc[int(V.selected_number)]
        with self.tab2_out:
            self.tab2_out.clear_output()
            if V.fsm is not None:
                print()
                V.fsm.run0(enforce=True, silent=False, debug=False)
                self.check_buttons()
                #print(f"fsm Operator Memory Consumption: {get_size(V.fsm.__dict__)/(1024*1024):8.1f} MB")

    def fsm_run1(self,b):
        with self.tab2_out:
            #tab2_out.clear_output()
            if V.fsm is not None:
                V.fsm.run1(silent=False, successtime=300, debug=False) # run Finite State Machine
                self.check_buttons()
                V.rdf = V.fsm.starts
                #print(f"fsm Operator Memory Consumption: {get_size(V.fsm.__dict__)/(1024*1024):8.1f} MB")

                
    def fsm_run2(self,b):
        #motor = V.fleet.iloc[int(V.selected_number))]
        with self.tab2_out:
            #tab2_out.clear_output()
            if V.fsm is not None:
                V.fsm.run2(silent = False, debug=True, p_refresh=self.run2_refresh_chkbox.value)
                self.check_buttons()
                V.rdf = V.fsm.starts
                #print(f"fsm Operator Memory Consumption: {get_size(V.fsm.__dict__)/(1024*1024):8.1f} MB")

                
    def fsm_save(self,b):
        if V.fsm is not None:
            filename = f'./data/{V.fsm._e["serialNumber"]}_{V.fsm._e["Validation Engine"]}.dfsm'
            with tabs_out:
                print(filename)
                V.fsm.save_results(filename)
        # with self.tab2_out:
        #     if V.fsm is not None:
        #         V.fsm.store()

    def check_buttons(self):
        for b in [ self.b_loadmessages, self.b_runfsm, self.b_resultsfsm, self.b_runfsm0, self.b_runfsm1, self.b_runfsm2, self.b_savefsm]:
            b.disabled=True
        if ((V.e is not None) and (self.t1.value is not None) and (self.t2.value is not None)):
            self.b_loadmessages.disabled=False
        if ((V.fsm is not None) and hasattr(V.fsm, '_messages')):
            self.b_runfsm.disabled = False
            self.b_runfsm0.disabled = False
        else:
            self.b_runfsm.disabled = True
        if ((V.fsm is not None) and all(e in V.fsm.runs_completed for e in [0])):
            self.b_runfsm0.disabled = True
            self.b_runfsm1.disabled = False
        if ((V.fsm is not None) and all(e in V.fsm.runs_completed for e in [0,1])):
            self.b_runfsm1.disabled = True
            self.b_runfsm2.disabled = False            
            self.b_resultsfsm.disabled = False            
            self.b_savefsm.disabled = False
        if ((V.fsm is not None) and all(e in V.fsm.runs_completed for e in [0,1,2])):
            self.b_runfsm2.disabled = True            

            
            
            
