import numpy as np
import pandas as pd
from datetime import datetime
from event import OrderEvent
# import threading

class TestRandomStrategy(object):
    def __init__(self, instrument, units, events,df,tf):
    # def __init__(self, instrument, units, events,tf,df):
        self.instrument = instrument
        self.units = units
        self.events = events
        self.ticks = 0
        self.tf=tf
        self.justnow=''
        self.data=[]
        self.df=df
        # print(df)
        # c=input('xxx')
        self.res_dict = {
            'Open':'first',
            'High':'max',
            'Low':'min',
            'Close': 'last'
            }
        self.ifBarClosed=False
    
    def resample_bar(self,event):
        ifBarClosed=False
        if event.type == 'TICK':
            ts=datetime.timestamp(datetime.strptime(event.time[:16],'%Y-%m-%dT%H:%M'))
            self.data.append([event.time,event.ask])
            
            # test ticks
            # self.df_ticks=pd.DataFrame(self.data, columns=['DateTime','Ask'])
            # self.df_ticks.DateTime = pd.to_datetime(self.df_ticks.DateTime)
            # self.df_ticks.to_csv('/Users/apple/Documents/code/PythonX86/OandaAPI/Output/df_ticks.csv', mode='w', index=1)
            
            if ts/(self.tf*60)==ts//(self.tf*60) and self.justnow!=ts:  
                # print('pass',ts/self.tf,ts//self.tf,self.justnow,ts)
                self.df_ticks=pd.DataFrame(self.data, columns=['DateTime','Ask'])
                self.df_ticks.DateTime = pd.to_datetime(self.df_ticks.DateTime)
                self.df_ticks.index = self.df_ticks.DateTime
                self.dfr = self.df_ticks.Ask.resample(str(self.tf)+'min', closed='left',label='left').agg(self.res_dict) 
                self.dfr.to_csv('/Users/apple/Documents/code/PythonX86/OandaAPI/Output/dfr.csv', mode='w', index=1)
                self.dfr.reset_index(inplace=True)
                self.dfr = pd.concat([self.df.iloc[-1:], self.dfr], ignore_index=True)
                self.dfr.index = self.dfr.DateTime
                self.dfr = self.dfr.resample(str(self.tf)+'min', closed='left',label='left').agg(self.res_dict) 
                self.dfr.reset_index(inplace=True)
                self.justnow=ts
                del self.data[0:len(self.data)-1]
                self.dfr.drop(self.dfr.index[-1], axis=0, inplace=True)
                # self.dfr.reset_index(inplace=True)
                
                if len(self.dfr.DateTime) != 0 and len(self.df.DateTime) != 0: #當有新的重組K線時
                    while self.df.iloc[-1, 0] >= self.dfr.iloc[0, 0]:  #以新的重組K線的資料為主，刪除歷史K線最後幾筆資料
                        self.df.drop(self.df.index[-1], axis=0, inplace=True)
                self.df = pd.concat([self.df, self.dfr], ignore_index=True)
                self.df.dropna(axis=0, how='any', inplace=True)  # 去掉空行
                # self.df.reset_index(drop=True) 
                self.df.to_csv('/Users/apple/Documents/code/PythonX86/OandaAPI/Output/df.csv', mode='w', index=1)
                ifBarClosed=True
        return ifBarClosed
    
    def RSI(self,DF,n=3):
        "function to calculate RSI"
        df = DF.copy()
        df['delta']=df['Close'] - df['Close'].shift(1)
        df['gain']=np.where(df['delta']>=0,df['delta'],0)
        df['loss']=np.where(df['delta']<0,abs(df['delta']),0)
        avg_gain = []
        avg_loss = []
        gain = df['gain'].tolist()
        loss = df['loss'].tolist()
        for i in range(len(df)):
            if i < n:
                avg_gain.append(np.NaN)
                avg_loss.append(np.NaN)
            elif i == n:
                avg_gain.append(df['gain'].rolling(n).mean()[n])
                avg_loss.append(df['loss'].rolling(n).mean()[n])
            elif i > n:
                avg_gain.append(((n-1)*avg_gain[i-1] + gain[i])/n)
                avg_loss.append(((n-1)*avg_loss[i-1] + loss[i])/n)
        df['avg_gain']=np.array(avg_gain)
        df['avg_loss']=np.array(avg_loss)
        df['RS'] = df['avg_gain']/df['avg_loss']
        df['RSI'] = 100 - (100/(1+df['RS']))
        df=df.drop(['RS','avg_loss','avg_gain','gain','loss','delta'],axis=1)
        # print(df)
        df.dropna(axis=0, how='any', inplace=True)

        return df
    
    def calculate_signals(self, event):
        
        # Resample the ticks to candles
        ifBarClosed=self.resample_bar(event)
        
        # resample_thread = threading.Thread(target=self.resample_bar, args=(event))
        
        df=self.df.copy()
        i=len(df)-1
        if i<3:
            return np.nan
        df['RSI']=self.RSI(df)['RSI']
        df['SMA']=df['Close'].rolling(100).mean()
        # df.loc[(df['RSI'].shift(1)<80)&(df['RSI']>=80),'Direction']='SELL'
        # df.loc[(df['RSI'].shift(1)>20)&(df['RSI']<=20),'Direction']='BUY'
        df.loc[(df['RSI'].shift(1)<80)&(df['RSI']>=80)&(df['High']<df['SMA']),'Direction']='SELL'
        df.loc[(df['RSI'].shift(1)>20)&(df['RSI']<=20)&(df['Low']>df['SMA']),'Direction']='BUY'
        df.to_csv('/Users/apple/Documents/code/PythonX86/OandaAPI/Output/df_RSI_SMA.csv',index=0) 
        
        if ifBarClosed:
            print(datetime.fromtimestamp(int(datetime.now().timestamp())),event.instrument,self.tf,'min Bar Closed')
            if df.loc[df.index[-1],'Direction']=='BUY':
                order = OrderEvent(
                    self.instrument, self.units, 'MARKET', 'BUY'
                )
                self.events.put(order)
            elif df.loc[df.index[-1],'Direction']=='SELL':
                order = OrderEvent(
                    self.instrument, self.units, 'CLOSEPOSITION', 'SELL'
                )
                self.events.put(order)
        
        return