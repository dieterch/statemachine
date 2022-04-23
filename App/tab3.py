import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
from datetime import datetime, date
import ipywidgets as widgets
#from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from IPython.display import display
from dmyplant2 import cred, MyPlant
from dmyplant2 import FSMOperator, equal_adjust, dbokeh_chart, bokeh_show
from App.common import loading_bar, V, overview_figure
from App import tab2

#########################################
# tab3
#########################################
tab3_out = widgets.Output()
el = widgets.Text(value='-', description='selected:', disabled=True, layout=widgets.Layout(width='603px'))
mo = widgets.SelectMultiple( options=['undefined','OFF','MAN','AUTO'], value=['MAN','AUTO'], rows=4, description='modes: ', disabled=False)
succ = widgets.SelectMultiple( options=['success','failed','undefined'], value=['success'], rows=3, description='success: ', disabled=False)
alarm_warning = widgets.SelectMultiple( options=['-','Alarms','Warnings'], value=['-'], rows=3, description='A&W: ', disabled=False)

@tab3_out.capture(clear_output=True)
def show_overview(b):
    rda = V.rdf[:].reset_index(drop='index')
    thefilter = (
        (rda['mode'].isin(mo.value)) & 
        (rda['success'].isin(succ.value)) & 
        ((rda['count_warnings'] > 0) | ('Warnings' not in alarm_warning.value)) & 
        ((rda['count_alarms'] > 0) | ('Alarms' not in alarm_warning.value))
    )
    rda = rda[thefilter].reset_index(drop='index')
    #rdb = rda
    rde = rda #.fillna('')
    if not rde.empty:
        rde['datetime'] = pd.to_datetime(rde['starttime'])
        sdict ={'success':1, 'failed':0, 'undefined':0.5}
        rde['isuccess'] = rde.apply(lambda x: sdict[x['success']], axis=1)
        #vec = ['startpreparation','speedup','idle','synchronize','loadramp','targetload','ramprate','cumstarttime','targetoperation','rampdown','coolrun','runout','isuccess']
        vec = V.fsm.results['run2_content']
        display(rde[vec].describe()
                    .style
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
        
        dfigsize = (20,10)
        dset = overview_figure()['basic']
        dset = equal_adjust(dset, rde, do_not_adjust=[-1])
        ftitle = f"{V.fsm._e}"
        try:
            fig = dbokeh_chart(rde, dset, style='both', figsize=dfigsize ,title=ftitle);
            print()
            bokeh_show(fig)
        except Exception as err:
            print('\n','no figure to display, Error: ', str(err))

        print()
        #display(rde[startstopFSM.run2filter_content]
        display(rde[V.fsm.results['run2_content']]
                .style
                .hide()
                .format(
            precision=2,
            na_rep='-',
            formatter={
                'starter': "{:.1f}",
                'idle': "{:.1f}",
                'ramprate':"{:.2f}",
                'runout': lambda x: f"{x:0.1f}"
            }
        ))
    else:
        print()
        print('Empty DataFrame.')

###############
# tab3 widgets
###############
t3_button = widgets.Button(description='Overview',disabled=False, button_style='primary')
t3_button.on_click(show_overview)
_tab = widgets.VBox([widgets.HBox([tab2.el,t3_button]), widgets.HBox([mo,succ,alarm_warning]),tab3_out])