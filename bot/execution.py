# import httplib
import http.client
# import urllib
import v20
from v20.request import Request
from datetime import datetime
import pandas as pd
import mplfinance as mpf
import configparser
import requests
from datetime import datetime

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
        self.ctx=v20.Context(
                 self.domain,
                 self.port,
                 self.ssl,
                 application=self.application,
                 token=self.access_token,
                #  datetime_format=self.date_format
        )
        
        return

    def obtain_connection(self):
        # return httplib.HTTPSConnection(self.domain)
        return  http.client.HTTPSConnection(self.domain)
    
    def get_instruments(self):
        response = self.ctx.account.instruments(self.account_id)
        instruments = response.get("instruments", "200")
        print(instruments)
        '''
        .name
        .type
        
        .pipLocation:"{:.4f}".format(float(10 ** instrument.pipLocation))
        .marginRate: "{:.0f}:1 ({})".format(1.0 / float(instrument.marginRate),instrument.marginRate)
        
        '''
        return
    
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

    def execute_order(self, event):
        
        # If open position doesn't exist
        response_OpenPositions=self.ctx.trade.list_open(self.account_id)
        if response_OpenPositions.body['trades']==[]:
            response_MarketOrder=self.ctx.order.market(
                 self.account_id,
                 instrument=event.instrument,
                 units=event.units,
                 type=event.order_type,
                 stopLossOnFill=v20.transaction.StopLossDetails(price=event.SL)
            )
            if response_MarketOrder.status==201 and response_MarketOrder.reason=='Created':
                print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Market Order #'+str(response_MarketOrder.body['orderFillTransaction'].id),event.side,str(abs(response_MarketOrder.body['orderFillTransaction'].units)),'@',str(response_MarketOrder.body['orderFillTransaction'].price))
                text='Market Order #'+str(response_MarketOrder.body['orderFillTransaction'].id)+' '+event.side+' '+response_MarketOrder.body['orderFillTransaction'].instrument+' '+str(response_MarketOrder.body['orderFillTransaction'].units)+'@'+str(response_MarketOrder.body['orderFillTransaction'].price)
                self.send_Telegram(text)
        else:
            for position in response_OpenPositions.body['trades']:
                # If open position exists
                if position.instrument==event.instrument and event.units>0 and position.currentUnits>0:
                    response_ClosePosition = self.ctx.position.close(
                        self.account_id,
                        self.instruments,
                        longUnits="ALL"
                    )
                    if response_ClosePosition.status==200:
                        print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Position Closed #'+str(response_ClosePosition.body['longOrderFillTransaction'].id),response_ClosePosition.body['longOrderFillTransaction'].instrument,str(response_ClosePosition.body['longOrderFillTransaction'].units),'@',str(response_ClosePosition.body['longOrderFillTransaction'].price),'with PNL:',str(response_ClosePosition.body['longOrderFillTransaction'].pl),'accountBalance:',str(response_ClosePosition.body['longOrderFillTransaction'].accountBalance))
                        text='Position Closed #'+str(response_ClosePosition.body['longOrderFillTransaction'].id)+' '+response_ClosePosition.body['longOrderFillTransaction'].instrument+' '+str(response_ClosePosition.body['longOrderFillTransaction'].units)+'@'+str(response_ClosePosition.body['longOrderFillTransaction'].price)+' with PNL:'+str(response_ClosePosition.body['longOrderFillTransaction'].pl)+' '+'accountBalance:'+str(response_ClosePosition.body['longOrderFillTransaction'].accountBalance)
                        # text='Market Order #'+str(response.body['orderFillTransaction'].id)+' '+event.side+' '+event.instrument+' '+str(event.units)+'@'+str(response.body['orderFillTransaction'].price)
                        self.send_Telegram(text)
                elif position.instrument==event.instrument and event.units<0 and position.currentUnits<0:
                    response_ClosePosition = self.ctx.position.close(
                        self.account_id,
                        self.instruments,
                        shortUnits="ALL"
                    )        
                    if response_ClosePosition.status==200:   
                        print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Position Closed #'+str(response_ClosePosition.body['shortOrderFillTransaction'].id),response_ClosePosition.body['shortOrderFillTransaction'].instrument,str(response_ClosePosition.body['shortOrderFillTransaction'].units),'@',str(response_ClosePosition.body['shortOrderFillTransaction'].price),'with PNL:',str(response_ClosePosition.body['shortOrderFillTransaction'].pl),'accountBalance:',str(response_ClosePosition.body['shortOrderFillTransaction'].accountBalance))
                        text='Position Closed #'+str(response_ClosePosition.body['shortOrderFillTransaction'].id)+' '+response_ClosePosition.body['shortOrderFillTransaction'].instrument+' '+str(response_ClosePosition.body['shortOrderFillTransaction'].units)+'@'+str(response_ClosePosition.body['shortOrderFillTransaction'].price)+' with PNL:'+str(response_ClosePosition.body['shortOrderFillTransaction'].pl)+' '+'accountBalance:'+str(response_ClosePosition.body['shortOrderFillTransaction'].accountBalance)
                        # text='Market Order #'+str(response.body['orderFillTransaction'].id)+' '+event.side+' '+event.instrument+' '+str(event.units)+'@'+str(response.body['orderFillTransaction'].price)
                        self.send_Telegram(text)
        
        '''
        curl: Close 99 units of EUR_USD Position in Account
        {
        "longUnits": "99"
        }
        EOF
        )
        
        curl \
        -X PUT \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer <AUTHENTICATION TOKEN>" \
        -d "$body" \
        "https://api-fxtrade.oanda.com/v3/accounts/<ACCOUNT>/positions/EUR_USD/close"
        
        header={"Authorization": "Bearer "+self.access_token}
        CLOSE_POSITION_PATH=f"/v3/accounts/{self.account_id}/positions/{self.instruments}/close"
        response=requests.put("https:/"+self.domain+CLOSE_POSITION_PATH,headers=header,params=)
        
        
        request = Request(
            'POST',
            '/v3/accounts/{accountID}/orders'
        )
        '''
        
        return
    
    def send_Telegram(self,text):
        config = configparser.ConfigParser()
        config.read('/Users/apple/Documents/code/PythonX86/OandaAPI/Settings/TelegramConfig.cfg')
        token = config.get('Section_A', 'token')
        chatid = config.get('Section_A', 'chatid')
        text='Oanda: '+text
        params = {'chat_id': chatid, 'text': text, 'parse_mode': 'HTML'}
        resp = requests.post(
         'https://api.telegram.org/bot{}/sendMessage'.format(token), params)
        resp.raise_for_status()
        return
    