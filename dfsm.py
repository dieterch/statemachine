from cProfile import label
from decimal import DivisionByZero
import arrow
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm.auto import tqdm
import os
import pickle
from pprint import pformat as pf
import warnings
from collections import namedtuple
warnings.simplefilter(action='ignore', category=FutureWarning)
from IPython.display import HTML, display


#Various_Bits_CollAlarm

# States und Transferfunktionen, Sammeln von Statebezogenen Daten ... 
class State:
    def __init__(self, name, transferfun_list):
        self._name = name
        self._transf = transferfun_list
        self._messages = []
        self._dt = pd.Timedelta(0)
    
    def send(self,msg):
        # store Warnings and Alarms vs. the states we are in.
        if msg['severity'] in [700,800]:
            self._messages.append(msg) 
        for transf in self._transf: # screen triggers
            if msg['name'] == transf['trigger'][:4]:
                return transf['new-state']
        return self._name

    def _to_sec(self, time_object):
        return float(time_object.seconds) + float(time_object.microseconds) / 1e6

    @property
    def dt(self):
        return self._to_sec(self._dt)

    @dt.setter
    def dt(self, value):
        self._dt = value

# dataClass FSM
class FSM:
    initial_state = 'standstill'
    states = {
            # 'coldstart': State('coldstart',[
            #     { 'trigger':'1225 Service selector switch Off', 'new-state':'standstill'},
            #     #{ 'trigger':'1226 Service selector switch Manual', 'new-state': 'mode-manual'},
            #     #{ 'trigger':'1227 Service selector switch Automatic', 'new-state':'mode-automatic'},
            #     ]),
            'standstill': State('standstill',[
                { 'trigger':'1231 Request module on', 'new-state': 'startpreparation'},
                #{ 'trigger':'1265 Demand gas leakage check gas train 1', 'new-state':'startpreparation'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}                
                ]),
            'startpreparation': State('startpreparation',[
                { 'trigger':'1249 Starter on', 'new-state': 'starter'},
                { 'trigger':'1232 Request module off', 'new-state': 'standstill'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),
            'starter': State('starter',[
                { 'trigger':'3225 Ignition on', 'new-state':'hochlauf'},
                { 'trigger':'1232 Request module off', 'new-state':'standstill'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),
            'hochlauf': State('hochlauf',[
                { 'trigger':'2124 Idle', 'new-state':'idle'},
                { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),             
            'idle': State('idle',[
                { 'trigger':'2139 Request Synchronization', 'new-state':'synchronize'},
                { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),
            'synchronize': State('synchronize',[
                { 'trigger':'1235 Generator CB closed', 'new-state':'loadramp'},                
                { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),             
            'loadramp': State('loadramp',[
                { 'trigger':'9047 Target load reached', 'new-state':'targetoperation'},
                { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),             
            'targetoperation': State('targetoperation',[
                #{ 'trigger':'1236 Generator CB opened', 'new-state':'idle'},
                { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                ])       
        }

    @classmethod
    def dot(cls, fn):
        """Create a FSM Diagram of specified states in *.dot Format

        Args:
            fn : Filename
        """
        with open(fn, 'w') as f:
            f.write("digraph G {\n")
            f.write('    graph [rankdir=TB labelfontcolor=red fontname="monospace" nodesep=1 size="20,33"]\n')
            f.write('    node [fontname="monospace" fontsize=10  shape="circle"]\n')
            f.write('    edge [fontname="monospace" color="grey" fontsize=10]\n')
            for s in cls.states:
                f.write(f'    {s.replace("-","")} [label="{s}"]\n')
                for t in cls.states[s]._transf:
                    f.write(f'    {s.replace("-","")} -> {t["new-state"].replace("-","")} [label="{t["trigger"]}"]\n')
            f.write("}\n")

class msgFSM:
    def __init__(self, e, p_from = None, p_to=None, frompickle=False, skip_days=None):
        self._e = e
        self._p_from = p_from
        self._p_to = p_to
        self.pfn = self._e._fname + '_statemachine.pkl'
        self._pre_period = 0 #sec earlier data download Start before event.

        # Filters
        self.filters = {
            'vertical_lines_times': ['startpreparation','starter','hochlauf','idle','synchronize','loadramp'],
            'filter_times': ['startpreparation','starter','hochlauf','idle','synchronize','loadramp','cumstarttime'],
            'filter_content': ['success','mode','startpreparation','starter','hochlauf','idle','synchronize','loadramp','cumstarttime','targetoperation'],
            'run2filter_content':['index','success','mode','startpreparation','starter','hochlauf','idle','synchronize','loadramp','cumstarttime','maxload','ramprate','targetoperation'],
            'filter_alarms_and_warnings':['count_alarms', 'count_warnings'],
            'filter_period':['starttime','endtime']
        }
        #self.vertical_lines_times = ['startpreparation','starter','hochlauf','idle','synchronize','loadramp']
        #self.filter_times = ['startpreparation','starter','hochlauf','idle','synchronize','loadramp','cumstarttime']
        #self.filter_content = ['success','mode'] + self.filter_times + ['targetoperation']
        #self.run2filter_content = ['index','success','mode'] + self.filter_times + ['index','maxload','ramp','targetoperation']
        #self.filter_alarms_and_warnings = ['count_alarms', 'count_warnings']
        #self.filter_period = ['starttime','endtime']

        if frompickle and os.path.exists(self.pfn):
            with open(self.pfn, 'rb') as handle:
                self.__dict__ = pickle.load(handle)    
        else:
            self.load_messages(e, p_from, p_to, skip_days)
            self._data_spec = ['Various_Values_SpeedAct','Power_PowerAct']
            #self.load_data(timecycle = 30)

            # Es gibt zwar die message, sie ist aber nicht bei allen Motoren implementiert
            # und wird zumindest in einem Fall (Forsa Hartmoor, M?) nicht 100% zuverlässig geloggt
            # daher ist das schätzen und verfeinern in run2 zuverlässiger. 1.3.2033 - Dieter 
            #self._target_load_message = any(self._messages['name'] == '9047')
            self._target_load_message = False
            self._loadramp = self._e['rP_Ramp_Set'] or 0.625 # %/sec
            self._default_ramp_duration = int(100.0 / self._loadramp * 1e3)
            self.full_load_timestamp = None
            # print(f"{'Using' if self._target_load_message else 'Calculating'} '9047 target load reached' Message.")
            # if not self._target_load_message:
            #     print(f"load ramp assumed to {self._loadramp} %/sec based on {'rP_Ramp_Set Parameter' if self._e['rP_Ramp_Set'] else 'INNIO standard'}")

            self.states = FSM.states
            self.current_state = FSM.initial_state
            self.act_service_selector = '???'

            # for initialize some values for collect_data.
            self._runlog = []
            self._in_operation = '???'
            self._timer = pd.Timedelta(0)
            self.last_ts = None
            self._starts = []
            self._starts_counter = 0

    def store(self):
        try:
            with open(self.pfn, 'wb') as handle:
                pickle.dump(self.__dict__, handle, protocol=4)
        except:
            pass

    def unstore(self):
        if os.path.exists(self.pfn):
            os.remove(self.pfn)

    @property
    def period(self):
        return self._period

    ## message handling
    def load_messages(self,e, p_from, p_to, skip_days):
        self._messages = e.get_messages(p_from, p_to)
        self.first_message = pd.Timestamp(self._messages.iloc[0]['timestamp']*1e6)
        self.last_message = pd.Timestamp(self._messages.iloc[-1]['timestamp']*1e6)
        self._period = pd.Timedelta(self.last_message - self.first_message).round('S')
        if skip_days and not p_from:
            self.first_message = pd.Timestamp(arrow.get(self.first_message).shift(days=skip_days).timestamp()*1e9)
            self._messages = self._messages[self._messages['timestamp'] > int(arrow.get(self.first_message).shift(days=skip_days).timestamp()*1e3)]
        self.count_messages = self._messages.shape[0]

    def msgtxt(self, msg, idx=0):
        return f"{idx:>06} {msg['severity']} {msg['timestamp']} {pd.to_datetime(int(msg['timestamp'])*1e6).strftime('%d.%m.%Y %H:%M:%S')}  {msg['name']} {msg['message']}"

    def save_messages(self, fn):
        with open(fn, 'w') as f:
            for index, msg in self._messages.iterrows():
                f.write(self.msgtxt(msg, index)+'\n')
                #f.write(f"{index:>06} {msg['severity']} {msg['timestamp']} {pd.to_datetime(int(msg['timestamp'])*1e6).strftime('%d.%m.%Y %H:%M:%S')}  {msg['name']} {msg['message']}\n")
                if 'associatedValues' in msg:
                    if msg['associatedValues'] == msg['associatedValues']:  # if not NaN ...
                        f.write(f"{pf(msg['associatedValues'])}\n\n")

    ## data handling
    def _load_data(self, engine=None, p_data=None, ts_from=None, ts_to=None, p_timeCycle=None, p_forceReload=False, p_slot=99, silent=False):
        engine = engine or self._e
        if not p_timeCycle:
            p_timeCycle = 30
        ts_from = ts_from or self.first_message 
        ts_to = ts_to or self.last_message 
        return engine.hist_data(
            itemIds = engine.get_dataItems(p_data or self._data_spec),
            p_from = arrow.get(ts_from).to('Europe/Vienna'),
            p_to = arrow.get(ts_to).to('Europe/Vienna'),
            timeCycle=p_timeCycle,
            forceReload=p_forceReload,
            slot=p_slot,
            silent=silent
        )

    def load_data(self, cycletime, tts_from=None, tts_to=None, silent=False):
        return self._load_data(p_timeCycle=cycletime, ts_from=tts_from, ts_to=tts_to, p_slot=tts_from or 9999, silent=silent)

    def get_period_data(self, ts0, ts1, cycletime=None):
        lts_from = int(ts0)
        lts_to = int(ts1)
        data = self.load_data(cycletime, tts_from=lts_from, tts_to=lts_to)
        data[(data['time'] >= lts_from) & 
                (data['time'] <= lts_to)]
        return data

    def get_ts_data(self, tts, left = -300, right = 150, cycletime=None):
        if not cycletime:
            cycletime = 1 # default for get_ts_data
        lts_from = int(tts + left)
        lts_to = int(tts + right)
        return self.get_period_data(lts_from, lts_to, cycletime)        

    def get_cycle_data(self,rec, max_length=None, min_length=None, cycletime=None, silent=False):
        t0 = int(arrow.get(rec['starttime']).timestamp() * 1e3 - self._pre_period * 1e3)
        t1 = int(arrow.get(rec['endtime']).timestamp() * 1e3)
        if max_length:
            if (t1 - t0) > max_length * 1e3:
                t1 = int(t0 + max_length * 1e3)
        if min_length:
            if (t1 - t0) < min_length * 1e3:
                t1 = int(t0 + min_length * 1e3)
        data = self.load_data(cycletime, tts_from=t0, tts_to=t1, silent=silent)
        data = data[(data['time'] >= t0) & (data['time'] <= t1)]
        return data

    ## plotting
    def plot_cycle(self, rec, max_length=None, cycletime=None, *args, **kwargs):
        t0 = int(arrow.get(rec['starttime']).timestamp() * 1e3 - self._pre_period * 1e3)
        t1 = int(arrow.get(rec['endtime']).timestamp() * 1e3)
        if max_length:
            if (t1 - t0) > max_length * 1e3:
                t1 = int(t0 + max_length * 1e3)
        data = self.load_data(cycletime, tts_from=t0, tts_to=t1)
        (ax, ax2, idf) = self._plot(
            data[
                (data['time'] >= t0) & 
                (data['time'] <= t1)],        
                *args, **kwargs
            )
        duration = 0.0
        for k in rec[self.filters['vertical_lines_times']].index:
            dtt=rec[k]
            if dtt == dtt:
                ax.axvline(arrow.get(rec['starttime']).shift(seconds=duration).datetime, color="red", linestyle="dotted", label=f"{duration:4.1f}")
                duration = duration + dtt
            else:
                break
        ax.axvline(arrow.get(rec['starttime']).shift(seconds=duration).datetime, color="red", linestyle="dotted", label=f"{duration:4.1f}")
        r_summary = pd.DataFrame(rec[self.filters['filter_times']], dtype=np.float64).round(2).T
        """
        available options for loc:
        best, upper right, upper left, lower left, lower right, center left, center right
        lower center, upper center, center, top right,top left, bottom left, bottom right
        right, left, top, bottom
        """
        plt.table(
            cellText=r_summary.values, 
            colWidths=[0.1]*len(r_summary.columns),
            colLabels=r_summary.columns,
            cellLoc='center', 
            rowLoc='center',
            loc='upper left')
        return idf

    def _plot(self, idf, x12='datetime', y1 = ['Various_Values_SpeedAct'], y2 = ['Power_PowerAct'], ylim2=(0,5000), *args, **kwargs):
        ax = idf[[x12] + y1].plot(
        x=x12,
        y=y1,
        kind='line',
        grid=True, 
        *args, **kwargs)

        ax2 = idf[[x12] + y2].plot(
        x=x12,
        y=y2,
        secondary_y = True,
        ax = ax,
        kind='line', 
        grid=True, 
        *args, **kwargs)

        ax2.set_ylim(ylim2)
        return ax, ax2, idf

    ### die Finite State Machine selbst:
    #1225 Service selector switch Off
    #1226 Service selector switch Manual
    #1227 Service selector switch Automatic
    def _fsm_Service_selector(self, msg):
        if msg['name'] == '1225 Service selector switch Off'[:4]:
            self.act_service_selector = 'OFF'
        if msg['name'] == '1226 Service selector switch Manual'[:4]:
            self.act_service_selector = 'MANUAL'
        if msg['name'] == '1227 Service selector switch Automatic'[:4]:
            self.act_service_selector = 'AUTO'

    def _fsm_Operating_Cycle(self, actstate, newstate, switch_point, duration, msg):
        def _to_sec(time_object):
            return float(time_object.seconds) + float(time_object.microseconds) / 1e6
        # Start Preparatio => the Engine ist starting
        if self.current_state == 'startpreparation':
            # apends a new record to the Starts list.
            self._starts.append({
                'index':self._starts_counter,
                'success': False,
                'mode':self.act_service_selector,
                'starttime': switch_point,
                'endtime': pd.Timestamp(0),
                'cumstarttime': pd.Timedelta(0),
                'alarms': [],
                'warnings': []
            })
            self._starts_counter += 1 # index for next start
            # indicate a 
            self._in_operation = 'on'
            self._timer = pd.Timedelta(0)
        elif self._in_operation == 'on': # and actstate != FSM.initial_state:
            self._timer = self._timer + duration
            self._starts[-1][actstate] = _to_sec(duration) if actstate != 'targetoperation' else duration.round('S')
            if actstate != 'targetoperation':
                self._starts[-1]['cumstarttime'] = _to_sec(self._timer)

        if self.current_state == 'targetoperation':
            if self._in_operation == 'on':
                self._starts[-1]['success'] = True   # wenn der Start bis hierhin kommt, ist er erfolgreich.

        # Ein Motorlauf(-versuch) is zu Ende. 
        if self.current_state == 'standstill': #'mode-off'
        #if actstate == 'loadramp': # übergang von loadramp to 'targetoperation'
            if self._in_operation == 'on':
                self._starts[-1]['endtime'] = switch_point
            self._in_operation = 'off'
            self._timer = pd.Timedelta(0)

        _logtxt = f"{switch_point.strftime('%d.%m.%Y %H:%M:%S')} |{actstate:<18} {_to_sec(duration):8.1f}s {_to_sec(self._timer):6.1f}s {msg['name']} {msg['message']:<40} {len(self._starts):>3d} {len([s for s in self._starts if s['success']]):>3d} {self._in_operation:>3} {self.act_service_selector:>4} => {self.current_state:<20}"
        #_logtxt = f"{switch_point.strftime('%d.%m.%Y %H:%M:%S')} |{actstate:<18} {_to_sec(duration):8.1f}s {msg['name']} {msg['message']:<40} {len(self._starts):>3d} {len([s for s in self._starts if s['success']]):>3d} {self._in_operation:>3} {self.act_service_selector:>4} => {self.current_state:<20}"
        self._runlog.append(_logtxt)


    def _collect_data(self, actstate, msg):
        self._fsm_Service_selector(msg)
        # collect alarms & warnings vs. Starts
        if self._in_operation == 'on':
            if msg['severity'] == 800:
                self._starts[-1]['alarms'].append({'state':self.current_state, 'msg': msg})
            if msg['severity'] == 700:
                self._starts[-1]['warnings'].append({'state':self.current_state, 'msg': msg})
        if self.current_state != actstate:
            # Timestamp at the time of switching states
            switch_ts = pd.to_datetime(float(msg['timestamp'])*1e6)
            # How long have i been in actstate ?
            d_ts = pd.Timedelta(switch_ts - self.last_ts) if self.last_ts else pd.Timedelta(0)
            # Summ all states durations and store the timestamp for next pereriod.
            self.states[actstate].dt = d_ts
            self.last_ts = switch_ts
            # state machine for service Selector Switch
            self._fsm_Operating_Cycle(actstate, self.current_state, switch_ts, d_ts, msg)

    ## 2nd run - in detail data analysis
    def detect_edge(self, data, name, kind='left'):
        fac = {'left': -1.0, 'right': 1.0}
        ldata = data[['datetime',name]]
        x0 = ldata.iloc[0]['datetime'];
        x1 = ldata.iloc[-1]['datetime'];
        edge0 = data.loc[data[name].idxmax()]
        
        try:
            if kind == 'left':
                xfac = (x1 - x0) / (edge0.datetime - x0)
            elif kind == 'right':
                xfac = (x1 - x0) / (x1 - edge0.datetime)
            else:
                raise ValueError('detect_edge: unknown kind parameter value.')
        except ZeroDivisionError:
            xfac = 0.0
        xfac = min(xfac, 5.0)
        #print(f"###### | xfac: {xfac:5.2f} | kind: {kind:>5} | name: {name}")
        lmax = ldata.loc[:,name].max() * xfac * 0.90

        data[name+'_'+kind] = data[name]+(data['datetime'] - x0)*(fac[kind] * lmax)/(x1-x0) + lmax* (1-fac[kind])/2
        
        Point = namedtuple('edge',["loc", "val"])
        edge = data.loc[data[name+'_'+kind].idxmax()]
        return  Point(edge.datetime, ldata.at[edge.name,name])


###################
# CODING IN WORK
    def run2(self, rda):

        index_list = []
        for n, startversuch in tqdm(rda.iterrows(), total=rda.shape[0], ncols=80, mininterval=1, unit=' starts', desc="FSM Run2"):

                ii = startversuch['index']
                index_list.append(ii)

                if not 'maxload' in startversuch:

                    data = self.get_cycle_data(startversuch, max_length=None, min_length=None, cycletime=1, silent=True)

                    pl = self.detect_edge(data, 'Power_PowerAct', kind='left')
                    pr = self.detect_edge(data, 'Power_PowerAct', kind='right')
                    sl = self.detect_edge(data, 'Various_Values_SpeedAct', kind='left')
                    sr = self.detect_edge(data, 'Various_Values_SpeedAct', kind='right')

                    self._starts[ii]['title'] = f"{self._e} ----- Start {ii} {startversuch['mode']} | {'SUCCESS' if startversuch['success'] else 'FAILED'} | {startversuch['starttime'].round('S')}"
                    #sv_lines = {k:(startversuch[k] if k in startversuch else np.NaN) for k in self.filters['vertical_lines_times']]}
                    sv_lines = [v for v in startversuch[self.filters['vertical_lines_times']]]

                    start = startversuch['starttime'];
                    
                    # lade die in run1 gesammelten Daten in ein DataFrame, ersetze NaN Werte mit 0
                    backup = {}
                    #svdf = pd.DataFrame.from_dict(sv_lines, orient='index', columns=['FSM']).fillna(0)
                    svdf = pd.DataFrame(sv_lines, index=self.filters['vertical_lines_times'], columns=['FSM'], dtype=np.float64).fillna(0)
                    svdf['RUN2'] = svdf['FSM']

                    # intentionally excluded - Dieter 1.3.2022
                    #if svdf.at['hochlauf','FSM'] > 0.0:
                    #        svdf.at['hochlauf','RUN2'] = sl.loc.timestamp() - start.timestamp() - np.cumsum(svdf['RUN2'])['starter']
                    #        svdf.at['idle','RUN2'] = svdf.at['idle','FSM'] - (svdf.at['hochlauf','RUN2'] - svdf.at['hochlauf','FSM'])
                    if svdf.at['loadramp','FSM'] > 0.0:
                            calc_loadramp = pl.loc.timestamp() - start.timestamp() - np.cumsum(svdf['RUN2'])['synchronize']
                            svdf.at['loadramp','RUN2'] = calc_loadramp

                            # collect run2 results.
                            backup['loadramp'] = svdf.at['loadramp','FSM'] # alten Wert merken
                            self._starts[ii]['loadramp'] = calc_loadramp

                    calc_maxload = pl.val
                    if calc_maxload > 0.0:
                        calc_ramp = (calc_maxload / self._e['Power_PowerNominal']) * 100 / svdf.at['loadramp','RUN2']
                    else:
                        calc_ramp = np.NaN
                    backup_cumstarttime = np.cumsum(svdf['FSM'])['loadramp']
                    calc_cumstarttime = np.cumsum(svdf['RUN2'])['loadramp']
                    svdf = pd.concat([
                            svdf, 
                            pd.DataFrame.from_dict(
                                    {       'maxload':['-',calc_maxload],
                                            'ramprate':['-',calc_ramp],
                                            'cumstarttime':[backup_cumstarttime, calc_cumstarttime]
                                    }, 
                                    columns=['FSM','RUN2'],
                                    orient='index')]
                            )
                    #display(HTML(svdf.round(2).T.to_html(escape=False)))

                    # collect run2 results.
                    self._starts[ii]['maxload'] = calc_maxload
                    self._starts[ii]['ramprate'] = calc_ramp
                    backup['cumstarttime'] = backup_cumstarttime
                    self._starts[ii]['cumstarttime'] = calc_cumstarttime

                    self._starts[ii]['backup'] = backup
                    self._starts[ii]['count_alarms'] = len(startversuch['alarms'])
                    self._starts[ii]['count_warnings'] = len(startversuch['warnings'])

        return pd.DataFrame([self._starts[s] for s in index_list])

# END
#################
    ## FSM Entry Point.
    def run1(self):
        self._starts_counter = 0
        for i,msg in tqdm(self._messages.iterrows(), total=self._messages.shape[0], ncols=80, mininterval=1, unit=' messages', desc="FSM"):

            ## FSM Motorstart
            actstate = self.current_state

            # Sonderbehandlung Ende der Lastrampe
            if self._target_load_message:
                self.current_state = self.states[self.current_state].send(msg)
            else: # berechne die Zeit bis Vollast
                if self.full_load_timestamp == None or int(msg['timestamp']) < self.full_load_timestamp:
                    self.current_state = self.states[self.current_state].send(msg)
                elif int(msg['timestamp']) >= self.full_load_timestamp: # now switch to 'targetoperation'
                    dmsg = {'name':'9047', 'message':'Target load reached (calculated)','timestamp':self.full_load_timestamp,'severity':600}
                    self.current_state = self.states[self.current_state].send(dmsg)
                    self._collect_data(actstate, dmsg)
                    self.full_load_timestamp = None
                    actstate = self.current_state            

                # Algorithm to switch from 'loadramp to' 'targetoperation'
                if self.current_state == 'loadramp' and self.full_load_timestamp == None:  # direct bein Umschalten das Ende der Rampe berechnen
                    self.full_load_timestamp = int(msg['timestamp']) + self._default_ramp_duration
            # Datensammlung
            self._collect_data(actstate, msg)
    
    ## Resultate aus einem erfolgreichen FSM Lauf ermitteln.
    def _pareto(self, mm):
        unique_res = set([msg['name'] for msg in mm])
        res = [{ 'anz': len([msg for msg in mm if msg['name'] == m]),
                 'name':m,
                 'msg':f"{str([msg['message'] for msg in mm if msg['name'] == m][0]):>}"
                } for m in unique_res]
        return sorted(res, key=lambda x:x['anz'], reverse=True)        

    def _states_pareto(self, severity, states = []):
        rmessages = []
        if type(states) == str:
            states = [states]
        for state in states:
            rmessages += [msg for msg in self.states[state]._messages if msg['severity'] == severity]
        return self._pareto(rmessages)

    def alarms_pareto(self, states):
        return pd.DataFrame(self._states_pareto(800, states))

    def warnings_pareto(self, states):
        return pd.DataFrame(self._states_pareto(700, states))

    def summary(self, res):
        display(HTML(
            f"""
            <h2>{str(res['engine'])}</h2>
            <br>
            <table>
                <thead>
                    <tr>
                        <td></td>
                        <td>From</td>
                        <td>To</td>
                        <td>Days</td>
                    </tr>
                </thead>
                <tr>
                    <td>Interval</td>
                    <td>{res['fsm'].first_message:%d.%m.%Y}</td>
                    <td>{res['fsm'].last_message:%d.%m.%Y}</td>
                    <td>{res['fsm'].period.days:5}</td>
            </td>
                </tr>
            </table>
            """))
        nsummary = []
        for mode in ['???','OFF','MANUAL', 'AUTO']:
            lstarts = res['result'][res['result']['mode'] == mode].shape[0]
            successful_starts = res['result'][((res['result'].success) & (res['result']['mode'] == mode))].shape[0]
            nsummary.append([lstarts, successful_starts,(successful_starts / lstarts) * 100.0 if lstarts != 0 else 0.0])
        nsummary.append([res['result'].shape[0],res['result'][res['result'].success].shape[0],(res['result'][res['result'].success].shape[0] / res['result'].shape[0]) * 100.0])
        display(HTML(pd.DataFrame(nsummary, index=['???','OFF','MANUAL', 'AUTO','ALL'],columns=['Starts','successful','%'], dtype=np.int64).to_html(escape=False)))

# alter Code
#     def completed(self, limit_to = 10):

#         def filter_messages(messages, severity):
#             fmessages = [msg for msg in messages if msg['severity'] == severity]
#             unique_messages = set([msg['name'] for msg in fmessages])
#             res_messages = [{ 'anz': len([msg for msg in fmessages if msg['name'] == m]), 
#                               'msg':f"{m} {[msg['message'] for msg in fmessages if msg['name'] == m][0]}"
#                             } for m in unique_messages]
#             return len(fmessages), sorted(res_messages, key=lambda x:x['anz'], reverse=True) 
        
#         print(f'''

# *****************************************
# * Ergebnisse (c)2022 Dieter Chvatal     *
# *****************************************
# gesamter Zeitraum: {self._period.round('S')}

# ''')
#         for state in self.states:

#             alarms, alu = filter_messages(self.states[state]._messages, 800)
#             al = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in alu[:limit_to]])

#             warnings, wru = filter_messages(self.states[state]._messages, 700)
#             wn = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in wru[:limit_to]])

#             print(
# f"""
# {state}:
# Dauer       : {str(self.states[state].get_duration().round('S')):>20}  
# Anteil      : {self.states[state].get_duration()/self._whole_period*100.0:20.2f}%
# Messages    : {len(self.states[state]._messages):20} 
# Alarms total: {alarms:20d}
#       unique: {len(alu):20d}

# {al}

# Warnings total: {warnings:20d}
#         unique: {len(wru):20d}

# {wn}
# """)
#         print('completed')
