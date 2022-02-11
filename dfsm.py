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
            msgname = msg['name']
            if msgname in ['1259']:
                #print(f"{msg['message']}@{msg['datetime']} Start -> Startvorbereitung")
                self._result = {}
                self._result['t0'] = [msg['timestamp'], msg['message']]
                self._summary.append(self._result)
                # switch to state Startvorbereitung 
                self.current_state = self.startprep
            else:
                pass #do nothing ?
    
    def _create_startprep(self):
        while True:
            msg = yield
            msgname = msg['name']
            if msgname in ['1260']:
                #print(f"{msg['message']}@{msg['datetime']} Startvorbereitung -> Ende")
                self._result['t1'] = [msg['timestamp'], msg['message']]
                self.current_state = self.stop
            else:
                pass #do nothing ?

    def _create_stop(self):
        while True:
            msg = yield
            msgname = msg['name']
            #print(f"last msg: {msg['message']}@{msg['datetime']} Stop")
            #print(F"here i could calculate ...")
            self._result['t0->t1'] = (float(self._result['t1'][0]) - float(self._result['t0'][0])) / 1000.0 # myplant => ms
            self.current_state = self.start
