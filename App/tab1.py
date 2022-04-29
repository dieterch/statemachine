import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
from pprint import pformat as pf
import ipywidgets as widgets
from IPython.display import display
from ipyfilechooser import FileChooser
from dmyplant2 import cred, MyPlant, FSMOperator
from .common import V, init_query_list, get_query_list, save_query_list, tabs_out

cred()
mp = MyPlant(3600)
#########################################
# tab1
#########################################
tab1_out = widgets.Output()

def selected():
    with tabs_out:
        tabs_out.clear_output()
        print('tab1')
        pass
            #init_globals()
            #tab1.sel.value = '-'
            #tab1.selno.value = '-'
            #tab1.tdd.value = ''
            #tab1.tdd.options = V.query_list
            #tab1.es.options = ['-']

            #tab2.tab2_out.clear_output()
            #tab3.tab3_out.clear_output()
            #tab4.tab4_out.clear_output()
            #tab2.b_runfsm.button_style=''
            #tab2.b_runfsm.disabled = True
            #tab2.b_loadfsm.disabled = True
            #tab2.b_loadfsm.button_style = ''
            
            
def do_lookup(lookup):
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

@tab1_out.capture(clear_output=True)
def do_sel(*args):
    selected_engine.value = engine_selections.value
    selected_engine_number.value = str(list(engine_selections.options).index(engine_selections.value))
    V.selected = selected_engine.value
    V.selected_number = selected_engine_number.value
    print()
    print(f"{len(list(engine_selections.options))} Engines found.")
    print()
    print('please select an Engine and  move to section 2.')

@tab1_out.capture(clear_output=True)
def search(but):
    if query_drop_down.value != '':
        engine_selections.options = do_lookup(query_drop_down.value)
        display(V.fleet[:20].T
            .style
            .set_table_styles([
                    {'selector':'th,tbody','props':'font-size:0.5rem; font-weight: bold; text-align:left; ' + \
                                            'border: 0px solid black; border-collapse: collapse; margin: 0px; padding: 0px;'},
                    {'selector':'td','props':'font-size:0.7rem; text-align:left; min-width: 30px; '}]
                )
            .format(
                precision=2,
                na_rep='-'
            ))
        if not query_drop_down.value in V.query_list:
            V.query_list.append(query_drop_down.value)
        save_query_list(V.query_list)
    else:
        print()
        print('please provide a query string.')

@tab1_out.capture(clear_output=True)
def load_testfile(but):
    if fdialog.selected.endswith('.dfsm'):
        print()
        print('please wait ...')
        V.fsm = FSMOperator.load_results(mp, fdialog.selected)
        V.e = V.fsm._e
        V.rdf = V.fsm.starts
        selected_engine.value = V.fsm.results['info']['Name']
        selected_engine_number.value = '0'
        tab1_out.clear_output()
        print(pf(V.fsm.results['info']))
    else:
        print()
        print('Please select a *.dfsm File.')

def clear(but):
    tab1_out.clear_output()
    #V.query_list = init_query_list()
    #save_query_list(V.query_list)
    
        
###############
# tab1 widgets
###############

bt_load_testfile = widgets.Button(
    description='Load',
    disabled=False, 
    button_style='')
bt_load_testfile.on_click(load_testfile)

fdialog = FileChooser(
    os.getcwd(),
    #filename='test.dfsm',
    #title='<b>FileChooser example</b>',
    show_hidden=False,
    select_default=True,
    show_only_dirs=False
)
#fdialog.title = '<b>Select FSM Result File</b>'
fdialog.filter_pattern = '*.dfsm'

query_drop_down = widgets.Combobox(
    value='',
    # placeholder='Choose Someone',
    options=V.query_list,
    description='Site Name:',
    #ensure_option=True,
    disabled=False,
    layout=widgets.Layout(width='600px'))

engine_selections = widgets.Select(
    options=['-'], 
    value='-', 
    rows=10, 
    description='Engine:', 
    disabled=False, 
    layout=widgets.Layout(width='600px'))
engine_selections.observe(do_sel, 'value')

selected_engine = widgets.Text(
    value='-', 
    description='selected:', 
    disabled=True, 
    layout=widgets.Layout(width='400px'))

selected_engine_number = widgets.Text(
    value='-', 
    description='Motor No:', 
    disabled=True, 
    layout=widgets.Layout(width='200px'))

b_search = widgets.Button(
    description='Lookup',
    disabled=False, 
    button_style='primary')
b_search.on_click(search)

b_clear = widgets.Button(
    description='Clear',
    disabled=False, 
    button_style='')
b_clear.on_click(clear)


child1 = widgets.HBox([bt_load_testfile,fdialog])
child2 = widgets.HBox([
                    widgets.VBox([
                        query_drop_down,
                        engine_selections,
                        widgets.HBox([selected_engine,selected_engine_number])
                    ]),
                    widgets.VBox([b_search,b_clear])
                ])

accordion = widgets.Accordion(
    children=[
        child1, 
        child2
    ]
)
accordion.set_title(0,'Select FSM Result File')
accordion.set_title(1,'Start Analysis from Installed Fleet')
accordion.selected_index = 1


_tab = widgets.VBox([
                accordion,
                tab1_out
            ],layout=widgets.Layout(min_height=V.hh))
