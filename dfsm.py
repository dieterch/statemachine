from cProfile import label
import arrow
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm.auto import tqdm
import os
import pickle
from pprint import pformat as pf
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

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

class FSM:
    initial_state = 'standstill'
    states = {
            # 'coldstart': State('coldstart',[
            #     { 'trigger':'1225 Service selector switch Off', 'new-state':'standstill'},
            #     #{ 'trigger':'1226 Service selector switch Manual', 'new-state': 'mode-manual'},
            #     #{ 'trigger':'1227 Service selector switch Automatic', 'new-state':'mode-automatic'},
            #     ]),
            'standstill': State('standstill',[
                { 'trigger':'1231 Request module on', 'new-state': 'start-preparation'},
                #{ 'trigger':'1265 Demand gas leakage check gas train 1', 'new-state':'start-preparation'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}                
                ]),
            'start-preparation': State('start-preparation',[
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
                { 'trigger':'1235 Generator CB closed', 'new-state':'load-ramp'},                
                { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),             
            'load-ramp': State('load-ramp',[
                { 'trigger':'9047 Target load reached', 'new-state':'target-operation'},
                { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                #{ 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),             
            'target-operation': State('target-operation',[
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
        self._pre_period = 15 #sec earlier data download Start before event.
        self.filter_times = ['start-preparation','starter','hochlauf','idle','synchronize','load-ramp','cumstarttime']
        self.filter_content = ['success','mode'] + self.filter_times + ['target-operation']
        self.filter_period = ['starttime','endtime']

        if frompickle and os.path.exists(self.pfn):
            with open(self.pfn, 'rb') as handle:
                self.__dict__ = pickle.load(handle)    
        else:
            self.load_messages(e, p_from, p_to, skip_days)
            self._data_spec = ['Various_Values_SpeedAct','Power_PowerAct']
            #self.load_data(timecycle = 30)

            self._target_load_message = any(self._messages['name'] == '9047')
            self.states = FSM.states
            self.current_state = FSM.initial_state
            self.act_service_selector = ''

            # for initialize some values for collect_data.
            self._runlog = []
            self._in_operation = '???'
            self._timer = pd.Timedelta(0)
            self.last_ts = None
            self._starts = []
            self._loadramp = self._e['rP_Ramp_Set'] or 0.625 # %/sec
            self._default_ramp_duration = int(100.0 / self._loadramp * 1e3)
            self.full_load_timestamp = None
            print(f"{'Using' if self._target_load_message else 'Calculating'} '9047 target load reached' Message.")
            if not self._target_load_message:
                print(f"load ramp assumed to {self._loadramp} %/sec based on {'rP_Ramp_Set Parameter' if self._e['rP_Ramp_Set'] else 'INNIO standard'}")

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

    ### messages handling
    def load_messages(self,e, p_from, p_to, skip_days):
        self._messages = e.get_messages(p_from, p_to)
        self.first_message = pd.Timestamp(self._messages.iloc[0]['timestamp']*1e6)
        self.last_message = pd.Timestamp(self._messages.iloc[-1]['timestamp']*1e6)
        self._period = pd.Timedelta(self.last_message - self.first_message).round('S')
        if skip_days and not p_from:
            self.first_message = pd.Timestamp(arrow.get(self.first_message).shift(days=skip_days).timestamp()*1e9)
            self._messages = self._messages[self._messages['timestamp'] > int(arrow.get(self.first_message).shift(days=skip_days).timestamp()*1e3)]
        self.count_messages = self._messages.shape[0]

    def save_messages(self, fn):
        with open(fn, 'w') as f:
            for index, msg in self._messages.iterrows():
                f.write(f"{index:>06} {msg['severity']} {msg['timestamp']} {pd.to_datetime(int(msg['timestamp'])*1e6).strftime('%d.%m.%Y %H:%M:%S')}  {msg['name']} {msg['message']}\n")
                if 'associatedValues' in msg:
                    if msg['associatedValues'] == msg['associatedValues']:  # if not NaN ...
                        f.write(f"{pf(msg['associatedValues'])}\n\n")

    ### data handling
    def _load_data(self, engine=None, p_data=None, ts_from=None, ts_to=None, p_timeCycle=30, p_forceReload=False, p_slot=99):
        engine = engine or self._e
        ts_from = ts_from or self.first_message 
        ts_to = ts_to or self.last_message 
        return engine.hist_data(
            itemIds = engine.get_dataItems(p_data or self._data_spec),
            p_from = arrow.get(ts_from).to('Europe/Vienna'),
            p_to = arrow.get(ts_to).to('Europe/Vienna'),
            timeCycle=p_timeCycle,
            forceReload=p_forceReload,
            slot=p_slot
        )

    def load_data(self, cycletime, tts_from=None, tts_to=None):
        return self._load_data(p_timeCycle=cycletime, ts_from=tts_from, ts_to=tts_to, p_slot=tts_from or 9999)

    def get_period(self, ts0, ts1, cycletime=None, *args, **kwargs):
        lts_from = int(ts0)
        lts_to = int(ts1)
        data = self.load_data(cycletime, tts_from=lts_from, tts_to=lts_to)
        return data

    ### plotting
    def plot_ts(self, tts, left = -300, right = 150, cycletime=None, *args, **kwargs):
        lts_from = int(tts + left * 1e3)
        lts_to = int(tts + right * 1e3)
        data = self.load_data(cycletime, tts_from=lts_from, tts_to=lts_to)
        step = data.iloc[1]['time'] - data.iloc[0]['time'] #in ms
        ax, ax2, idf = self._plot(data[
            (data['time'] >= lts_from) & 
            (data['time'] <= lts_to)
            ], *args, **kwargs)
        return idf

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
        for k in list(self.states.keys())[1:-1]:
            dtt=rec[k]
            if dtt == dtt:
                ax.axvline(arrow.get(rec['starttime']).shift(seconds=duration).datetime, color="red", linestyle="dotted", label=f"{duration:4.1f}")
                duration = duration + dtt
            else:
                break
        ax.axvline(arrow.get(rec['starttime']).shift(seconds=duration).datetime, color="red", linestyle="dotted", label=f"{duration:4.1f}")
        r_summary = pd.DataFrame(rec[self.filter_times], dtype=np.float64).round(2).T
        plt.table(
            cellText=r_summary.values, 
            colWidths=[0.1]*len(r_summary.columns),
            colLabels=r_summary.columns,
            cellLoc='center', 
            rowLoc='center',
            loc='lower right')
        return idf

    def _plot(self, idf, ylim2=(0,5000), *args, **kwargs):
        ax = idf[['datetime','Various_Values_SpeedAct']].plot(
        x='datetime',
        y='Various_Values_SpeedAct',
        kind='line',
        grid=True, 
        *args, **kwargs)

        ax2 = idf[['datetime','Power_PowerAct']].plot(
        x='datetime',
        y='Power_PowerAct',
        secondary_y = True,
        ax = ax,
        kind='line', 
        grid=True, 
        *args, **kwargs)

        ax2.set_ylim(ylim2)
        return ax, ax2, idf
         
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
        if self.current_state == 'start-preparation':
            # apends a new record to the Starts list.
            self._starts.append({
                'success': False,
                'mode':self.act_service_selector,
                'starttime': switch_point,
                'endtime': pd.Timestamp(0),
                'cumstarttime': pd.Timedelta(0),
                'alarms': [],
                'warnings': []
            })
            # indicate a 
            self._in_operation = 'on'
            self._timer = pd.Timedelta(0)
        elif self._in_operation == 'on': # and actstate != FSM.initial_state:
            self._timer = self._timer + duration
            self._starts[-1][actstate] = _to_sec(duration) if actstate != 'target-operation' else duration.round('S')
            if actstate != 'target-operation':
                self._starts[-1]['cumstarttime'] = _to_sec(self._timer)

        if self.current_state == 'target-operation':
            if self._in_operation == 'on':
                self._starts[-1]['success'] = True   # wenn der Start bis hierhin kommt, ist er erfolgreich.

        # Ein Motorlauf(-versuch) is zu Ende. 
        if self.current_state == 'standstill': #'mode-off'
        #if actstate == 'load-ramp': # übergang von loadramp to 'target-operation'
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

    ### FSM Entry Point.
    def run(self):
        for i,msg in tqdm(self._messages.iterrows(), total=self._messages.shape[0], ncols=80, mininterval=1, unit=' messages', desc="FSM"):
            actstate = self.current_state

            if self._target_load_message:
                self.current_state = self.states[self.current_state].send(msg)
            else: # berechne die Zeit bis Vollast
                if self.full_load_timestamp == None or int(msg['timestamp']) < self.full_load_timestamp:
                    self.current_state = self.states[self.current_state].send(msg)
                elif int(msg['timestamp']) >= self.full_load_timestamp: # now switch to 'target-operation'
                    dmsg = {'name':'9047', 'message':'Target load reached (calculated)','timestamp':self.full_load_timestamp,'severity':600}
                    self.current_state = self.states[self.current_state].send(dmsg)
                    self._collect_data(actstate, dmsg)
                    self.full_load_timestamp = None
                    actstate = self.current_state            

                # Algorithm to switch from 'load-ramp to' 'target-operation'
                if self.current_state == 'load-ramp' and self.full_load_timestamp == None:  # direct bein Umschalten das Ende der Rampe berechnen
                    self.full_load_timestamp = int(msg['timestamp']) + self._default_ramp_duration

            self._collect_data(actstate, msg)
    
    ### Prepare Results
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

    def completed(self, limit_to = 10):

        def filter_messages(messages, severity):
            fmessages = [msg for msg in messages if msg['severity'] == severity]
            unique_messages = set([msg['name'] for msg in fmessages])
            res_messages = [{ 'anz': len([msg for msg in fmessages if msg['name'] == m]), 
                              'msg':f"{m} {[msg['message'] for msg in fmessages if msg['name'] == m][0]}"
                            } for m in unique_messages]
            return len(fmessages), sorted(res_messages, key=lambda x:x['anz'], reverse=True) 
        
        print(f'''

*****************************************
* Ergebnisse (c)2022 Dieter Chvatal     *
*****************************************
gesamter Zeitraum: {self._period.round('S')}

''')
        for state in self.states:

            alarms, alu = filter_messages(self.states[state]._messages, 800)
            al = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in alu[:limit_to]])

            warnings, wru = filter_messages(self.states[state]._messages, 700)
            wn = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in wru[:limit_to]])

            print(
f"""
{state}:
Dauer       : {str(self.states[state].get_duration().round('S')):>20}  
Anteil      : {self.states[state].get_duration()/self._whole_period*100.0:20.2f}%
Messages    : {len(self.states[state]._messages):20} 
Alarms total: {alarms:20d}
      unique: {len(alu):20d}

{al}

Warnings total: {warnings:20d}
        unique: {len(wru):20d}

{wn}
""")
        print('completed')
