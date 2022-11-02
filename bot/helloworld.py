import sys
sys.path.append('/Users/apple/Documents/code/PythonX86/OandaAPI/Settings')
import v20
import pandas as pd
import configparser
import numpy as np
import matplotlib.pyplot as plt

config = configparser.ConfigParser()
config.read('/Users/apple/Documents/code/PythonX86/OandaAPI/Settings/config.cfg')

ctx=v20.Context(
    config['oanda']['hostname'],
    config['oanda']['port'],
    config['oanda']['ssl'],
    application=config['oanda']['application'],
    token=config['oanda']['access_token'],
    datetime_format=config['oanda']['date_format']
)

instrument='EUR_USD'
kwargs={}
kwargs['granularity']='M1'
kwargs['price']='MBA'
response=ctx.instrument.candles(instrument,**kwargs)

# print(response)
if str(response.status) == "200":
    closeAsk=[]
    time=[]
    for candle in response.get('candles',200):
        closeAsk.append(getattr(candle,'ask',None).c)
        time.append(getattr(candle,'time',None))
    df=pd.DataFrame({'closeAsk':closeAsk,'time':time}).set_index('time')
    df.index=pd.DatetimeIndex(df.index)
    
df['returns']=np.log(df['closeAsk']/df['closeAsk'].shift(1))
cols=[]

for momentum in [15,30,60,120]:
    col='position_%s' % momentum
    df[col]=np.sign(df['returns'].rolling(momentum).mean())
    cols.append(col)

# %matplotlib inline
strats=['returns']
for col in cols:
    strat='strategy_%s' % col.split('_')[1]
    df[strat]=df[col].shift(1)*df['returns']
    strats.append(strat)
df[strats].dropna().cumsum().apply(np.exp).plot()


plt.show()