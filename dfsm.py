import warnings
import pandas as pd
class State:
    def __init__(self, name, transferfun_list):
        self._name = name
        self._transf = transferfun_list
        self._messages = []
    
    def send(self,msg):
        self._messages.append(msg)
        for transf in self._transf: # screen triggers
            if msg['name'] == transf['trigger'][:4]:
                return transf['new-state']
        return self._name

class msgFSM:
    def __init__(self):
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
                { 'trigger':'1267 Demand gas leakage check gas train 2', 'new-state':'start-preparation'},
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
        self.timing = 'off'
        self.last_ts = None
        self.cutlist = 10

    def send(self, msg):
        try:
            actstate = self.current_state
            self.current_state = self.states[self.current_state].send(msg)
            if self.current_state != actstate:
                switch_ts = pd.to_datetime(int(msg['timestamp'])*1e6)
                tt = switch_ts.strftime('%d.%m.%Y %H:%M:%S')
                d_ts = pd.Timedelta(switch_ts - self.last_ts).round('S') if self.last_ts else pd.Timedelta(0).round('S')
                self.last_ts = switch_ts
                if self.current_state == 'start-preparation':
                    self.startversuch += 1
                    self.timing = 'on'
                if self.current_state == 'mode-off':
                    self.timing = 'off'
                print(f"{tt} Δ[{str(d_ts)}] {msg['name']} {msg['message']:<40} {self.startversuch:>3d} {self.timing:>3} {actstate:<20} => {self.current_state:<20}")
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
        
        print('''

*****************************************
* Ergebnisse (c)2022 Dieter Chvatal     *
*****************************************
''')
        for state in self.states:

            alarms, alu = filter_messages(self.states[state]._messages, 800)
            al = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in alu[:self.cutlist]])

            warnings, wru = filter_messages(self.states[state]._messages, 700)
            wn = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in wru[:self.cutlist]])

            print(
f"""{state}:
 Messages: {len(self.states[state]._messages)} 
 Alarms   total:{alarms:3d} unique:{len(alu):3d}
 top ten:
{al}
 Warnings total:{warnings:3d} unique{len(wru):3d}
 top ten:
{wn}

""")
        return print('completed')

def Start_FSM(msgs):
    fsmrunner = msgFSM()
    for index,msg in msgs.iterrows():
        fsmrunner.send(msg)