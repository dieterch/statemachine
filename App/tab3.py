import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
from datetime import datetime, date
import ipywidgets as widgets
#from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from IPython.display import display, HTML
from dmyplant2 import cred, MyPlant
from dmyplant2 import FSMOperator, equal_adjust, dbokeh_chart, bokeh_show
from App.common import loading_bar, V, overview_figure, tabs_out, disp_alwr, display_fmt
#from App import tab2

#########################################
# tab3
#########################################
class Tab():
    def __init__(self):

        self.title = '3. Filter Results'
        self.tab3_out = widgets.Output()
        self.el = widgets.Text(
            value='-', 
            description='selected:', 
            disabled=True, 
            layout=widgets.Layout(width='603px')
        )
        
        self.mo = widgets.SelectMultiple( 
            options=['undefined','OFF','MAN','AUTO'], 
            value=V.modes_value, 
            rows=4, 
            description='modes: ', 
            disabled=False,
            layout=widgets.Layout(width='200px'))
        self.mo.observe(self.mo_observe, 'value')

        self.succ = widgets.SelectMultiple( 
            options=['success','failed','undefined'], 
            value=V.succ_value, 
            rows=4, 
            description='success: ', 
            disabled=False,
            layout=widgets.Layout(width='200px'))        
        self.succ.observe(self.succ_observe, 'value')

        self.alarm_warning = widgets.SelectMultiple( 
            options=['-','Alarms','Warnings'], 
            value=['-'], 
            rows=3, 
            description='A/W', 
            disabled=False,
            layout=widgets.Layout(width='200px'))
        self.alarm_warning.observe(self.alarm_warning_observe, 'value')
        
        self.msg_no = widgets.Text(
            value='',
            description='msg no:',
            layout=widgets.Layout(max_width='200px'))

        self.show_only_messages = widgets.Checkbox(
            value=False,
            description="msg's only",
            disabled=False,
            indent=False,
            layout=widgets.Layout(width='100px')
        )

        self.selected_engine = widgets.Text(
            value='-', 
            description='selected:', 
            disabled=True, 
            layout=widgets.Layout(width='603px')
        )


        self.t3_button = widgets.Button(
            description='Overview',
            disabled=False, 
            button_style='primary'
        )
        self.t3_button.on_click(self.show_overview)

    @property
    def tab(self):
        return widgets.VBox(
            [widgets.HBox([self.selected_engine,self.t3_button]), 
            widgets.HBox([self.mo,self.succ,widgets.VBox([self.alarm_warning,self.msg_no]),self.show_only_messages]),
            self.tab3_out],
            layout=widgets.Layout(min_height=V.hh))

    def mo_observe(self,*args):
        V.modes_value = self.mo.value

    def succ_observe(self,*args):
        V.succ_value = self.succ.value

    def alarm_warning_observe(self,*args):
        V.alarm_warning_value = self.alarm_warning.value

    def selected(self):
        self.selected_engine.value = V.selected
        with tabs_out:
            tabs_out.clear_output()
            print('tab3')

    def filter_msg(self, df, mnum):
        return any([m['msg']['name'] == str(mnum) for m in df['alarms']] + [m['msg']['name'] == str(mnum) for m in df['warnings']])

    #@tab3_out.capture(clear_output=True)
    def show_overview(self,b):
        with self.tab3_out:
            if V.fsm is not None:
                self.tab3_out.clear_output()
                self.rda = V.rdf[:].reset_index(drop='index')
                thefilter = (
                    (self.rda['mode'].isin(self.mo.value)) & 
                    (self.rda['success'].isin(self.succ.value)) & 
                    ((self.rda['W'] > 0) | ('Warnings' not in self.alarm_warning.value)) & 
                    ((self.rda['A'] > 0) | ('Alarms' not in self.alarm_warning.value))
                )
                if self.msg_no.value != '':
                    self.rda = self.rda[self.rda.apply(lambda x: self.filter_msg(x, self.msg_no.value), axis=1)] 
                self.rda = self.rda[thefilter].reset_index(drop='index')
                #rdb = rda
                self.rde = self.rda #.fillna('')
                if not self.rde.empty:
                    self.rde['datetime'] = pd.to_datetime(self.rde['starttime'])
                    sdict ={'success':1, 'failed':0, 'undefined':0.5}
                    self.rde['isuccess'] = self.rde.apply(lambda x: sdict[x['success']], axis=1)
                    #vec = ['startpreparation','speedup','idle','synchronize','loadramp','targetload','ramprate','cumstarttime','targetoperation','rampdown','coolrun','runout','isuccess']
                    
                    dfigsize = (20,10)
                    dset = overview_figure()['basic']
                    dset = equal_adjust(dset, self.rde, do_not_adjust=[-1])
                    ftitle = f"{V.fsm._e}"
                    try:
                        fig = dbokeh_chart(self.rde, dset, style='both', figsize=dfigsize ,title=ftitle);
                        print()
                        bokeh_show(fig)
                    except Exception as err:
                        print('\n','no figure to display, Error: ', str(err))

                    vec = V.fsm.results['run2_content']['startstop']
                    display(self.rde[vec].describe()
                                .style
                                .set_table_styles([
                                    {'selector':'table,td,th', 'props': 'font-size: 0.7rem; '}
                                ])
                                .format(
                            precision=0,
                            na_rep='-',
                            formatter={
                                'starter': "{:.1f}",
                                'idle': "{:.1f}",
                                'ramprate':"{:.2f}",
                                'runout': lambda x: f"{x:0.1f}"
                            }
                        ))
                    print()
                    # display(self.rde[['starttime'] + V.fsm.results['run2_content']['startstop']][::-1]
                    #         .style
                    #         .hide()
                    #         .format(
                    #     precision=2,
                    #     na_rep='-',
                    #     formatter={
                    #         'starttime': "{:%Y-%m-%d %H:%M:%S %z}",
                    #         'starter': "{:.1f}",
                    #         'idle': "{:.1f}",
                    #         'ramprate':"{:.2f}",
                    #         'runout': lambda x: f"{x:0.1f}"
                    #     }
                    # ))
                    self.rde['AW'] = self.rde.apply(lambda x: x['A'] + x['W'] > 0, axis=1)
                    self.rde = self.rde[::-1].reset_index()
                    j = 0; k = 0
                    rowgen = self.rde.iterrows()
                    try:
                        while True:
                            i,row = next(rowgen)
                            if row['AW']:
                                if i-k > 0:
                                    if not self.show_only_messages.value:
                                        display_fmt(self.rde.iloc[k:i])
                                if not self.show_only_messages.value:
                                    display_fmt(row.to_frame().T)
                                else:
                                    print('--------------')
                                disp_alwr(row,'alarms')
                                disp_alwr(row,'warnings')
                                k = i + 1
                    except StopIteration:
                        pass

                else:
                    print()
                    print('Empty DataFrame.')
