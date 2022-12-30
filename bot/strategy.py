from datetime import datetime
from event import OrderEvent
from allStrategies import RiskManage,Strategies
from settings import API_DOMAIN, ACCESS_TOKEN
from tradeSetup import RR
import pandas as pd
import time

class TestRandomStrategy(object):
    def __init__(self,accountDetails,instrument,events,df,df_instruments,direction,tf):
        self.domain=API_DOMAIN
        self.token=ACCESS_TOKEN
        self.instrument = instrument
        self.units = 0
        self.events = events
        self.direction = direction
        self.tf=tf
        self.df=df
        self.rr=RR
        self.df_instruments=df_instruments
        self.ifBarClosed=False
        self.data=[]
        self.justnow=''
        self.res_dict = {
            'Open':'first',
            'High':'max',
            'Low':'min',
            'Close': 'last'
            }
        self.close=0
        self.accountDetails=accountDetails
        
    def resample_to_candles(self,event):
        ifBarClosed=False
        if event.type == 'TICK':
            ts=datetime.timestamp(datetime.strptime(event.time[:16],'%Y-%m-%dT%H:%M'))
            self.data.append([event.time,event.ask])
            # test ticks
            # self.df_ticks=pd.DataFrame(self.data, columns=['DateTime','Ask'])
            # self.df_ticks.DateTime = pd.to_datetime(self.df_ticks.DateTime)
            # self.df_ticks.to_csv('/Users/apple/Documents/code/PythonX86/OandaAPI/Output/df_ticks.csv', mode='w', index=1)
            if ts/(self.tf*60)==ts//(self.tf*60) and self.justnow!=ts:  
                self.close=event.ask
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
    
    def calculate_signals(self, event):
        ifBarClosed=self.resample_to_candles(event)
        st=Strategies()
        rm=RiskManage()
        action=st._RSI(self.df)
        # for test
        # action='SELL'
        # ifBarClosed=True
        
        # print(decimal,SL,TP)
        if ifBarClosed:
            print(datetime.fromtimestamp(int(datetime.now().timestamp())),event.instrument,self.tf,'min Bar Closed')
            if action=='BUY' and action==self.direction.upper():
                decimal=int(self.df_instruments.loc[self.instrument,'pipLocation'])
                SL=str(rm.SL(self.df,decimal,action))
                TP=str(rm.TP(self.df,decimal,action,self.rr))
                self.units=(float(self.accountDetails['account']['balance'])*0.01/(self.close-float(SL)))//float(self.df_instruments.loc[self.instrument,'minimumTradeSize'])*float(self.df_instruments.loc[self.instrument,'minimumTradeSize'])
                # print('self.accountDetails*0.02',float(self.accountDetails['account']['balance'])*0.02)
                # print('close',self.close)
                # print('SL:',SL)
                # print('units:',self.units)
                
                print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Place Order:',action,event.instrument,self.units,'SL:',SL,'TP:',TP)
                order = OrderEvent(
                    self.instrument, self.units, 'MARKET', action,SL,TP
                )
                self.events.put(order)
                
            elif action=='SELL' and action==self.direction.upper():
                decimal=int(self.df_instruments.loc[self.instrument,'pipLocation'])
                SL=str(rm.SL(self.df,decimal,action))
                TP=str(rm.TP(self.df,decimal,action,self.rr))
                self.units=(float(self.accountDetails['account']['balance'])*0.01/(float(SL)-self.close))//float(self.df_instruments.loc[self.instrument,'minimumTradeSize'])*float(self.df_instruments.loc[self.instrument,'minimumTradeSize'])
                # print('self.accountDetails*0.02',float(self.accountDetails['account']['balance'])*0.02)
                # print('close',self.close)
                # print('SL:',SL)
                # print('units:',self.units)
                
                order = OrderEvent(
                    self.instrument, -1*self.units, 'MARKET', action,SL,TP
                )
                print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Place Order:',action,event.instrument,self.units,'SL:',SL,'TP:',TP)
                self.events.put(order)
                
            # elif event.ask >10*10*decimal+
                
            
            
            
        
        
        return