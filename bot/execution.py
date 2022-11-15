# import httplib
import http.client
# import urllib
import v20
from datetime import datetime
import pandas as pd
import mplfinance as mpf

class Execution(object):
    # def __init__(self, domain,port,ssl,application, access_token, date_format,account_id,tf,instruments):
    def __init__(self, domain,port,ssl,application, access_token, account_id,tf,instruments):
        self.domain = domain
        self.port=port
        self.ssl=ssl
        self.application=application
        self.access_token = access_token
        # self.date_format=date_format
        self.account_id = account_id
        self.tf=tf
        self.instruments=instruments
        self.conn = self.obtain_connection()
        
        return

    def obtain_connection(self):
        # return httplib.HTTPSConnection(self.domain)
        return  http.client.HTTPSConnection(self.domain)
    
    
    def connect_to_candles(self):
        try:
            ctx_candles = v20.Context(
                 self.domain,
                 self.port,
                 self.ssl,
                 application=self.application,
                 token=self.access_token,
                #  datetime_format=self.date_format
            )
            kwargs={}
            kwargs['granularity']='M'+str(self.tf)
            kwargs['price']='MBA'
            
            response=ctx_candles.instrument.candles(self.instruments,**kwargs)
            if str(response.status) == "200":
                # df=pd.DataFrame([],columns=['DateTime','Open','High','Low','Close','Volume'])              
                data=[]
                for candle in response.get('candles',200):
                    data.append([candle.time,candle.mid.o,candle.mid.h,candle.mid.l,candle.mid.c])
                df=pd.DataFrame(data,columns=['DateTime','Open','High','Low','Close'])  
                
                # df.index=pd.DatetimeIndex(df.index)
                df.DateTime = pd.to_datetime(df.DateTime)
                # df.index = df.DateTime
                df.to_csv('/Users/apple/Documents/code/PythonX86/OandaAPI/Output/historical_df.csv', mode='w', index=0)
                print('saved historicalCandles')
                
                # Show the chart
                # mc = mpf.make_marketcolors(up='limegreen',down='red',inherit=True) # Create my own `marketcolors` to use with the `nightclouds` style:
                # s  = mpf.make_mpf_style(base_mpf_style='nightclouds',marketcolors=mc,gridstyle='') # Create a new style based on `nightclouds` but with my own `marketcolors`:
                # mpf.plot(df,type='candle',style=s,show_nontrading = False,block = True, tight_layout=True,returnfig = True,title='AUDUSD 5min')
                # mpf.show()
                
                # print(data)
                
                return df

            
        except Exception as e:
            print("Caught exception when connecting to candles\n" + str(e))
        
        return

    
    
    def execute_order(self, event):
        ctx=v20.Context(
                 self.domain,
                 self.port,
                 self.ssl,
                 application=self.application,
                 token=self.access_token,
                #  datetime_format=self.date_format
        )
        
        response=ctx.order.market(
             self.account_id,
             instrument=event.instrument,
             units=event.units,
             type=event.order_type,
             side=event.side
        )
        
        print(datetime.fromtimestamp(int(datetime.now().timestamp())),response)
        
        return