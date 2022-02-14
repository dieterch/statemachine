import pandas as pd
from tqdm.auto import tqdm
import os
import pickle

class State:
    def __init__(self, name, transferfun_list):
        self._name = name
        self._transf = transferfun_list
        self._messages = []
        self._duration = pd.Timedelta(0)
    
    def send(self,msg):
        self._messages.append(msg)
        for transf in self._transf: # screen triggers
            if msg['name'] == transf['trigger'][:4]:
                return transf['new-state']
        return self._name

    def add_duration(self, dt):
        self._duration += dt

    def get_duration(self):
        return self._duration

class FSM:
    initial_state = 'coldstart'
    states = {
            'coldstart': State('coldstart',[
                { 'trigger':'1225 Service selector switch Off', 'new-state':'mode-off'}
                ]),
            'mode-off':  State('mode-off',[
                { 'trigger':'1226 Service selector switch Manual', 'new-state': 'mode-manual'},
                { 'trigger':'1227 Service selector switch Automatic', 'new-state':'mode-automatic'},
                { 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),
            'mode-manual': State('mode-manual',[
                { 'trigger':'1227 Service selector switch Automatic', 'new-state':'mode-automatic'},
                { 'trigger':'1265 Demand gas leakage check gas train 1', 'new-state':'start-preparation'},
                #{ 'trigger':'1267 Demand gas leakage check gas train 2', 'new-state':'start-preparation'},
                { 'trigger':'1225 Service selector switch Off', 'new-state':'mode-off'},
                { 'trigger':'1232 Request module off', 'new-state':'mode-off'},
                { 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),
            'mode-automatic': State('mode-automatic',[
                { 'trigger':'1265 Demand gas leakage check gas train 1', 'new-state':'start-preparation'},
                { 'trigger':'1226 Service selector switch Manual', 'new-state':'mode-manual'},
                { 'trigger':'1225 Service selector switch Off', 'new-state':'mode-off'},
                { 'trigger':'1232 Request module off', 'new-state':'mode-off'},
                { 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),
            'start-preparation': State('start-preparation',[
                { 'trigger':'1249 Starter on', 'new-state': 'starter'},
                { 'trigger':'1225 Service selector switch Off', 'new-state':'mode-off'},
                { 'trigger':'1232 Request module off', 'new-state': 'mode-off'},
                { 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),
            'starter': State('starter',[
                { 'trigger':'3225 Ignition on', 'new-state':'hochlauf'},
                { 'trigger':'1225 Service selector switch Off', 'new-state':'mode-off'},
                { 'trigger':'1232 Request module off', 'new-state':'mode-off'},
                { 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),
            'hochlauf': State('hochlauf',[
                { 'trigger':'2124 Idle', 'new-state':'idle'},
                { 'trigger':'1225 Service selector switch Off', 'new-state':'mode-off'},
                { 'trigger':'1232 Request module off', 'new-state':'mode-off'},
                { 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),             
            'idle': State('idle',[
                { 'trigger':'2139 Request Synchronization', 'new-state':'synchronize'},
                { 'trigger':'1225 Service selector switch Off', 'new-state':'mode-off'},
                { 'trigger':'1232 Request module off', 'new-state':'mode-off'},
                { 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),
            'synchronize': State('synchronize',[
                { 'trigger':'2122 Mains parallel operation', 'new-state':'net-parallel'},                
                { 'trigger':'1225 Service selector switch Off', 'new-state':'mode-off'},
                { 'trigger':'1232 Request module off', 'new-state':'mode-off'},
                { 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ]),             
            'net-parallel': State('net-parallel',[
                { 'trigger':'2122 Mains parallel operation', 'new-state':'net-parallel'},                
                { 'trigger':'1225 Service selector switch Off', 'new-state':'mode-off'},
                { 'trigger':'1232 Request module off', 'new-state':'mode-off'},
                { 'trigger':'1254 Cold start CPU', 'new-state':'coldstart'}
                ])             
        }


class msgFSM:
    def __init__(self, sn, frompickle=False):
        if not frompickle:
            self.load_messages(sn)

            self.states = FSM.states
            self.current_state = FSM.initial_state
            self.act_service_selector = None

            # for initialize some values for collect_data.
            self._runlog = []
            self.st_timing = 'off'
            self.st_timer = pd.Timedelta(0)
            self.last_ts = None
            self._starts = []
        else:
            pfn = os.getcwd() + '/data/' + str(sn) + '_statemachine.pkl'
            with open(pfn, 'rb') as handle:
                self.__dict__ = pickle.load(handle)

    def store(self):
        pfn = os.getcwd() + '/data/' + str(self._sn) + '_statemachine.pkl'
        with open(pfn, 'wb') as handle:
            pickle.dump(self.__dict__, handle, protocol=4)

    def load_messages(self,sn):
        self._sn = sn
        mfn = os.getcwd() + '/data/' + str(self._sn) + '_messages.pkl'
        if os.path.exists(mfn):
            self._messages = pd.read_pickle(mfn).reset_index()
        else:
            raise ValueError(f'messages for SN{self._sn} not found')
        self._messages_first = pd.Timestamp(self._messages.iloc[0]['timestamp']*1e6)
        self._messages_last = pd.Timestamp(self._messages.iloc[-1]['timestamp']*1e6)
        self._whole_period = pd.Timedelta(self._messages_last - self._messages_first).round('S')

    def run(self):
        pbar = tqdm(total=self._messages.shape[0])
        for i,msg in self._messages.iterrows():
            self.send(msg)
            pbar.update(i)
        pbar.close()

    def _collect_data(self, actstate, msg):

        if self.current_state != actstate:
            # Timestamp at the time of switching states
            switch_ts = pd.to_datetime(int(msg['timestamp'])*1e6)
            tt = switch_ts.strftime('%d.%m.%Y %H:%M:%S')

            # How long have i been in actstate ?
            d_ts = pd.Timedelta(switch_ts - self.last_ts) if self.last_ts else pd.Timedelta(0)

            # Summ all states durations and store the timestamp for next pereriod.
            self.states[actstate].add_duration(d_ts)
            self.last_ts = switch_ts

            if self.current_state == 'mode-off':
                self.act_service_selector = 'OFF'
            if self.current_state == 'mode-manual':
                self.act_service_selector = 'MANUAL'
            if self.current_state == 'mode-automatic':
                self.act_service_selector = 'AUTO'

            # a Start is happening.
            if self.current_state == 'start-preparation':
                self._starts.append({
                    'success': False,
                    'mode':self.act_service_selector,
                    'starttime': switch_ts.round('S'),
                    'endtime': pd.Timestamp(0),
                    'cumtime': pd.Timedelta(0).round('S')
                })
                self.st_timing = 'on'
                self.st_timer = pd.Timedelta(0)
            elif self.st_timing == 'on' and actstate != 'coldstart':
                self.st_timer = self.st_timer + d_ts
                self._starts[-1][actstate] = d_ts.seconds + d_ts.microseconds / 1e6 if actstate != 'net-parallel' else d_ts.round('S')
                if actstate != 'net-parallel':
                    self._starts[-1]['cumtime'] = self.st_timer.seconds + self.st_timer.microseconds / 1e6

            if self.current_state == 'net-parallel':
                if self.st_timing == 'on':
                    self._starts[-1]['success'] = True   # wenn der Start bis hierhin kommt, ist er erfolgreich.

            # Ein Motorlauf(-versuch) is zu Ende. 
            if self.current_state == 'mode-off':
                if self.st_timing == 'on':
                    self._starts[-1]['endtime'] = switch_ts.round('S')
                self.st_timing = 'off'
                self.st_timer = pd.Timedelta(0)

            _logtxt = f"{tt} |{actstate:<18} {d_ts.seconds:6d}s {self.st_timer.seconds:3d}s {msg['name']} {msg['message']:<40} {len(self._starts):>3d} {len([s for s in self._starts if s['success']]):>3d} {self.st_timing:>3} => {self.current_state:<20}"
            self._runlog.append(_logtxt)
            #print(_logtxt)

    def send(self, msg):
        actstate = self.current_state
        self.current_state = self.states[self.current_state].send(msg)
        self._collect_data(actstate, msg)
    
    def completed(self):

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
gesamter Zeitraum: {self.dauer.round('S')}

''')
        for state in self.states:

            alarms, alu = filter_messages(self.states[state]._messages, 800)
            al = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in alu[:self.cutlist]])

            warnings, wru = filter_messages(self.states[state]._messages, 700)
            wn = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in wru[:self.cutlist]])

            print(
f"""
{state}:
Dauer       : {str(self.states[state].get_duration().round('S')):>20}  
Anteil      : {self.states[state].get_duration()/self.dauer*100.0:20.2f}%
Messages    : {len(self.states[state]._messages):20} 
Alarms total: {alarms:20d}
      unique: {len(alu):20d}

{al}

Warnings total: {warnings:20d}
        unique: {len(wru):20d}

{wn}
""")
        print('completed')
