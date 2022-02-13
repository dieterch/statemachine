import pandas as pd
import numpy as np
from dfsm import msgFSM, Start_FSM

print('''
\033[H\033[J
**************************************
* FSM(c)2022 Dieter Chvatal          *
**************************************
''')

messages = pd.read_pickle('1184199_messages.pkl').reset_index()
#m = messages[messages.name != '9007'] # filter out hourly messages
m = messages[:]
Start_FSM(m)