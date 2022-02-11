import pandas as pd
import numpy as np
from dfsm import msgFSM

def Start_FSM(msgs):
    fsmrunner = msgFSM()
    for index,msg in msgs.iterrows():
        #print(msg['message'])
        fsmrunner.send(msg)
    return fsmrunner.completed()

messages = pd.read_pickle('1184199_messages.pkl').reset_index()
m = messages[messages.name != '9007'] # filter out hourly messages
m = m[:2000]
Start_FSM(m)

