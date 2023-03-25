import dmyplant2
dmyplant2.cred()
mp = dmyplant2.MyPlant(0)
try:
    mp.login()
except Exception as e:
    print(e)
print('\nLogin successful')
