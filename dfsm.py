import pandas as pd
class regexFSM:
    def __init__(self):

        self.start = self._create_start()
        self.start.send(None) # Advance to first yield
        
        self.q1 = self._create_q1()
        self.q1.send(None) # Advance to first yield
        
        self.q2 = self._create_q2()
        self.q2.send(None) # Advance to first yield
        
        self.q3 = self._create_q3()
        self.q3.send(None) # Advance to first yield

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

    #@prime
    def _create_start(self):
        while True:
            char = yield
            if char == 'a':
                print('S  -> Q1')
                self.current_state = self.q1
            else:
                print('Start, Break')
                break
    
    #@prime
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

    #@prime
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

    #@prime
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

        self.start = self._create_start()
        self.start.send(None) # Advance to first yield
        
        self.mode_off = self._create_mode_off()
        self.mode_off.send(None) # Advance to first yield
        
        self.mode_manual = self._create_mode_manual()
        self.mode_manual.send(None) # Advance to first yield
        
        self.mode_automatic = self._create_mode_automatic()
        self.mode_automatic.send(None) # Advance to first yield

        self.startprep = self._create_startprep()
        self.startprep.send(None) # Advance to first yield

        self.stop = self._create_stop()
        self.stop.send(None) # Advance to first yield

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

    def _create_start(self):
        while True:
            msg = yield
            self._result = {
                'warnings':[],
                'alarms':[],
                'operations':[]
            }
            if msg['severity'] == 600:
                if msg['name'] == '1254':
                    lr = {
                        'mode':'FSM-start',
                        'start':{
                            'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                            'msg':msg['message']
                        }
                    }
                    self._result.update(lr)
                    self._summary.append(self._result)
                    self.current_state = self.mode_off
                self._result['operations'].append(msg)
            elif msg['severity'] == 700:
                self._result['warnings'].append(msg)
            elif msg['severity'] == 800:
                self._result['alarms'].append(msg)
    
    def _create_mode_off(self):
        while True:
            msg = yield
            self._result = {
                'warnings':[],
                'alarms':[],
                'operations':[]
            }
            if msg['severity'] == 600:
                if msg['name'] == '1226':
                    lr = {
                        'mode':'mode-manual',
                        'start':{
                            'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                            'msg':msg['message']
                        }
                    }
                    self._result.update(lr)
                    self._summary.append(self._result)
                    # switch to state Startvorbereitung 
                    self.current_state = self.mode_manual
                elif msg['name'] == '1227':
                    lr = {
                        'mode':'mode-automatic',
                        'start':{
                            'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                            'msg':msg['message']
                        }
                    }
                    self._result.update(lr)
                    self._summary.append(self._result)
                    self.current_state = self.mode_automatic                    
                self._result['operations'].append(msg)
            elif msg['severity'] == 700:
                self._result['warnings'].append(msg)
            elif msg['severity'] == 800:
                self._result['alarms'].append(msg)

    def _create_mode_manual(self):
        while True:
            msg = yield
            self._result = {
                'warnings':[],
                'alarms':[],
                'operations':[]
            }
            if msg['severity'] == 600:
                if msg['name'] == '1259':
                    lr = {
                        'mode':'start-preparation',
                        'start':{
                            'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                            'msg':msg['message']
                        }
                    }
                    self._result.update(lr)
                    self._summary.append(self._result)
                    self.current_state = self.startprep
                elif msg['name'] == '1225':
                    lr = {
                        'mode':'mode-off',
                        'start':{
                            'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                            'msg':msg['message']
                        }
                    }
                    self._result.update(lr)
                    self._summary.append(self._result)
                    self.current_state = self.startprep
                    self._summary.append(self._result)
                    self.current_state = self.mode_off
                elif msg['name'] == '1227':
                    lr = {
                        'mode':'mode-automatic',
                        'start':{
                            'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                            'msg':msg['message']
                        }
                    }
                    self._result.update(lr)
                    self._summary.append(self._result)
                    self.current_state = self.mode_automatic
                self._result['operations'].append(msg)
            elif msg['severity'] == 700:
                self._result['warnings'].append(msg)
            elif msg['severity'] == 800:
                self._result['alarms'].append(msg)

    def _create_mode_automatic(self):
        while True:
            msg = yield
            self._result = {
                'warnings':[],
                'alarms':[],
                'operations':[]
            }
            if msg['severity'] == 600:
                if msg['name'] == '1259':
                    lr = {
                        'mode':'start-preparation',
                        'start':{
                            'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                            'msg':msg['message']
                        }
                    }
                    self._result.update(lr)
                    self._summary.append(self._result)
                    self.current_state = self.startprep
                elif msg['name'] == '1225':
                    lr = {
                        'mode':'mode-off',
                        'start':{
                            'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                            'msg':msg['message']
                        }
                    }
                    self._result.update(lr)
                    self._summary.append(self._result)
                    self.current_state = self.startprep
                    self._summary.append(self._result)
                    self.current_state = self.mode_off
                elif msg['name'] == '1226':
                    lr = {
                        'mode':'mode-manual',
                        'start':{
                            'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                            'msg':msg['message']
                        }
                    }
                    self._result.update(lr)
                    self._summary.append(self._result)
                    self.current_state = self.mode_manual
                self._result['operations'].append(msg)
            elif msg['severity'] == 700:
                self._result['warnings'].append(msg)
            elif msg['severity'] == 800:
                self._result['alarms'].append(msg)

    def _create_startprep(self):
        while True:
            msg = yield
            if msg['severity'] == 600:
                if msg['name'] == '1260':
                    self._result['end'] = {
                        'ts':pd.Timestamp(int(msg['timestamp'])*1e6),
                        'msg':msg['message']
                    }
                    self.current_state = self.stop
                self._result['operations'].append(msg)
            elif msg['severity'] == 700:
                self._result['warnings'].append(msg)
            elif msg['severity'] == 800:
                self._result['alarms'].append(msg)

    def _create_stop(self):
        while True:
            msg = yield
            self._result['Δt'] = self._result['end']['ts'] - self._result['start']['ts'] # myplant => ms
            self.current_state = self.start
