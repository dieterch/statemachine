import pandas as pd


def prime(fn): # I guess this is needed to 'prime' the generator
    def wrapper(*args, **kwargs):
        v = fn(*args, **kwargs)
        v.send(None)
        return v
    return wrapper

class regexFSM:
    def __init__(self):

        self.start = self._create_start()
        self.q1 = self._create_q1()
        self.q2 = self._create_q2()
        self.q3 = self._create_q3()
        self.current_state = self.start
        self.stopped = False
        
    def send(self, char):
        try:
            self.current_state.send(char)
        except StopIteration:
            self.stopped = True
        
    def does_match(self):
        if self.stopped:
            return False
        return self.current_state == self.q3

    @prime
    def _create_start(self):
        while True:
            char = yield
            if char == 'a':
                print('S  -> Q1')
                self.current_state = self.q1
            else:
                print('Start, Break')
                break
    
    @prime
    def _create_q1(self):
        while True:
            char = yield
            if char == 'b':
                print('Q1 -> Q2')
                self.current_state = self.q2
            elif char == 'c':
                print('Q1 -> Q3')
                self.current_state = self.q3
            else:
                print('Q1, Break')
                break

    @prime
    def _create_q2(self):
        while True:
            char = yield
            if char == 'b':
                print('Q2 -> Q2')
                self.current_state = self.q2
            elif char == 'c':
                print('Q2 -> Q3')
                self.current_state = self.q3
            else:
                print('Q2, Break')
                break

    @prime
    def _create_q3(self):
        while True:
            char = yield
            print('Q3, Completed')
            break

def grep_regex(text):
    evaluator = regexFSM()
    for ch in text:
        evaluator.send(ch)
    return evaluator.does_match()


class msgFSM:
    def __init__(self):

        self._summary = []

        # for each Finite State
        # create a Coroutine
        self.start = self._create_start()
        self.mode_off = self._create_mode_off()
        self.mode_manual = self._create_mode_manual()
        self.mode_automatic = self._create_mode_automatic()
        self.startprep = self._create_startprep()
        self.current_state = self.start
        self.stopped = False
        
    def send(self, msg):
        try:
            self.current_state.send(msg)
        except StopIteration:
            self.stopped = True
        
    def completed(self):
        """Returns the collected statistical data

        Returns:
            list: List of results dicts
        """
        return self._summary

    def _action(self,msg,tsflist, res, sum=True):
        if msg['severity'] == 600:
            for tsf in tsflist:
                if msg['name'] == tsf['key']:
                    lr = {
                        'mode':tsf['mode'],
                        'msg': msg
                    }
                    res.update(lr)
                    if sum:
                        self._summary.append(res)
                    self.current_state = tsf['fun']
            res['operations'].append(msg)
        elif msg['severity'] == 700:
            res['warnings'].append(msg)
        elif msg['severity'] == 800:
            res['alarms'].append(msg)
        return res

# inside the coroutines
# create the Transfer Functions
# use _action to simplify ...

    @prime
    def _create_start(self):
        while True:
            msg = yield
            self._result = {'warnings':[], 'alarms':[],'operations':[]}
            self._result = self._action( 
                msg,  
                [
                    { 'key':'1254', 'mode':'FSM-start', 'fun':self.mode_off}
                ], 
                self._result, 
            )
    
    @prime
    def _create_mode_off(self):
        while True:
            msg = yield
            self._result = {'warnings':[],'alarms':[],'operations':[]}
            self._result = self._action( 
                msg,  
                [
                    { 'key':'1226', 'mode':'mode-manual', 'fun':self.mode_manual},
                    { 'key':'1227', 'mode':'mode-automatic', 'fun':self.mode_automatic},
                ], 
                self._result, 
                sum = True
            )

    @prime
    def _create_mode_manual(self):
        while True:
            msg = yield
            self._result = {'warnings':[], 'alarms':[], 'operations':[] }
            self._result = self._action( 
                msg,  
                [
                    { 'key':'1259', 'mode':'startpreparation', 'fun':self.startprep},
                    { 'key':'1225', 'mode':'mode-off', 'fun':self.mode_off},
                    { 'key':'1227', 'mode':'mode-automatic', 'fun':self.mode_automatic},
                ], 
                self._result, 
            )

    @prime
    def _create_mode_automatic(self):
        while True:
            msg = yield
            self._result = {'warnings':[],'alarms':[],'operations':[]}
            self._result = self._action( 
                msg,  
                [
                    { 'key':'1259', 'mode':'startpreparation', 'fun':self.startprep},
                    { 'key':'1225', 'mode':'mode-off', 'fun':self.mode_off},
                    { 'key':'1226', 'mode':'mode-manual', 'fun':self.mode_manual},
                ], 
                self._result, 
            )

    @prime
    def _create_startprep(self):
        while True:
            msg = yield
            self._result = self._action( 
                msg,  
                [
                    { 'key':'1225', 'mode':'mode-off', 'fun':self.mode_off},                ], 
                self._result, 
            )

def Start_FSM(msgs):
    fsmrunner = msgFSM()
    for index,msg in msgs.iterrows():
        fsmrunner.send(msg)
    return fsmrunner.completed()