#Finite State Machine
# built by Coroutines as states( enhanced Generators )
# and if and else as transition function
#
# Example regular Expression ab*c
#

def prime(fn):
    def wrapper(*args, **kwargs):
        v = fn(*args, **kwargs)
        v.send(None)
        return v
    return wrapper

class RegexFSM:
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
                print('\nStart, go to Q1')
                self.current_state = self.q1
            else:
                print('Start, Break')
                break
    
    @prime
    def _create_q1(self):
        while True:
            char = yield
            if char == 'b':
                print('Q1, go to Q2')
                self.current_state = self.q2
            elif char == 'c':
                print('Q1, go to Q3')
                self.current_state = self.q3
            else:
                print('Q1, Break')
                break

    @prime
    def _create_q2(self):
        while True:
            char = yield
            if char == 'b':
                print('Q2, go to Q2')
                self.current_state = self.q2
            elif char == 'c':
                print('Q2, go to Q3')
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
    evaluator = RegexFSM()
    for ch in text:
        evaluator.send(ch)
    return evaluator.does_match()

print(grep_regex("a"))
print(grep_regex("abc"))
print(grep_regex("abbbbbbbc"))
