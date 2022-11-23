from datetime import datetime
import pandas as pd
import v20

class historicalCandles():
    def __init__(self,domain,token,instruments,tf):
        self.domain=domain
        self.access_token=token
        self.tf=tf
        self.instruments=instruments
        
        
    
    def connect_to_candles(self):
        try:
            ctx_candles = v20.Context(
                 self.domain,
                 443,
                 'true',
                 token=self.access_token,
            )
            kwargs={}
            kwargs['granularity']='M'+str(self.tf)
            kwargs['price']='MBA'
            response=ctx_candles.instrument.candles(self.instruments,**kwargs)
            if str(response.status) == "200":
                data=[]
                for candle in response.get('candles',200):
                    data.append([candle.time,candle.mid.o,candle.mid.h,candle.mid.l,candle.mid.c])
                df=pd.DataFrame(data,columns=['DateTime','Open','High','Low','Close'])  
                # df.index=pd.DatetimeIndex(df.index)
                df.DateTime = pd.to_datetime(df.DateTime)
                # df.index = df.DateTime
                df.to_csv('/Users/apple/Documents/code/PythonX86/OandaAPI/Output/historical_df.csv', mode='w', index=0)
                print(self.instruments,'saved historicalCandles')
                 # Show the chart
                # df.index = df.DateTime
                # df['Close'].plot()
                # df.reset_index(inplace=True)
                # Show the chart
                # mc = mpf.make_marketcolors(up='limegreen',down='red',inherit=True) # Create my own `marketcolors` to use with the `nightclouds` style:
                # s  = mpf.make_mpf_style(base_mpf_style='nightclouds',marketcolors=mc,gridstyle='') # Create a new style based on `nightclouds` but with my own `marketcolors`:
                # mpf.plot(df,type='candle',style=s,show_nontrading = False,block = True, tight_layout=True,returnfig = True,title='AUDUSD 5min')
                # mpf.show()
                return df
        except Exception as e:
            print("Caught exception when connecting to candles\n" + str(e))
        return
    
    
    