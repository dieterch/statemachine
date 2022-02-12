import warnings
import pandas as pd

def prime(fn): # I guess this is needed to 'prime' the generator
    def wrapper(*args, **kwargs):
        v = fn(*args, **kwargs)
        v.send(None)
        return v
    return wrapper

class engine:
    pass


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


class State:
    def __init__(self, name, transferfun_list):
        self._name = name
        self._transf = transferfun_list
        self._messages = []
    
    def send(self,msg):
        self._messages.append(msg)
        for transf in self._transf: # screen triggers
            if msg['name'] == transf['trigger']:
                return transf['state']
        return self._name

class msgFSM:
    def __init__(self):
        self.states = {
            'coldstart': State('coldstart',[
                { 'trigger':'1254', 'state':'mode-off'}]),
            'mode-off':  State('mode-off',[
                { 'trigger':'1226', 'state': 'mode-manual'},
                { 'trigger':'1227', 'state':'mode-automatic'}]),
            'mode-manual': State('mode-manual',[
                { 'trigger':'1265', 'state':'start-preparation'},
                { 'trigger':'1225', 'state':'mode-off'},
                { 'trigger':'1227', 'state':'mode-automatic'}]),
            'mode-automatic': State('mode-automatic',[
                { 'trigger':'1265', 'state':'start-preparation'},
                { 'trigger':'1225', 'state':'mode-off'},
                { 'trigger':'1226', 'state':'mode-manual'}]),
            'start-preparation': State('start-preparation',[
                { 'trigger':'1259', 'state':'coldstart'},
                { 'trigger':'1249', 'state': 'starter'}]),
            'starter': State('starter',[
                { 'trigger':'3225', 'state':'hochlauf'}]),
            'hochlauf': State('hochlauf',[
                { 'trigger':'2124', 'state':'idle'}]),             
            'idle': State('idle',[
                { 'trigger':'1259', 'state':'coldstart'}])             
        }
        self.current_state = 'coldstart'
        self.counter = 0

    def send(self, msg):
        try:
            self.current_state = self.states[self.current_state].send(msg)
            #print('|',self.counter, ' ', self.current_state,' ',msg['name'],msg['message'])
            self.counter += 1
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

        for state in self.states:

            alarms, alu = filter_messages(self.states[state]._messages, 800)
            al = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in alu[:10]])

            warnings, wru = filter_messages(self.states[state]._messages, 700)
            wn = "".join([f"{line['anz']:3d} {line['msg']}\n" for line in wru[:10]])

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