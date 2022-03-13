import pandas as pd
import numpy as np
from tqdm.auto import tqdm
import dmyplant2


# States und Transferfunktionen, Sammeln von Statebezogenen Daten ... 
class State:
    def __init__(self, statename, transferfun_list):
        self._statename = statename
        self._transferfunctions = transferfun_list
        self._trigger = False
    
    def send(self,msg):
        for transfun in self._transferfunctions: # screen triggers
            self._trigger = msg['name'] == transfun['trigger'][:4]
            if self._trigger:
                return transfun['new-state']
        return self._statename

    def trigger_on_vector(self, vector):
        vector['currentstate'] = self.send(vector['msg'])
        vector['statechange'] = self._trigger
        if self._trigger:
            vector['laststate'] = self._statename
            vector['laststate_ts'] = vector['msg']['timestamp']
        return vector

# SpezialFall Loadram, hier wird ein berechneter Statechange ermittelt.
class LoadrampState(State):
    def __init__(self, statename, transferfun_list, e):
        self._e = e
        self._full_load_timestamp = None
        self._loadramp = self._e['rP_Ramp_Set'] or 0.625 # %/sec
        self._default_ramp_duration = int(100.0 / self._loadramp * 1e3)
        super().__init__(statename, transferfun_list)

    def trigger_on_vector(self, vector):
        vector = super().trigger_on_vector(vector)
        if self._full_load_timestamp == None:
            self._full_load_timestamp = int(vector['msg']['timestamp']) + self._default_ramp_duration
        if int(vector['msg']['timestamp']) >= self._full_load_timestamp: # now switch to 'targetoperation'
                vector['msg'] = {'name':'9047', 'message':'Target load reached (calculated)','timestamp':self._full_load_timestamp,'severity':600}
                self._full_load_timestamp = None
                vector['statechange'] = True
                vector['currentstate'] = 'targetoperation'
                vector['laststate'] = self._statename
                vector['laststate_ts'] = vector['msg']['timestamp']
                return vector
        else:
            return vector
        

