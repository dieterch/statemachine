from cgitb import html
import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
from pprint import pformat as pf
import ipywidgets as widgets
from IPython.display import display
from ipyfilechooser import FileChooser
from dmyplant2 import cred, MyPlant, FSMOperator, save_json, load_json
from .common import V, init_query_list, get_query_list, save_query_list,mp, tabs_out, tabs_html, status

#cred()
#mp = MyPlant(3600)
#########################################
# tab1
#########################################
class Tab():
    def __init__(self):

        self.title = '1. select Engine'
        self.tab1_out = widgets.Output()

        self.bt_load_testfile = widgets.Button(
            description='Load',
            disabled=False, 
            button_style='')
        self.bt_load_testfile.on_click(self.load_testfile)

        self.fdialog = FileChooser(
            os.getcwd(),
            filename='test.dfsm',
            #title='<b>FileChooser example</b>',
            show_hidden=False,
            select_default=True,
            show_only_dirs=False
        )
        self.fdialog.filter_pattern = '*.dfsm'

        self.query_drop_down = widgets.Combobox(
            value='',
            # placeholder='Choose Someone',
            options=V.query_list,
            description='Site Name:',
            #ensure_option=True,
            disabled=False,
            layout=widgets.Layout(width='600px'))

        self.engine_selections = widgets.Select(
            options=list(), 
            #value='', 
            rows=10, 
            description='Engine:', 
            disabled=False, 
            layout=widgets.Layout(width='600px'))
        self.engine_selections.observe(self.do_selection, 'value')

        self.selected_engine = widgets.Text(
            value='-', 
            description='selected:', 
            disabled=True, 
            layout=widgets.Layout(width='400px'))

        self.selected_engine_number = widgets.Text(
            value='-', 
            description='Motor No:', 
            disabled=True, 
            layout=widgets.Layout(width='200px'))

        self.b_search = widgets.Button(
            description='Lookup',
            disabled=False,
            tooltip = \
        '''- Site Name
        - Engine Type
        - Engine Version
        - Design Number
        - serialNumber
        - assetNumber''',
            button_style='primary')
        self.b_search.on_click(self.search)

        self.b_clear = widgets.Button(
            description='Clear',
            disabled=False, 
            button_style='')
        self.b_clear.on_click(self.clear)


        self.child1 = widgets.HBox([self.bt_load_testfile,self.fdialog])
        self.child2 = widgets.HBox([
                            widgets.VBox([
                                self.query_drop_down,
                                self.engine_selections,
                                widgets.HBox([self.selected_engine,self.selected_engine_number])
                            ]),
                            widgets.VBox([self.b_search,self.b_clear])
                        ])

        self.accordion = widgets.Accordion(
            children=[
                self.child1, 
                self.child2
            ]
        )
        self.accordion.set_title(0,'Work on stored FSM Results')
        self.accordion.set_title(1,'Start Analysis from Installed Fleet')
        self.accordion.observe(self.accordion_change_index, 'selected_index')
        self.accordion.selected_index = 1

    @property
    def tab(self):
        return widgets.VBox([
                        self.accordion,
                        self.tab1_out
                    ],layout=widgets.Layout(min_height=V.hh))


    def selected(self):
        status('tab1')
            
    def do_lookup(self,lookup):
        def sfun(x):
            #return all([ (lookup in str(x['Design Number'])),  (x['OperationalCondition'] != 'Decommissioned') ])
            return (
                (str(lookup).upper() in str(x['IB Site Name']).upper()) or \
                (str(lookup).upper() in str(x['Engine Type']).upper()) or \
                (str(lookup).upper() in str(x['Engine Version']).upper()) or \
                (str(lookup) == str(x['Design Number'])) or \
                (str(lookup) == str(x['serialNumber'])) or \
                (str(lookup) == str(x['id']))) and \
                (x['OperationalCondition'] != 'Decommissioned')

        V.fleet = mp.search_installed_fleet(sfun).drop('index', axis=1)
        V.fleet = V.fleet.sort_values(by = "Engine ID",ascending=True).reset_index(drop='index')
        ddl = [f"{x['serialNumber']}  J{x['Engine Type']} {x['Engine Version']:<4} {x['Engine ID']} {x['IB Site Name']}" for i, x in V.fleet.iterrows()]
        ddl = [m for m in ddl]
        return ddl

    #@tab1_out.capture(clear_output=True)
    def do_selection(self,*args):
        self.selected_engine.value = self.engine_selections.value
        self.selected_engine_number.value = str(list(self.engine_selections.options).index(self.engine_selections.value))
        V.selected = self.selected_engine.value
        V.selected_number = self.selected_engine_number.value
        status('tab1',f'{len(list(self.engine_selections.options))} Engines found - please select an Engine and  move to section 2.')

    #@self.tab1_out.capture(clear_output=True)
    def search(self,but):
        self.tab1_out.clear_output()
        if self.query_drop_down.value != '':
            self.engine_selections.options = self.do_lookup(self.query_drop_down.value)
            #display(HTML(pd.DataFrame.from_dict(e.dash, orient='index').T.to_html(escape=False, index=False)))
            with tabs_out:
                tabs_html.value = V.fleet[:].T \
                    .style \
                    .set_table_styles([
                            {'selector':'th,td','props':'font-size:0.6rem; min-width: 70px; margin: 0px; padding: 0px;'}]
                        ) \
                    .format(
                        precision=0,
                        na_rep='-'
                        ).to_html(escape=False, index=False)
            if ((not self.query_drop_down.value in V.query_list) and (len(self.engine_selections.options) > 0)):
                V.query_list.append(self.query_drop_down.value)
            save_query_list(V.query_list)
        else: 
            status('tab1','please provide a query string.')

    #@tab1_out.capture(clear_output=True)
    def load_testfile(self,but):
        self.tab1_out.clear_output()
        if self.fdialog.selected.endswith('.dfsm'):
            status('tab1', f'⌛ loading {self.fdialog.selected}')
            V.fsm = FSMOperator.load_results(mp, self.fdialog.selected)
            V.e = V.fsm._e
            V.rdf = V.fsm.starts
            self.selected_engine.value = V.selected = V.fsm.results['info']['Name']
            self.selected_engine_number.value = V.selected_number = '0'
            with tabs_out:
                status('tab1')
                display(pd.DataFrame.from_dict(V.fsm.results['info'], orient='index').T.style.hide())
        else:
            status('tab1','please select a *.dfsm File.')

    def clear(self,but):
        self.tab1_out.clear_output()
        self.query_drop_down.value = ''
        self.engine_selections.options = list()
        #engine_selections.value = ''
        self.selected_engine.value = ''
        self.selected_engine_number.value = ''
        tabs_html.value = ''
        V.selected = ''
        V.selected_number = ''
        status('tab1')
        #V.query_list = init_query_list()
        #save_query_list(V.query_list)

#    def status(self,text=''):
#        with tabs_out:
#            tabs_out.clear_output()
#            print(f'tab1{" - " if text != "" else ""}{text}')

    def accordion_change_index(self,*args):
        if self.accordion.selected_index == 0:
            status('tab1','please select a *.dfsm File.')
        elif self.accordion.selected_index == 1:
            status('tab1','please provide a query string.')
