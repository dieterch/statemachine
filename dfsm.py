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

        self.start = self._create_start()
        self.start.send(None) # Advance to first yield
        
        self.q1 = self._create_startprep()
        self.q1.send(None) # Advance to first yield
        
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
                print('Start -> Q1')
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