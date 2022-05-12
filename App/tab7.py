import pandas as pd
pd.options.mode.chained_assignment = None
pd.options.display.float_format = '{:,0.2f}'.format
import numpy as np
import ipywidgets as widgets
from IPython.display import display
import ipyregulartable as rt
from App.common import loading_bar, V, tabs_out

#########################################
# tab7 - playground2
#########################################
class Tab():
    def __init__(self):

        self.title = '7. playground'
        self.tab7_out = widgets.Output()

        self.button = widgets.Button(
            description='Button',
            disabled=False, 
            button_style='primary')
        self.button.on_click(self.b_button)

    def b_button(self, b):
        with self.tab7_out:
            self.tab7_out.clear_output()
            #w = rt.RegularTableWidget(rt.NumpyDataModel())
            self.rde = V.rdf
            self.rde['starttime'] = self.rde['starttime'].dt.strftime('%d.%m.%Y %H:%M:%S')
            #self.rde[['no','startpreparation','starter','speedup','idle','synchronize','loadramp','cumstarttime','targetload','ramprate','maxload','targetoperation','rampdown','coolrun','runout','A', 'W']] = self.rde[['no','startpreparation','starter','speedup','idle','synchronize','loadramp','cumstarttime','targetload','ramprate','maxload','targetoperation','rampdown','coolrun','runout','A', 'W']].applymap(lambda x: '{0:.2f}'.format(x))
            self.rde.fillna('-', inplace=True)
            w = rt.RegularTableWidget(self.rde[['starttime'] + V.fsm.results['run2_content']['startstop']])
            display(w)
            #self.w = rt.RegularTableWidget(V.rdf[['starttime'] + V.fsm.results['run2_content']['startstop']])


    @property
    def tab(self):
        return widgets.VBox([self.button,self.tab7_out])

    def selected(self):
        with tabs_out:
            tabs_out.clear_output()
            print('tab7')