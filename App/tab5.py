import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
from datetime import datetime, date
import ipywidgets as widgets
from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from IPython.display import display
from dmyplant2 import cred, MyPlant
from dmyplant2 import FSMOperator, cplotdef #, Engine
from App.common import loading_bar, V, myfigures, el, mp

#########################################
# tab5
#########################################
tab5_out = widgets.Output()

@tab5_out.capture(clear_output=True)
def do_refresh(but):
    print()
    print('Please Wait ...')
    display(loading_bar)
    mp._fetch_installed_base(); # refresh local installed fleet database
    tab5_out.clear_output()

@tab5_out.capture(clear_output=True)
def do_lookupDI(b):
    lookup = txt_lookup.value
    def sfun(x):
        return (
            (str(lookup).upper() in str(x['id']).upper()) or \
            (str(lookup).upper() in str(x['name']).upper()) or \
            (str(lookup).upper() in str(x['unit']).upper()) or \
            ((str(lookup).upper() in str(x['myPlantName']).upper() and txt_lookup_chbx.value)))
    df = MyPlant.get_dataitems()
    df = df[df.apply(lambda x: sfun(x), axis=1)].reset_index()
    if txt_lookup_exclude.value != '':
        lookup = txt_lookup_exclude.value
        df = df[~df.apply(lambda x: sfun(x), axis=1)].reset_index()
    display(df.style.hide())

@tab5_out.capture(clear_output=True)
def do_save_messages(but):
    if V.fsm is not None:
        if '_messages' in V.fsm.__dict__:
            print()
            print('Please Wait ...')
            display(loading_bar)
            mfn = V.e._fname + '_messages.txt'
            print(f'saving messages to {mfn}')
            V.fsm.save_messages(mfn)
            tab5_out.clear_output()
        else:
            print()
            print('Please Select an Engine and load messages first.')
    
###############
# tab5 widgets
###############

txt_lookup = widgets.Text(
    value='',
    placeholder='Type id, name, unit or MyplantName of a DataItem',
    description='DataItem:',
    disabled=False,
    layout=widgets.Layout(width='400px')
)
txt_lookup_exclude = widgets.Text(
    value='',
    placeholder='Exclude DataItem',
    description='Exclude:',
    disabled=False,
    layout=widgets.Layout(width='400px')
)
txt_lookup_chbx = widgets.Checkbox(
    value=False,
    description='search in MyplantName',
    disabled=False,
    indent=False
)
lookup_button = Button(
    description='Lookup DataItems',
    disabled=False,
    button_style='primary',
    tooltip='Lookup DataItems by id, name, unit or MyplantName',
    icon='question-circle' # (FontAwesome names without the `fa-` prefix)
)
lookup_button.on_click(do_lookupDI)

reload_button = Button(
    description='Refresh Installed Base',
    disabled=False,
    button_style='',
    tooltip='Refresh Installed Base Database',
    icon='refresh', # (FontAwesome names without the `fa-` prefix)
)
reload_button.on_click(do_refresh)

save_messages = Button(
    description='Save All Messages',
    disabled=False,
    button_style='',
    tooltip='Store all messages into the engine data Folder',
    icon='floppy-disk', # (FontAwesome names without the `fa-` prefix)
)
save_messages.on_click(do_save_messages)

spacer = HTML(
    value="<hr>",
    placeholder='',
    description='',
)

_tab = VBox([HBox([reload_button,save_messages]),spacer,HBox([txt_lookup, txt_lookup_exclude, lookup_button, txt_lookup_chbx]), tab5_out])