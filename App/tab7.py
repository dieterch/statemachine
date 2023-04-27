import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
from datetime import datetime, date
import ipywidgets as widgets
#from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from bokeh.models import Span
from IPython.display import display
from dmyplant2 import cred, MyPlant, equal_adjust, dbokeh_chart, bokeh_show
from dmyplant2 import FSMOperator, cplotdef #, Engine
from App.common import loading_bar, V, tabs_out

#########################################
# tab7 - playground
#########################################
class Tab():
    def __init__(self):

        self.title = '7. Run4 Results'
        self.dfigsize = V.dfigsize
        self.tab7_out = widgets.Output()

        self.cb_loadcap = widgets.Checkbox(
            value=True,
            description='forget starts with power below',
            disabled=False,
            indent=False,
            layout=widgets.Layout(max_width='220px')
        )

        self.t_loadcap = widgets.IntText(
            #description='%:',
            value=95,
            layout=widgets.Layout(max_width='120px')
        )

        self.t_loadcaplabel = widgets.Label(
            value="%"
        )

        self.b_stop = widgets.Button(
            description='Stop Results',
            disabled=False,
            button_style='primary',
            tooltip='Show Stop Results collected in Run4',
        )
        self.b_stop.on_click(self.show_stop)

    @property
    def tab(self):
        return widgets.VBox([
            widgets.HBox([self.cb_loadcap, self.t_loadcap, self.t_loadcaplabel]),
            widgets.HBox([self.b_stop]),
            self.tab7_out],
            layout=widgets.Layout(min_height=V.hh))

    def selected(self):
        with tabs_out:
            tabs_out.clear_output()
            print('tab7')

    def show_stop(self,b): # stop callback
        with self.tab7_out:
            self.tab7_out.clear_output()
            if ((V.fsm is not None) and V.fsm.starts.iloc[0]['run4']):
                rda = V.fsm.starts.reset_index(drop='index')
                thefilter = (
                    (rda['mode'].isin(V.modes_value)) & 
                    (rda['success'].isin(V.succ_value)) & 
                    ((rda['W'] > 0) | ('Warnings' not in V.alarm_warning_value)) & 
                    ((rda['A'] > 0) | ('Alarms' not in V.alarm_warning_value))
                )
                rda = rda[thefilter].reset_index(drop='index')
                #rdb = rda
                rde = rda #.fillna('')
                if not rde.empty:
                    rde['datetime'] = pd.to_datetime(rde['starttime'])
                    dr2set2 = [
                    {'col':['maxload','targetload'],'ylim': [4200, 5000], 'color':['FireBrick','red'], 'unit':'kW'},
                    {'col':['Stop_Overspeed'],'ylim': [0, 2000], 'color':'blue', 'unit':'rpm'},
                    {'col':['Stop_Throttle'],'ylim': [0, 10], 'color':'gray', 'unit':'%'},
                    {'col':['Stop_PVKDifPress'],'ylim': [0, 100], 'color':'purple', 'unit':'mbar'},
                    {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.05)'] },
                    ]
                    
                    #Checken, ob run2 Resultate im den Daten vorhanden sind und dr2set2 entsprechend anpassen
                    dr2set2_c = [r for r in dr2set2 if all(res in list(V.fsm.starts.columns) for res in r['col'])]
 
                    dr2set2 = equal_adjust(dr2set2_c, rde, do_not_adjust=['no'], minfactor=0.95, maxfactor=1.2)
                    ftitle = f"{V.fsm._e}"
                    fig2 = dbokeh_chart(rde, dr2set2, style='both', figsize=self.dfigsize ,title=ftitle);
                    bokeh_show(fig2)

                    
                    if self.cb_loadcap.value:
                        rde = rde[rde['targetload'] > self.t_loadcap.value / 100 * V.fsm._e['Power_PowerNominal']]
                    rde['bmep'] = rde.apply(lambda x: V.fsm._e._calc_BMEP(x['targetload'], V.fsm._e.Speed_nominal), axis=1)
                    rde['bmep2'] = rde.apply(lambda x: V.fsm._e._calc_BMEP(x['maxload'], V.fsm._e.Speed_nominal), axis=1)
                    dr2set2 = [
                            #{'col':['targetload'],'ylim': [4100, 4700], 'color':'red', 'unit':'kW'},
                            {'col':['bmep2','bmep'],'ylim': [20, 30], 'color':['FireBrick','red'], 'unit':'bar'},
                            {'col':['Stop_Overspeed'],'ylim': [0, 2000], 'color':'blue', 'unit':'rpm'},
                            {'col':['Stop_Throttle'],'ylim': [0, 10], 'color':'gray', 'unit':'%'},
                            {'col':['Stop_PVKDifPress'],'ylim': [0, 100], 'color':'purple', 'unit':'mbar'},
                            {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.05)'] },
                            ]
                    try:
                        dr2set2 = equal_adjust(dr2set2, rde, do_not_adjust=['no'], minfactor=1.0, maxfactor=1.1)
                    except Exception as err:
                        print(f'Error: {str(err)}')
                    ntitle = ftitle + ' | BMEP at Start vs TJ Gas Temperature in °C '
                    fig3 = dbokeh_chart(rde, dr2set2, x='TJ_GasTemp1_at_Min', style='circle', figsize=self.dfigsize ,title=ntitle);
                    fig3.add_layout(Span(location=V.fsm._e.BMEP,
                            dimension='width',x_range_name='default', y_range_name='0',line_color='red', line_dash='dashed', line_alpha=0.6))
                    fig3.add_layout(Span(location=20.0,
                            dimension='width',x_range_name='default', y_range_name='1',line_color='blue', line_dash='dashed', line_alpha=0.6))

                    bokeh_show(fig3)
                    
                    dr2set2 = [
                            {'col':['targetload'],'ylim': [4100, 4700], 'color':'red', 'unit':'kW'},
                            {'col':['bmep2','bmep'],'ylim': [20, 30], 'color':['FireBrick','red'], 'unit':'bar'},
                            {'col':['Stop_Overspeed'],'ylim': [0, 2000], 'color':'blue', 'unit':'rpm'},
                            {'col':['Stop_Throttle'],'ylim': [0, 10], 'color':'gray', 'unit':'%'},
                            {'col':['Stop_PVKDifPress'],'ylim': [0, 100], 'color':'purple', 'unit':'mbar'},
                            {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.05)'] },
                            ]
                    try:
                        #Check, ob run2 Resultate im den Daten vorhanden sind und dr2set2 entsprechend anpassen
                        dr2set2_c = [r for r in dr2set2 if all(res in list(V.fsm.starts.columns) for res in r['col'])]
                        dr2set2 = equal_adjust(dr2set2_c, rde, do_not_adjust=['no'], minfactor=1.0, maxfactor=1.1)
                    except Exception as err:
                        print(f'Error: {str(err)}')
                        
                    ntitle = ftitle + ' | BMEP at Start vs TJ TJ_GasDiffPressMin in mbar '
                    fig3 = dbokeh_chart(rde, dr2set2, x='TJ_GasDiffPressMin', style='circle', figsize=self.dfigsize ,title=ntitle);
                    fig3.add_layout(Span(location=V.fsm._e.BMEP,
                            dimension='width',x_range_name='default', y_range_name='0',line_color='red', line_dash='dashed', line_alpha=0.6))
                    #fig3.add_layout(Span(location=20.0,
                    #        dimension='width',x_range_name='default', y_range_name='1',line_color='blue', line_dash='dashed', line_alpha=0.6))

                    bokeh_show(fig3)            
                    
                print()
                display(rde[V.fsm.results['run4_content']['stop']].describe().style.format(precision=2, na_rep='-'))                
                print()
                display(rde[V.fsm.results['run4_content']['stop']][::-1].style.format(precision=2,na_rep='-').hide())
            else:
                print('No Data available.')