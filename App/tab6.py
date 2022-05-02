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
# tab6 - playground
#########################################
class Tab():
    def __init__(self):

        self.title = 'Playground'
        self.dfigsize = V.dfigsize
        self.tab6_out = widgets.Output()

        self.b_tecjet = widgets.Button(
            description='TecJet Results',
            disabled=False,
            button_style='primary',
            tooltip='Show TecJet Results collected in Run2',
        )
        self.b_tecjet.on_click(self.show_tecjet)

        self.b_exhaust = widgets.Button(
            description='Exh Temp Results',
            disabled=False,
            button_style='primary',
            tooltip='Show Exhaust Temp Results collected in Run2',
        )
        self.b_exhaust.on_click(self.show_temp)

        self.b_sync = widgets.Button(
            description='Sync Results',
            disabled=False,
            button_style='primary',
            tooltip='Show Snchronization Results collected in Run2',
        )
        self.b_sync.on_click(self.show_sync)

    @property
    def tab(self):
        return widgets.VBox([
            widgets.HBox([self.b_tecjet,self.b_exhaust,self.b_sync]),
            self.tab6_out],
            layout=widgets.Layout(min_height=V.hh))

    def selected(self):
        with tabs_out:
            tabs_out.clear_output()
            print('tab6')

    def show_tecjet(self,b): # tecjet callback
        with self.tab6_out:
            self.tab6_out.clear_output()
            if ((V.fsm is not None) and V.fsm.starts.iloc[0]['run2']):
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
                    {'col':['TJ_GasDiffPressMin'],'ylim': [0, 100], 'color':'orange', 'unit':'mbar'},
                    {'col':['TJ_Pos_at_Min'],'ylim': [0, 100], 'color':'purple', 'unit':'°C'},
                    {'col':['TJ_GasPress1_at_Min'],'ylim': [700, 1200], 'color':'brown', 'unit':'mbar'},
                    {'col':['TJ_GasTemp1_at_Min'],'ylim': [0, 100], 'color':'dodgerblue', 'unit':'°C'},
                    {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.05)'] },
                    ]
                    dr2set2 = equal_adjust(dr2set2, rde, do_not_adjust=['no'], minfactor=0.95, maxfactor=1.2)
                    ftitle = f"{V.fsm._e}"
                    fig2 = dbokeh_chart(rde, dr2set2, style='both', figsize=self.dfigsize ,title=ftitle);
                    bokeh_show(fig2)

                    
                    rde = rde[rde['targetload'] > 0.95 * V.fsm._e['Power_PowerNominal']]
                    rde['bmep'] = rde.apply(lambda x: V.fsm._e._calc_BMEP(x['targetload'], V.fsm._e.Speed_nominal), axis=1)
                    rde['bmep2'] = rde.apply(lambda x: V.fsm._e._calc_BMEP(x['maxload'], V.fsm._e.Speed_nominal), axis=1)
                    dr2set2 = [
                            #{'col':['targetload'],'ylim': [4100, 4700], 'color':'red', 'unit':'kW'},
                            {'col':['bmep2','bmep'],'ylim': [20, 30], 'color':['FireBrick','red'], 'unit':'bar'},
                            {'col':['TJ_GasDiffPressMin'],'ylim': [-20, 80], 'color':'blue', 'unit':'mbar'},
                            {'col':['TJ_Pos_at_Min'],'ylim': [0, 600], 'color':'purple', 'unit':'%'},
                            #{'col':['TJ_GasPress1_at_Min'],'ylim': [800, 1300], 'color':'dodgerblue', 'unit':'mbar'},
                            #{'col':['TJ_GasTemp1_at_Min'],'ylim': [0, 100], 'color':'red', 'unit':'°C'},
                            {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.05)'] },
                            ]
                    dr2set2 = equal_adjust(dr2set2, rde, do_not_adjust=['no'], minfactor=1.0, maxfactor=1.1)
                    ntitle = ftitle + ' | BMEP at Start vs TJ Gas Temperature in °C '
                    fig3 = dbokeh_chart(rde, dr2set2, x='TJ_GasTemp1_at_Min', style='circle', figsize=self.dfigsize ,title=ntitle);
                    fig3.add_layout(Span(location=24.5,
                            dimension='width',x_range_name='default', y_range_name='0',line_color='red', line_dash='dashed', line_alpha=0.6))
                    fig3.add_layout(Span(location=20.0,
                            dimension='width',x_range_name='default', y_range_name='1',line_color='blue', line_dash='dashed', line_alpha=0.6))

                    bokeh_show(fig3)
                    
                    dr2set2 = [
                            #{'col':['targetload'],'ylim': [4100, 4700], 'color':'red', 'unit':'kW'},
                            {'col':['bmep2','bmep'],'ylim': [20, 30], 'color':['FireBrick','red'], 'unit':'bar'},
                            #{'col':['TJ_GasDiffPressMin'],'ylim': [-20, 80], 'color':'blue', 'unit':'mbar'},
                            {'col':['TJ_Pos_at_Min'],'ylim': [0, 600], 'color':'purple', 'unit':'%'},
                            #{'col':['TJ_GasPress1_at_Min'],'ylim': [800, 1300], 'color':'dodgerblue', 'unit':'mbar'},
                            {'col':['TJ_GasTemp1_at_Min'],'ylim': [0, 100], 'color':'dodgerblue', 'unit':'°C'},
                            {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.05)'] },
                            ]
                    dr2set2 = equal_adjust(dr2set2, rde, do_not_adjust=['no'], minfactor=1.0, maxfactor=1.1)
                    ntitle = ftitle + ' | BMEP at Start vs TJ TJ_GasDiffPressMin in mbar '
                    fig3 = dbokeh_chart(rde, dr2set2, x='TJ_GasDiffPressMin', style='circle', figsize=self.dfigsize ,title=ntitle);
                    fig3.add_layout(Span(location=24.5,
                            dimension='width',x_range_name='default', y_range_name='0',line_color='red', line_dash='dashed', line_alpha=0.6))
                    #fig3.add_layout(Span(location=20.0,
                    #        dimension='width',x_range_name='default', y_range_name='1',line_color='blue', line_dash='dashed', line_alpha=0.6))

                    bokeh_show(fig3)            
                    
                print()
                display(rde[V.fsm.results['run2_content']].describe().style.format(precision=2, na_rep='-'))                
                    
                display(rde[V.fsm.results['run2_content']].style.format(precision=2,na_rep='-').hide())
            else:
                print('No Data available.')
    
    def show_temp(self,b): # exhaust callback
        with self.tab6_out:
            self.tab6_out.clear_output()
            if ((V.fsm is not None) and V.fsm.starts.iloc[0]['run2']):
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
                #'ExhTempCylMax','ExhSpread_at_Max','Power_at_ExhTempCylMax'
                if not rde.empty:
                    rde['datetime'] = pd.to_datetime(rde['starttime'])
                    dr2set3 = [
                            {'col':['ExhTempCylMax'],'_ylim': [4200, 4800], 'color':'red', 'unit':'°C'},
                            {'col':['ExhSpreadMax','ExhSpread_at_Max'],'_ylim': [0, 100], 'color':['dodgerblue','blue'], 'unit':'°C'},
                            {'col':['Power_at_ExhTempCylMax'],'_ylim': [0, 100], 'color':'orange', 'unit':'kW'},
                            {'col':['synchronize'],'_ylim':(-20,400), 'color':'brown', 'unit':'sec'},
                            {'col':['startpreparation'],'_ylim':(-1000,800), 'unit':'sec'},
                            {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.05)'] },
                            ]
                    dr2set3 = equal_adjust(dr2set3, rde, do_not_adjust=[5], minfactor=0.95, maxfactor=1.2)
                    ntitle = f"{V.fsm._e}" + ' | Exhaust Temperture at Start, Max, Min & Spread.'
                    fig4 = dbokeh_chart(rde, dr2set3, style='both', figsize=self.dfigsize ,title=ntitle);
                    bokeh_show(fig4)

                    print()
                    display(rde[['no','ExhTempCylMax','ExhSpreadMax','ExhSpread_at_Max','Power_at_ExhTempCylMax']].describe()
                                .style.format(precision=2, na_rep='-'))            

                    print()
                    display(rde[['no','ExhTempCylMax','ExhSpreadMax','ExhSpread_at_Max','Power_at_ExhTempCylMax']]
                                .style.format(precision=2,na_rep='-').hide())
            else:
                print('No Data available.')

    def show_sync(self,b): # synch callback
        with self.tab6_out:
            self.tab6_out.clear_output()
            if ((V.fsm is not None) and V.fsm.starts.iloc[0]['run2']):
                rda = V.fsm.starts.reset_index(drop='index')
                thefilter = (
                    (rda['mode'].isin(V.modes_value)) & 
                    (rda['success'].isin(V.succ_value)) & 
                    ((rda['W'] > 0) | ('Warnings' not in V.alarm_warning_value)) & 
                    ((rda['A'] > 0) | ('Alarms' not in V.alarm_warning_value))
                )
                rda = rda[thefilter].reset_index(drop='index')
                global rdb
                rdb = rda
                rde = rda #.fillna('')
                # ['rpm_dmax','rpm_dmin','rpm_spread', 'Lambda_rpm_max', 'TempOil_rpm_max', 'TempCoolWat_rpm_max']
                if not rde.empty:
                    rde['datetime'] = pd.to_datetime(rde['starttime'])
                    dr2set3 = [
                        {'col':['rpm_dmax'],'_ylim': [4200, 4800], 'color':'red', 'unit':'rpm'},
                        {'col':['rpm_dmin'],'_ylim': [0, 100], 'color':'blue', 'unit':'rpm'},
                        {'col':['rpm_spread'],'_ylim': [0, 100], 'color':'orange', 'unit':'rpm'},
                        {'col':['synchronize'],'_ylim':(-20,400), 'color':'brown', 'unit':'sec'},
                        {'col':['Lambda_rpm_max'],'_ylim': [0, 100], 'color':'purple', 'unit':'a/f'},
                        #{'col':['TempOil_rpm_max','TempCoolWat_rpm_max'],'_ylim': [0, 100], 'color':['crimson','dodgerblue'], 'unit':'mbar'},
                        {'col':['TempOil_rpm_max'],'_ylim': [0, 100], 'color':'crimson', 'unit':'°C'},
                        {'col':['TempCoolWat_rpm_max'],'_ylim': [0, 100], 'color':'dodgerblue', 'unit':'-'},
                        {'col':['W'],'_ylim':(-1,200), 'color':['rgba(255,165,0,0.3)'] },
                        {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.05)'] }
                    ]
                    dr2set3 = equal_adjust(dr2set3, rde, do_not_adjust=['no'], minfactor=0.95, maxfactor=1.2)
                    ntitle = f"{V.fsm._e}" + ' | Speed Max, Min & Spread between Speedmax and GC On'
                    fig4 = dbokeh_chart(rde, dr2set3, style='both', figsize=self.dfigsize ,title=ntitle);
                    bokeh_show(fig4)

                    dr2set3 = [
                        {'col':['rpm_dmax'],'_ylim': [4200, 4800], 'color':'red', 'unit':'rpm'},
                        {'col':['rpm_dmin'],'_ylim': [0, 100], 'color':'blue', 'unit':'rpm'},
                        {'col':['rpm_spread'],'_ylim': [0, 100], 'color':'orange', 'unit':'rpm'},
                        {'col':['synchronize'],'_ylim':(-20,400), 'color':'brown', 'unit':'sec'},
                        {'col':['Lambda_rpm_max'],'_ylim': [0, 100], 'color':'purple', 'unit':'a/f'},
                        #{'col':['TempOil_rpm_max','TempCoolWat_rpm_max'],'_ylim': [0, 100], 'color':['crimson','dodgerblue'], 'unit':'mbar'},
                        #{'col':['TempOil_rpm_max'],'_ylim': [0, 100], 'color':'crimson', 'unit':'mbar'},
                        {'col':['TempCoolWat_rpm_max'],'_ylim': [0, 100], 'color':'dodgerblue', 'unit':'°C'},
                        {'col':['W'],'_ylim':(-1,200), 'color':['rgba(255,165,0,0.3)'] },
                        {'col':['no'],'_ylim':(0,1000), 'color':['rgba(0,0,0,0.05)'] },
                    ]
                    dr2set3 = equal_adjust(dr2set3, rde, do_not_adjust=['no'], minfactor=0.95, maxfactor=1.2)
                    ntitle = f"{V.fsm._e}" + ' | Speed Max, Min & Spread between Speedmax and GC On'
                    fig4 = dbokeh_chart(rde, dr2set3, x='TempOil_rpm_max', style='circle', figsize=self.dfigsize ,title=ntitle);
                    bokeh_show(fig4)


                    print()
                    display(rde[['rpm_dmax','rpm_dmin','rpm_spread', 'Lambda_rpm_max', 'TempOil_rpm_max', 'TempCoolWat_rpm_max']].describe()
                                .style.format(precision=2, na_rep='-'))
                    print()
                    display(rde[['no','rpm_dmax','rpm_dmin','rpm_spread', 'Lambda_rpm_max', 'TempOil_rpm_max', 'TempCoolWat_rpm_max']]
                                .style.format(precision=2,na_rep='-').hide())
            else:
                print('No Data available.')

