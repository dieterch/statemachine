import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
from datetime import datetime, date
import ipywidgets as widgets
from ipywidgets import AppLayout, Button, Text, Select, Tab, Layout, VBox, HBox, Label, HTML, interact, interact_manual, interactive, IntSlider, Output
from IPython.display import display
from dmyplant2 import cred, MyPlant
from dmyplant2 import FSMOperator, cplotdef #, Engine
from App.common import loading_bar, V, mp, tabs_out

#########################################
# tab5
#########################################
class Tab():
    def __init__(self):

        self.title = '5. settings'
        self.tab5_out = widgets.Output()

        self.txt_lookup = widgets.Text(
            value='',
            placeholder='Type id, name, unit or MyplantName of a DataItem',
            description='DataItem:',
            disabled=False,
            layout=widgets.Layout(width='400px')
        )

        self.txt_lookup_exclude = widgets.Text(
            value='',
            placeholder='Exclude DataItem',
            description='Exclude:',
            disabled=False,
            layout=widgets.Layout(width='400px')
        )
        self.txt_lookup_chbx = widgets.Checkbox(
            value=False,
            description='search in MyplantName',
            disabled=False,
            indent=False
        )
        self.lookup_button = Button(
            description='Lookup DataItems',
            disabled=False,
            button_style='primary',
            tooltip='Lookup DataItems by id, name, unit or MyplantName',
            icon='question-circle' # (FontAwesome names without the `fa-` prefix)
        )
        self.lookup_button.on_click(self.do_lookupDI)

        self.reload_button = Button(
            description='Refresh Installed Base',
            disabled=False,
            button_style='',
            tooltip='Refresh Installed Base Database',
            icon='refresh', # (FontAwesome names without the `fa-` prefix)
        )
        self.reload_button.on_click(self.do_refresh)

        self.save_messages = Button(
            description='Save All Messages',
            disabled=False,
            button_style='',
            tooltip='Store all messages into the engine data Folder',
            icon='floppy-disk', # (FontAwesome names without the `fa-` prefix)
        )
        self.save_messages.on_click(self.do_save_messages)
        
        self.b_fsm_diagrams = Button(
            description='Save State Diagrams',
            disabled=False,
            button_style='',
            tooltip='Save GraphViz dot State Diagrams on all currently implemented Finite State Machines',
            icon='<file-export', # (FontAwesome names without the `fa-` prefix)
        )
        self.b_fsm_diagrams.on_click(self.do_save_dotfiles)

        self.spacer = HTML(
            value="<hr>",
            placeholder='',
            description='',
        )

    @property
    def tab(self):
        return VBox(
            [HBox([self.reload_button,self.save_messages,self.b_fsm_diagrams]),
            self.spacer,
            HBox([self.txt_lookup, self.txt_lookup_exclude, self.lookup_button, self.txt_lookup_chbx]),
            self.tab5_out],
            layout=widgets.Layout(min_height=V.hh))

    def selected(self):
        with tabs_out:
            tabs_out.clear_output()
            print('tab5')

    #@tab5_out.capture(clear_output=True)
    def do_refresh(self,but):
        with tabs_out:
            tabs_out.clear_output()
            print('tab5 - ⌛ refresh installed fleet.')
            mp._fetch_installed_base(); # refresh local installed fleet database
            tabs_out.clear_output()

    #@tab5_out.capture(clear_output=True)
    def do_lookupDI(self,b):
        with self.tab5_out:
            self.tab5_out.clear_output()
            lookup = self.txt_lookup.value
            def sfun(x):
                return (
                    (str(lookup).upper() in str(x['id']).upper()) or \
                    (str(lookup).upper() in str(x['name']).upper()) or \
                    (str(lookup).upper() in str(x['unit']).upper()) or \
                    ((str(lookup).upper() in str(x['myPlantName']).upper() and self.txt_lookup_chbx.value)))
            df = MyPlant.get_dataitems()
            df = df[df.apply(lambda x: sfun(x), axis=1)].reset_index()
            if self.txt_lookup_exclude.value != '':
                lookup = self.txt_lookup_exclude.value
                df = df[~df.apply(lambda x: sfun(x), axis=1)].reset_index()
            display(df.style.hide())

    #@tab5_out.capture(clear_output=True)
    def do_save_messages(self, but):
        with self.tab5_out:
            self.tab5_out.clear_output()
            if V.fsm is not None:
                if '_messages' in V.fsm.__dict__:
                    print()
                    print('Please Wait ...')
                    display(loading_bar)
                    mfn = V.e._fname + '_messages.txt'
                    print(f'saving messages to {mfn}')
                    V.fsm.save_messages(mfn)
                    self.tab5_out.clear_output()
                else:
                    print()
                    print('Please Select an Engine and load messages first.')

    def do_save_dotfiles(self, but):
        with self.tab5_out:
            self.tab5_out.clear_output()
            if V.fsm is not None:
                V.fsm.save_docu()
            else:
                print()
                print('Please Select an Engine and load messages first.')
