from cgitb import html
import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
from pprint import pformat as pf
import ipywidgets as widgets
from IPython.display import display
from ipyfilechooser import FileChooser
from dmyplant2 import cred, MyPlant, FSMOperator
from .common import V, init_query_list, get_query_list, save_query_list, tabs_out, tabs_html

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

#@tab1_out.capture(clear_output=True)
def do_selection(*args):
    selected_engine.value = engine_selections.value
    selected_engine_number.value = str(list(engine_selections.options).index(engine_selections.value))
    V.selected = selected_engine.value
    V.selected_number = selected_engine_number.value
    with tabs_out:
        tabs_out.clear_output()
        print(f'tab1 - {len(list(engine_selections.options))} Engines found - please select an Engine and  move to section 2.')

@tab1_out.capture(clear_output=True)
def search(but):
    if query_drop_down.value != '':
        engine_selections.options = do_lookup(query_drop_down.value)
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
        if not query_drop_down.value in V.query_list:
            V.query_list.append(query_drop_down.value)
        save_query_list(V.query_list)
    else:
        with tabs_out:
            tabs_out.clear_output()     
            print('tab1 - please provide a query string.')

@tab1_out.capture(clear_output=True)
def load_testfile(but):
    if fdialog.selected.endswith('.dfsm'):
        status(f'loading {fdialog.selected}')
        V.fsm = FSMOperator.load_results(mp, fdialog.selected)
        V.e = V.fsm._e
        V.rdf = V.fsm.starts
        selected_engine.value = V.fsm.results['info']['Name']
        selected_engine_number.value = '0'
        with tabs_out:
            status('')
            display(pd.DataFrame.from_dict(V.fsm.results['info'], orient='index').T.style.hide())
    else:
        with tabs_out:
            tabs_out.clear_output()
            print('tab1 - please select a *.dfsm File.')

def clear(but):
    tab1_out.clear_output()
    tabs_html.value = '<hr>'
    status()
    #V.query_list = init_query_list()
    #save_query_list(V.query_list)

def status(text=''):
    with tabs_out:
        tabs_out.clear_output()
        print(f'tab1{" - " if text != "" else ""}{text}')

def accordion_change_index(*args):
    if accordion.selected_index == 0:
        status('please select a *.dfsm File.')
    elif accordion.selected_index == 1:
        status('please provide a query string.')

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
    filename='test.dfsm',
    #title='<b>FileChooser example</b>',
    show_hidden=False,
    select_default=True,
    show_only_dirs=False
)
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
engine_selections.observe(do_selection, 'value')

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
accordion.observe(accordion_change_index, 'selected_index')
accordion.selected_index = 1

_tab = widgets.VBox([
                accordion,
                tab1_out
            ],layout=widgets.Layout(min_height=V.hh))
