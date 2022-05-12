import pandas as pd; pd.options.mode.chained_assignment = None
import numpy as np
import ipywidgets as widgets
import ipyregulartable as rt
from App.common import loading_bar, V, tabs_out

#########################################
# tab7 - playground2
#########################################
class Tab():
    def __init__(self):

        self.title = '7. playground'
        self.tab7_out = widgets.Output()
        self.w = rt.RegularTableWidget()

    @property
    def tab(self):
        return widgets.VBox([self.w])

    def selected(self):
        with tabs_out:
            tabs_out.clear_output()
            #self.w = rt.RegularTableWidget(V.rdf[['starttime'] + V.fsm.results['run2_content']['startstop']])
            print('tab7')