# dataClass FSM
class operationFSM:
    def __init__(self, e):
        self._e = e
        self._initial_state = 'standstill'
        self._states = {
                'standstill': State('standstill',[
                    { 'trigger':'1231 Request module on', 'new-state': 'startpreparation'},            
                    ]),
                'startpreparation': State('startpreparation',[
                    { 'trigger':'1249 Starter on', 'new-state': 'starter'},
                    { 'trigger':'1232 Request module off', 'new-state': 'standstill'}
                    ]),
                'starter': State('starter',[
                    { 'trigger':'3225 Ignition on', 'new-state':'speedup'},
                    { 'trigger':'1232 Request module off', 'new-state':'standstill'}
                    ]),
                'speedup': State('speedup',[
                    { 'trigger':'2124 Idle', 'new-state':'idle'},
                    { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                    ]),             
                'idle': State('idle',[
                    { 'trigger':'2139 Request Synchronization', 'new-state':'synchronize'},
                    { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                    ]),
                'synchronize': State('synchronize',[
                    { 'trigger':'1235 Generator CB closed', 'new-state':'loadramp'},                
                    { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                    ]),             
                'loadramp': LoadrampState('loadramp',[
                    { 'trigger':'9047 Target load reached', 'new-state':'targetoperation'},
                    { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                    ], e),             
                'targetoperation': State('targetoperation',[
                    { 'trigger':'1232 Request module off', 'new-state':'rampdown'},
                    ]),
                'rampdown': State('rampdown',[
                    { 'trigger':'1236 Generator CB opened', 'new-state':'coolrun'},
                    { 'trigger':'1231 Request module on', 'new-state':'targetoperation'},
                    ]),
                'coolrun': State('coolrun',[
                    { 'trigger':'1234 Operation off', 'new-state':'runout'},
                    { 'trigger':'3226 Ignition off', 'new-state':'standstill'}
                    ]),
                'runout': State('runout',[
                    { 'trigger':'3226 Ignition off', 'new-state':'standstill'},
                    { 'trigger':'1231 Request module on', 'new-state': 'startpreparation'},            
                ])
            }

    @property
    def initial_state(self):
        return self._initial_state

    @property
    def states(self):
        return self._states

class demoFSM:
    def __init__(self, e, successtime=600):
        self._e = e
        self._successtime = successtime

        self.load_messages(e)

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

        fsmStates = operationFSM(self._e)
        self.states = fsmStates.states

        self.current_service_selector = '???'
        self._in_operation = '???'
        self.current_state = fsmStates.initial_state
        self.last_ts = pd.to_datetime(self.first_message)
        self.status_vector = {
            'statechange':True,
            'laststate': 'init',
            'laststate_ts': self.first_message.timestamp() * 1e3,
            'currentstate': self.current_state,
            'in_operation': 'off',
            'service_selector': '???'
        }

        self._starts = []
        self._starts_counter = 0

        # for initialize some values for collect_data.
        self._runlog = []
        self._runlogdetail = []


        self.results = {
            'starts': [],
            'starts_counter':0,
            'stops': [
            {
                'run2':False,
                'no': 0,
                'mode': self.status_vector['service_selector'],
                'starttime': self.status_vector['laststate_ts'],
                'endtime': pd.Timestamp(0),
                'alarms':[],
                'warnings':[]                
            }],
            'stops_counter':0,
            'runlog': []
        }

    @property
    def result(self):
        for startversuch in self._starts:
            startversuch['count_alarms'] = len(startversuch['alarms'])
            startversuch['count_warnings'] = len(startversuch['warnings'])
        return pd.DataFrame(self._starts)


    ## message handling
    def load_messages(self,e, p_from=None, p_to=None):
        self._messages = e.get_messages(p_from, p_to) [2031:2500]
        self.first_message = pd.Timestamp(self._messages.iloc[0]['timestamp']*1e6)
        self.last_message = pd.Timestamp(self._messages.iloc[-1]['timestamp']*1e6)
        self._period = pd.Timedelta(self.last_message - self.first_message).round('S')
        self.count_messages = self._messages.shape[0]

    def msgtxt(self, msg, idx=0):
        return f"{idx:>06} {msg['severity']} {msg['timestamp']} {pd.to_datetime(int(msg['timestamp'])*1e6).strftime('%d.%m.%Y %H:%M:%S')}  {msg['name']} {msg['message']}"

    def msg_smalltxt(self, msg, idx=0):
        return f"{msg['severity']} {pd.to_datetime(int(msg['timestamp'])*1e6).strftime('%d.%m.%Y %H:%M:%S')}  {msg['name']} {msg['message']}"

    def save_messages(self, fn):
        with open(fn, 'w') as f:
            for index, msg in self._messages.iterrows():
                f.write(self.msgtxt(msg, index)+'\n')
                #f.write(f"{index:>06} {msg['severity']} {msg['timestamp']} {pd.to_datetime(int(msg['timestamp'])*1e6).strftime('%d.%m.%Y %H:%M:%S')}  {msg['name']} {msg['message']}\n")
                if 'associatedValues' in msg:
                    if msg['associatedValues'] == msg['associatedValues']:  # if not NaN ...
                        f.write(f"{pf(msg['associatedValues'])}\n\n")

    def save_runlog(self, fn):
        if len(self._runlog):
            with open(fn, 'w') as f:
                for line in self._runlog:
                    f.write(line + '\n')


#################################################################################################################
    ### die Finite State Machine selbst:
    #1225 Service selector switch Off
    #1226 Service selector switch Manual
    #1227 Service selector switch Automatic
    def _fsm_Service_selector(self, msg):
        if msg['name'] == '1225 Service selector switch Off'[:4]:
            self.current_service_selector = 'OFF'
            self.status_vector['service_selector'] = 'OFF'
        if msg['name'] == '1226 Service selector switch Manual'[:4]:
            self.current_service_selector = 'MANUAL'
            self.status_vector['service_selector'] = 'MANUAL'
        if msg['name'] == '1227 Service selector switch Automatic'[:4]:
            self.current_service_selector = 'AUTO'
            self.status_vector['service_selector'] = 'AUTO'

    def _fsm_collect_alarms(self, msg):
        if self._in_operation == 'on':
            if msg['severity'] == 800:
                self._starts[-1]['alarms'].append({'state':self.current_state, 'msg': msg})
                self.results['starts'][-1]['alarms'].append({'state':self.status_vector['currentstate'], 'msg': msg})
            if msg['severity'] == 700:
                self._starts[-1]['warnings'].append({'state':self.current_state, 'msg': msg})
                self.results['starts'][-1]['warnings'].append({'state':self.status_vector['currentstate'], 'msg': msg})
        elif self._in_operation == 'off':
            if msg['severity'] == 800:
                self.results['stops'][-1]['alarms'].append({'state':self.status_vector['currentstate'], 'msg': msg})
            if msg['severity'] == 700:
                self.results['stops'][-1]['warnings'].append({'state':self.status_vector['currentstate'], 'msg': msg})

    def _fsm_Operating_Cycle2(self):
        if self.status_vector['statechange']:
            if self.status_vector['currentstate'] == 'standstill':
                if self.status_vector['in_operation'] == 'on':
                    self.results['starts'][-1]['endtime'] = pd.to_datetime(self.status_vector['laststate_ts']*1e6 )
                    if 'start_targetoperation' in self.results['starts'][-1]['timing']:
                        #successful if the targetoperation run was longer than specified
                        self.results['starts'][-1]['success'] = True #wird implementiert, wenn das timing dann stimmt
                        #(self.results['starts'][-1]['targetoperation'] > self._successtime) 
                self.status_vector['in_operation'] = 'off'
                self.results['stops'].append({
                    'run2':False,
                    'no': self.results['stops_counter'],
                    'mode': self.status_vector['service_selector'],
                    'starttime': self.status_vector['laststate_ts'],
                    'endtime': pd.Timestamp(0),
                    'alarms':[],
                    'warnings':[]
                })

            if self.status_vector['currentstate'] == 'startpreparation':
                self.results['stops'][-1]['endtime'] = self.status_vector['laststate_ts']
                # apends a new record to the Starts list.
                self.results['starts'].append({
                    'run2':False,
                    'no':self.results['starts_counter'],
                    'success': False,
                    'mode':self.status_vector['service_selector'],
                    'starttime': pd.to_datetime(self.status_vector['laststate_ts']*1e6 ),
                    'endtime': pd.Timestamp(0),
                    'cumstarttime': pd.Timedelta(0),
                    'timing': {},
                    'alarms': [],
                    'warnings': [],
                    'maxload': np.nan,
                    'ramprate': np.nan
                })
                self.results['starts_counter'] += 1 # index for next start
                self.status_vector['in_operation'] = 'on'
            elif self.status_vector['in_operation'] == 'on': # and actstate != FSM.initial_state:            
                self.results['starts'][-1]['timing']['start_'+ self.status_vector['currentstate']] = self.status_vector['laststate_ts'] 
                self.results['starts'][-1]['timing']['end_'+ self.status_vector['currentstate']] = self.status_vector['msg']['timestamp'] 

            _logline= {
                'laststate': self.status_vector['laststate'],
                'laststate_ts': pd.to_datetime(self.status_vector['laststate_ts']*1e6).strftime('%d.%m.%Y %H:%M:%S'),
                'msg': self.status_vector['msg']['name'] + ' ' + self.status_vector['msg']['message'],
                'currenstate': self.status_vector['currentstate'],
                'currentstate_ts': pd.to_datetime(self.status_vector['msg']['timestamp']*1e6).strftime('%d.%m.%Y %H:%M:%S'),
                'starts': len(self.results['starts']),
                'Successful_starts': len([s for s in self.results['starts'] if s['success']]),
                'operation': self.status_vector['in_operation'],
                'mode': self.status_vector['service_selector'],
            }
            self.results['runlog'].append(_logline)
            #_logtxt = f"{new_transition_time.strftime('%d.%m.%Y %H:%M:%S')} |{actstate:<18} {_to_sec(duration):>10.1f}s {_to_sec(self._timer):>10.1f}s {msg['name']} {msg['message']:<40} {len(self._starts):>3d} {len([s for s in self._starts if s['success']]):>3d} {self._in_operation:>3} {self.current_service_selector:>6} => {self.current_state:<20}"
            #_logtxt = f"{switch_point.strftime('%d.%m.%Y %H:%M:%S')} |{actstate:<18} {_to_sec(duration):8.1f}s {msg['name']} {msg['message']:<40} {len(self._starts):>3d} {len([s for s in self._starts if s['success']]):>3d} {self._in_operation:>3} {self.current_service_selector:>4} => {self.current_state:<20}"
            #self._runlog.append(_logtxt)


    def _fsm_Operating_Cycle(self, actstate, act_transition_time, newstate, new_transition_time, duration, msg):
        def _to_sec(time_object):
            return float(time_object.seconds) + float(time_object.microseconds) / 1e6
        # Start Preparatio => the Engine ist starting
        if self.current_state == 'startpreparation':
            # apends a new record to the Starts list.
            self._starts.append({
                'run2':False,
                'no':self._starts_counter,
                'success': False,
                'mode':self.current_service_selector,
                'starttime': new_transition_time,
                'endtime': pd.Timestamp(0),
                'cumstarttime': pd.Timedelta(0),
                'timing': {},
                'alarms': [],
                'warnings': [],
                'maxload': np.nan,
                'ramprate': np.nan
            })
            self._starts_counter += 1 # index for next start
            # indicate a 
            self._in_operation = 'on'
            self._timer = pd.Timedelta(0)
        elif self._in_operation == 'on': # and actstate != FSM.initial_state:
            self._timer = self._timer + duration

            if actstate in self._starts[-1]: # add all duration a start is in a certain state ( important if the engine switches back and forth between states, e.g. Forsa Hartmoor M4, 18.1.2022 fff)
                self._starts[-1][actstate] += _to_sec(duration)
            else:
                self._starts[-1][actstate] = _to_sec(duration) #if actstate != 'targetoperation' else duration.round('S')
            
            self._starts[-1]['timing']['start_'+ actstate] = act_transition_time 
            self._starts[-1]['timing']['end_'+ actstate] = new_transition_time 

            if actstate not in ['targetoperation','rampdown','coolrun','aftercooling']: 
                self._starts[-1]['cumstarttime'] = _to_sec(self._timer)

        # if self.current_state == 'targetoperation':
        #     if self._in_operation == 'on':
        #         self._starts[-1]['success'] = True   # wenn der Start bis hierhin kommt, ist er erfolgreich.

        # Ein Motorlauf(-versuch) is zu Ende. 
        if self.current_state == 'standstill': #'mode-off'
        #if actstate == 'loadramp': # übergang von loadramp to 'targetoperation'
            if self._in_operation == 'on':
                self._starts[-1]['endtime'] = new_transition_time
                if 'targetoperation' in self._starts[-1]:
                    #successful if the targetoperation run was longer than specified
                    self._starts[-1]['success'] = (self._starts[-1]['targetoperation'] > self._successtime) 
            self._in_operation = 'off'
            self._timer = pd.Timedelta(0)

        _logline= {
            'actstate': actstate,
            'start_time': act_transition_time.strftime('%d.%m.%Y %H:%M:%S'),
            'msg': msg['name'] + ' ' + msg['message'],
            'currenstate': self.current_state,
            'new_transition_time': new_transition_time.strftime('%d.%m.%Y %H:%M:%S'),
            'duration': _to_sec(duration),
            '_timer': _to_sec(self._timer),
            'starts': len(self._starts),
            'Successful_starts': len([s for s in self._starts if s['success']]),
            'operation': self._in_operation,
            'mode': self.current_service_selector,
        }
        self._runlog.append(_logline)
        #_logtxt = f"{new_transition_time.strftime('%d.%m.%Y %H:%M:%S')} |{actstate:<18} {_to_sec(duration):>10.1f}s {_to_sec(self._timer):>10.1f}s {msg['name']} {msg['message']:<40} {len(self._starts):>3d} {len([s for s in self._starts if s['success']]):>3d} {self._in_operation:>3} {self.current_service_selector:>6} => {self.current_state:<20}"
        #_logtxt = f"{switch_point.strftime('%d.%m.%Y %H:%M:%S')} |{actstate:<18} {_to_sec(duration):8.1f}s {msg['name']} {msg['message']:<40} {len(self._starts):>3d} {len([s for s in self._starts if s['success']]):>3d} {self._in_operation:>3} {self.current_service_selector:>4} => {self.current_state:<20}"
        #self._runlog.append(_logtxt)

    def _collect_data(self, actstate, msg):
        if self.current_state != actstate:
            transition_time = pd.to_datetime(float(msg['timestamp'])*1e6)
            d_ts = pd.Timedelta(transition_time - self.last_ts) if self.last_ts else pd.Timedelta(0)
            self._fsm_Operating_Cycle(actstate, self.last_ts, self.current_state, transition_time, d_ts, msg)
            self.last_ts = transition_time

    def handle_states(self, lactstate, lcurrent_state, msg):

        # Sonderbehandlung Ende der Phase loadramp
        if self._target_load_message:
            new_state = self.states[lcurrent_state].send(msg)  # die Message kommt in den messages vor, normal behandeln        

        else: # die 'target load reached' message kommt nicht vor => die Zeit bis Vollast muß in RUN 1 geschätzt werden ...
            #die FSM hat die Phase 'loadramp' noch nicht erreicht 
            if self.full_load_timestamp == None or int(msg['timestamp']) < self.full_load_timestamp:
                new_state = self.states[lcurrent_state].send(msg)           
            elif int(msg['timestamp']) >= self.full_load_timestamp: # now switch to 'targetoperation'
                dmsg = {'name':'9047', 'message':'Target load reached (calculated)','timestamp':self.full_load_timestamp,'severity':600}
                new_state = self.states[lcurrent_state].send(dmsg)            
                # Inject the message , collect the data
                self._collect_data(lactstate, dmsg)
                # rest the algorithm for the next cycle.
                self.full_load_timestamp = None
                lactstate = lcurrent_state

            # Algorithm to switch from 'loadramp to' 'targetoperation'
            # direkt bein Umschalten das Ende der Rampe berechnen

            if lcurrent_state == 'loadramp' and self.full_load_timestamp == None:  
                self.full_load_timestamp = int(msg['timestamp']) + self._default_ramp_duration

        return lactstate, new_state


    def call_trigger_states(self):
        return self.states[self.status_vector['currentstate']].trigger_on_vector(self.status_vector)
                  
    ## FSM Entry Point.
    def run1(self, enforce=False):
        if len(self._starts) == 0 or enforce or not ('run2' in self._starts[0]):
            self._starts = []
            self._starts_counter = 0      
            for i,msg in tqdm(self._messages.iterrows(), total=self._messages.shape[0], ncols=80, mininterval=1, unit=' messages', desc="FSM"):
                last_state = self.current_state
                self.status_vector['msg'] = msg
                self.status_vector = self.call_trigger_states()   
                last_state, self.current_state = self.handle_states(last_state, self.current_state, msg)
                #print(f"o {last_state:18} {self.current_state:18} {self.msgtxt(msg, i)}")
                self._runlogdetail.append(f"= {str(self.status_vector['statechange']):6} {self.status_vector['laststate']:18} {pd.Timestamp(self.status_vector['msg']['timestamp']*1e6).strftime('%d.%m.%Y %H:%M:%S')} {self.status_vector['currentstate']:18} {self.msg_smalltxt(self.status_vector['msg'])}")
                self._fsm_Service_selector(msg)
                self._fsm_collect_alarms(msg)
                self._fsm_Operating_Cycle2()
                self._collect_data(last_state, msg)









#########################################################################################################################
    def dorun2(self, index_list, startversuch):
                ii = startversuch['no']
                index_list.append(ii)

                if not startversuch['run2']:

                    data = dmyplant2.get_cycle_data2(self, startversuch, max_length=None, min_length=None, silent=True)

                    if not data.empty:

                        pl, _ = dmyplant2.detect_edge_left(data, 'Power_PowerAct', startversuch)
                        #pr, _ = detect_edge_right(data, 'Power_PowerAct', startversuch)
                        #sl, _ = detect_edge_left(data, 'Various_Values_SpeedAct', startversuch)
                        #sr, _ = detect_edge_right(data, 'Various_Values_SpeedAct', startversuch)

                        self._starts[ii]['title'] = f"{self._e} ----- Start {ii} {startversuch['mode']} | {'SUCCESS' if startversuch['success'] else 'FAILED'} | {startversuch['starttime'].round('S')}"
                        #sv_lines = {k:(startversuch[k] if k in startversuch else np.NaN) for k in filterFSM.vertical_lines_times]}
                        sv_lines = [v for v in startversuch[filterFSM.vertical_lines_times]]
                        start = startversuch['starttime'];
                        
                        # lade die in run1 gesammelten Daten in ein DataFrame, ersetze NaN Werte mit 0
                        backup = {}
                        svdf = pd.DataFrame(sv_lines, index=filterFSM.vertical_lines_times, columns=['FSM'], dtype=np.float64).fillna(0)
                        svdf['RUN2'] = svdf['FSM']

                        # intentionally excluded - Dieter 1.3.2022
                        #if svdf.at['speedup','FSM'] > 0.0:
                        #        svdf.at['speedup','RUN2'] = sl.loc.timestamp() - start.timestamp() - np.cumsum(svdf['RUN2'])['starter']
                        #        svdf.at['idle','RUN2'] = svdf.at['idle','FSM'] - (svdf.at['speedup','RUN2'] - svdf.at['speedup','FSM'])
                        if svdf.at['loadramp','FSM'] > 0.0:
                                calc_loadramp = pl.loc.timestamp() - start.timestamp() - np.cumsum(svdf['RUN2'])['synchronize']
                                svdf.at['loadramp','RUN2'] = calc_loadramp

                                # collect run2 results.
                                backup['loadramp'] = svdf.at['loadramp','FSM'] # alten Wert merken
                                self._starts[ii]['loadramp'] = calc_loadramp

                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            calc_maxload = pl.val
                            try:
                                calc_ramp = (calc_maxload / self._e['Power_PowerNominal']) * 100 / svdf.at['loadramp','RUN2']
                            except ZeroDivisionError as err:
                                logging.warning(f"calc_ramp: {str(err)}")
                                calc_ramp = np.NaN
                            # doppelte Hosenträger ... hier könnte man ein wenig aufräumen :-)
                            if not np.isfinite(calc_ramp) :
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
                        self._starts[ii]['run2'] = True


    def run2(self, rda, silent=False):
        index_list = []
        if silent:
            for n, startversuch in rda.iterrows():
                self.dorun2(index_list, startversuch)
        else:
            for n, startversuch in tqdm(rda.iterrows(), total=rda.shape[0], ncols=80, mininterval=1, unit=' starts', desc="FSM Run2"):
                self.dorun2(index_list, startversuch)
        return pd.DataFrame([self._starts[s] for s in index_list])
