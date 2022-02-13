from re import T
import warnings
import pandas as pd
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
class msgFSM:
    def __init__(self, dauer):
        self.dauer = dauer
        self.states = {
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
        self.current_state = 'coldstart'
        self.startversuch = 0
        self.successfulstart = 0
        self.timing = 'off'
        self.st_timer = pd.Timedelta(0)
        self.last_ts = None
        self.cutlist = 100

    def send(self, msg):
        try:
            actstate = self.current_state
            self.current_state = self.states[self.current_state].send(msg)
            if self.current_state != actstate:
                switch_ts = pd.to_datetime(int(msg['timestamp'])*1e6)
                tt = switch_ts.strftime('%d.%m.%Y %H:%M:%S')
                d_ts = pd.Timedelta(switch_ts - self.last_ts) if self.last_ts else pd.Timedelta(0)
                self.states[actstate].add_duration(d_ts)
                self.last_ts = switch_ts
                if self.current_state == 'start-preparation':
                    self.startversuch += 1
                    self.timing = 'on'
                    self.st_timer = pd.Timedelta(0)
                if self.current_state == 'mode-off':
                    self.timing = 'off'
                    self.st_timer = pd.Timedelta(0)
                if self.current_state == 'net-parallel':
                    if self.timing:
                        self.successfulstart += 1
                if self.timing == 'on':
                    self.st_timer = self.st_timer + d_ts
                print(f"{tt} {actstate:<18} {d_ts.seconds:6d}s {self.st_timer.seconds:3d}s {msg['name']} {msg['message']:<40} {self.startversuch:>3d} {self.successfulstart:>3d} {self.timing:>3} => {self.current_state:<20}")
        except Exception as err:
            print(str(err))
    
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

def Start_FSM(msgs):
    tstart = pd.Timestamp(msgs.iloc[0]['timestamp']*1e6)
    tend = pd.Timestamp(msgs.iloc[-1]['timestamp']*1e6)
    tdelta = pd.Timedelta(tend-tstart).round('S')
    fsmrunner = msgFSM(tdelta)
    for index,msg in msgs.iterrows():
        fsmrunner.send(msg)
    fsmrunner.completed()