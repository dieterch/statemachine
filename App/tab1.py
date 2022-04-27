import os
import pickle
import pandas as pd; pd.options.mode.chained_assignment = None
import ipywidgets as widgets
from IPython.display import display
from dmyplant2 import cred, MyPlant
from .common import V, get_query_list, save_query_list

cred()
mp = MyPlant(3600)
#########################################
# tab1
#########################################
tab1_out = widgets.Output()

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
    sel.value = es.value
    selno.value = str(list(es.options).index(es.value))
    print()
    print(f"{len(list(es.options))} Engines found.")
    print()
    print('please select an Engine and  move to section 2.')

@tab1_out.capture(clear_output=True)
def sbcb(but):
    elst = do_lookup(tdd.value)
    es.options = elst
    # es.value = elst[0]
    print()
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
        ).
        hide())
    if not tdd.value in V.query_list:
        V.query_list.append(tdd.value)
    save_query_list(V.query_list)
        
###############
# tab1 widgets
###############
tdd = widgets.Combobox(
    value='',
    # placeholder='Choose Someone',
    options=V.query_list,
    description='Site Name:',
    #ensure_option=True,
    disabled=False,
    layout=widgets.Layout(width='448px'))

es = widgets.Select(
    options=['-'], 
    value='-', 
    rows=10, 
    description='Engine:', 
    disabled=False, 
    layout=widgets.Layout(width='600px'))
es.observe(do_sel, 'value')

sel = widgets.Text(
    value='-', 
    description='selected:', 
    disabled=True, 
    layout=widgets.Layout(width='400px'))

selno = widgets.Text(
    value='-', 
    description='Motor No:', 
    disabled=True, 
    layout=widgets.Layout(width='200px'))

sb = widgets.Button(
    description='Lookup',
    disabled=False, 
    button_style='primary')
sb.on_click(sbcb)

_tab = widgets.VBox([
        widgets.HBox([tdd,sb]),
        es,
        widgets.HBox([sel,selno]),
        tab1_out
    ],
    layout=widgets.Layout(height=V.hh)
)