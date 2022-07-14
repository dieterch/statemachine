import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
import numpy as np
import traceback
from datetime import datetime, date
import ipywidgets as widgets
from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from IPython.display import display, HTML
from dmyplant2 import (
    cred, MyPlant, FSMOperator, startstopFSM, cplotdef, load_data, get_cycle_data2, get_cycle_data3, count_columns, 
    FSM_splot, FSM_add_Notations, FSM_add_StatesLines, disp_alarms, disp_warnings, FSM_add_Alarms,
    FSM_add_Warnings, bokeh_show, cvset
)
from bokeh.io import push_notebook #, show, output_notebook
from App.common import loading_bar, V, myfigures, mp, tabs_out, status
#from App import tab2

#########################################
# tab4
#########################################
class Tab():
    def __init__(self):

        self.title = '4. Start Plots'
        self.tab4_out = widgets.Output()
        self.pfigsize=V.dfigsize

        self.selected_engine = widgets.Text(
            value='-', description='Selected:', disabled=True, 
            layout=widgets.Layout(width='608px'))

        self.sno = widgets.IntText(
            #description='StartNo: ',
            layout=widgets.Layout(max_width='120px'))

        self.sno_slider = widgets.IntSlider(0, 0, 5 , 1,
            description = 'StartNo:',
            layout=widgets.Layout(width='483px'))
        mylink = widgets.jslink((self.sno, 'value'), (self.sno_slider, 'value'))
        self.sno.observe(self.start_info, 'value')

        self.b_plots = widgets.Button(
            description='Plot',
            disabled=False, 
            button_style='primary')
        self.b_plots.on_click(self.show_plots)

        # self.b_run2 = widgets.Button(
        #     description='FSM 2',
        #     disabled=False, 
        #     tooltip='Run FSM2 Results just for the selected Start', 
        #     button_style='primary')
        # self.b_run2.on_click(self.start_run2)

        self.plot_selection = widgets.SelectMultiple( 
            options=list(myfigures().keys()), 
            value=list(myfigures().keys())[:], 
            rows=min(len(myfigures()),4), 
            disabled=False,
            #description=''
            layout=widgets.Layout(width='100px')
            )

        self.par_data_chkbox = widgets.Checkbox(
            value=True,
            description='Parallel',
            disabled=False,
            indent=False,
            layout=widgets.Layout(width='100px'))

        self.refresh_chkbox = widgets.Checkbox(
            value=False,
            description='Refresh',
            disabled=False,
            indent=False,
            layout=widgets.Layout(width='100px'))

        self.alarms_chkbox = widgets.Checkbox(
            value=True,
            description='Alarms',
            disabled=False,
            indent=False,
            layout=widgets.Layout(width='100px'))

        self.warnings_chkbox = widgets.Checkbox(
            value=True,
            description='Warnings',
            disabled=False,
            indent=False,
            layout=widgets.Layout(width='100px'))

        self.annotations_chkbox = widgets.Checkbox(
            value=True,
            description='Annotations',
            disabled=False,
            indent=False,
            layout=widgets.Layout(width='100px'))

        self.stateslines_chkbox = widgets.Checkbox(
            value=True,
            description='States Lines',
            disabled=False,
            indent=False,
            layout=widgets.Layout(width='100px'))

        self.plotsize_chkbox = widgets.Checkbox(
            value=False,
            description='Big Plot Size',
            disabled=False,
            indent=False,
            layout=widgets.Layout(width='100px'))
        
        #self.start_table = widgets.HTML()
        self.start_table = widgets.Output(
             layout=widgets.Layout(height='100px')
             )

        self.time_range = widgets.IntRangeSlider(
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
        self.time_range.observe(self.start_info,'value')
        self.start_info()

    @property
    def tab(self):
        return VBox([
                    HBox([
                        VBox([
                            HBox([self.b_plots]),
                            HBox([self.selected_engine]),
                            HBox([self.sno_slider, self.sno]),
                            #HBox([self.time_range]),
                        ]),
                        self.plot_selection,
                        VBox([
                            HBox([self.par_data_chkbox, self.alarms_chkbox, self.annotations_chkbox, self.plotsize_chkbox]),
                            HBox([self.refresh_chkbox, self.warnings_chkbox, self.stateslines_chkbox])
                        ])
                    ]),
                    self.start_table,
                    self.tab4_out
                ],layout=widgets.Layout(min_height=V.hh));

    def selected(self):
        if V.fsm is not None: 
            self.selected_engine.value = V.selected
            V.lfigures = myfigures(V.e)
            V.plotdef, V.vset = cplotdef(mp, V.lfigures)
            rdf = V.fsm.starts
            if not rdf.empty:
                if self.sno_slider.max != (rdf.shape[0]-1):
                    self.sno_slider.max = rdf.shape[0]-1
            with tabs_out:
                tabs_out.clear_output()
                print('tab4')

    def calc_time_range(self,sv):
        tns = pd.to_datetime((sv['starttime'].timestamp() + self.time_range.value[0]/100.0 * (sv['endtime']-sv['starttime']).seconds), unit='s')
        tne = pd.to_datetime((sv['starttime'].timestamp() + self.time_range.value[1]/100.0 * (sv['endtime']-sv['starttime']).seconds), unit='s')
        return tns, tne


    def update_fig(self, x=0, lfigures=V.lfigures, plotselection=V.plotdef, vset=V.vset, plot_range=(0,100), debug=False, fsm=V.fsm, VSC=False):
        if V.fsm is None:
            return
        rdfs = V.rdf[V.rdf.no == x]
        if not rdfs.empty:
            if not VSC:
                with tabs_out:
                    tabs_out.clear_output()
                    print(f'tab4 - ⌛ loading data ...')

        startversuch = rdfs.iloc[0]
        status('tab4',f'⌛ Please Wait, loading data for Start No. {startversuch.no}')
        try:
            if self.par_data_chkbox.value:
                # load data using concurrent.futures
                data = get_cycle_data3(fsm, startversuch, cycletime=1, silent=True, p_data=vset, t_range=plot_range, p_refresh=self.refresh_chkbox.value)
            else:
                data = get_cycle_data2(fsm, startversuch, cycletime=1, silent=True, p_data=vset, t_range=plot_range, p_refresh=self.refresh_chkbox.value)

            data['bmep'] = data.apply(lambda x: V.fsm._e._calc_BMEP(x['Power_PowerAct'], V.fsm._e.Speed_nominal), axis=1)
            data['power_diff'] = pd.Series(np.gradient(data['Power_PowerAct']))
            if not VSC:
                tabs_out.clear_output()
            # PLotter
            ftitle = f"{fsm._e} ----- Start {startversuch['no']} {startversuch['mode']} | {startversuch['success']} | {startversuch['starttime'].round('S')}"
            fig_handles = []
            if self.plotsize_chkbox.value:
                self.pfigsize = V.dfigsize_big
            else:
                self.pfigsize = V.dfigsize                
            for doplot in plotselection:

                res2_dict = {
                    'actors':'synchronisation',
                    'tecjet':'tecjet',
                    'exhaust':'exhaust'
                }

                if res2_dict.get(doplot, '') in V.fsm.results['run2_content']:
                    display(HTML(self.html_table(startversuch[V.fsm.results['run2_content'][res2_dict[doplot]]])))
                dset = lfigures[doplot]
                ltitle = f"{ftitle} | {doplot}"
                if count_columns(dset) > 12: # no legend, if too many lines.
                    fig = FSM_splot(fsm, startversuch, data, dset, title=ltitle, legend=False, figsize=self.pfigsize)
                else:
                    fig = FSM_splot(fsm, startversuch, data, dset, title=ltitle, figsize=self.pfigsize)

                if self.annotations_chkbox.value:
                    fig = FSM_add_Notations(fig, fsm, startversuch)
                if self.stateslines_chkbox.value:
                    fig = FSM_add_StatesLines(fig, fsm, startversuch)

                disp_alarms(startversuch)
                disp_warnings(startversuch)
                if self.alarms_chkbox.value:
                    fig = FSM_add_Alarms(fig, fsm, startversuch)
                if self.warnings_chkbox.value:
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
            tabs_out.clear_output()
            print('Error: ', str(err))
            if debug:
                print(traceback.format_exc())

    #@tab4_out.capture(clear_output=True)
    def show_plots(self, but):
        with self.tab4_out:
            self.tab4_out.clear_output()
            self.update_fig(x=self.sno.value, lfigures=V.lfigures, plotselection=self.plot_selection.value, 
                            vset=V.vset, plot_range=self.time_range.value, fsm=V.fsm)

    def html_table(self, result_list):
            table = pd.DataFrame(result_list).T
            return table.style.set_table_styles([
                {'selector':'th,tbody','props':'font-size:0.7rem; font-weight: bold; text-align:center; background-color: #D3D3D3; ' + \
                                        'border: 1px solid black; border-collapse: collapse; margin: 0px; padding: 5px;'},
                {'selector':'td','props':'font-size:0.7rem; text-align:center; min-width: 58px; background-color: #FFFFFF; '}]
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

    def start_info(self,*args):
        if V.fsm is not None:
            rdf = V.fsm.starts
            if not rdf.empty:
                sv = rdf.iloc[self.sno.value]
                ltitle = f" Start No {sv['no']} from: {sv['starttime'].round('S')} to: {sv['endtime'].round('S')}"
                #r = self.html_table(sv[startstopFSM.run2filter_content])
                r = self.html_table(sv[V.fsm.results['run2_content']['startstop']])
                links = 'links to Myplant: | '
                time_new_start, time_new_end = self.calc_time_range(sv)
                for doplot in self.plot_selection.options:
                    ll = V.e.myplant_workbench_link(time_new_start, time_new_end, V.e.get_dataItems(dat=cvset(mp,V.lfigures[doplot])),doplot)
                    links += f'{ll} | '
                #self.start_table.value = links + ltitle + '<br>' + r
                with self.start_table:
                    self.start_table.clear_output()
                    display(HTML(links + ltitle + '<br>' + r))

    # def start_run2(self,b):
    #     if V.fsm is not None:
    #         rdf = V.fsm.starts
    #         if not rdf.empty:
    #             sv = rdf.iloc[self.sno.value]
    #             V.fsm.run2_collectors_setup()
    #             vset, tfrom, tto = V.fsm.run2_collectors_register(sv)
    #             ldata = load_data(V.fsm, cycletime=1, tts_from=tfrom, tts_to=tto, silent=True, p_data=vset, p_forceReload=False, p_suffix='_individual', debug=False)
    #             V.fsm.results = V.fsm.run2_collectors_collect(sv, V.fsm.results, ldata)
    #             phases = list(V.fsm.results['starts'][self.sno]['startstoptiming'].keys())
    #             V.fsm.self.startstopHandler._harvest_timings(V.fsm.results['starts'][self.sno], phases, V.fsm.results)
    #             self.start_info() 
