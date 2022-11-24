# import httplib
import http.client
# import urllib
import v20
from datetime import datetime
import mplfinance as mpf
import configparser
import requests
from datetime import datetime
import time

class Execution(object):
    def __init__(self, domain, access_token, account_id,instruments,df_instrument):
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.instruments=instruments
        self.df_instrument=df_instrument
        self.conn = self.obtain_connection()
        self.ctx=v20.Context(
                 self.domain,
                 443,
                 'true',
                 token=self.access_token,
        )
        return

    def obtain_connection(self):
        # return httplib.HTTPSConnection(self.domain)
        return  http.client.HTTPSConnection(self.domain)

    def execute_order(self, event):
        # Check open position
        try:
            response_OpenPositions=self.ctx.trade.list_open(self.account_id)
            if len(response_OpenPositions.body['trades'])!=0:
                for opentrade in response_OpenPositions['trades']:
                    print(datetime.fromtimestamp(int(datetime.now().timestamp())),'checked openposition #',response_OpenPositions.body['lastTransactionID'].id,response_OpenPositions.body['lastTransactionID'].instrument,response_OpenPositions.body['lastTransactionID'].state,'Price:',response_OpenPositions.body['lastTransactionID'].price,'Units:',response_OpenPositions.body['lastTransactionID'].currentUnits,'Unrealized PNL:',response_OpenPositions.body['lastTransactionID'].unrealizedPL)
            # If open position doesn't exist
            if len(response_OpenPositions.body['trades'])==0:
                # print(datetime.fromtimestamp(int(datetime.now().timestamp())),'no open position')
                try:
                    response_MarketOrder=self.ctx.order.market(
                        self.account_id,
                        instrument=event.instrument,
                        units=event.units,
                        type=event.order_type,
                        stopLossOnFill=v20.transaction.StopLossDetails(price=event.SL),
                        takeProfitOnFill=v20.transaction.TakeProfitDetails(price=event.TP)
                    )
                except:
                    print(datetime.fromtimestamp(int(datetime.now().timestamp())),'error place market order')
                    print(response_MarketOrder.body)
                    print(response_MarketOrder.body.keys())
                    pass
                if response_MarketOrder.status==201 and response_MarketOrder.reason=='Created':
                    if 'orderFillTransaction' in response_MarketOrder.body.keys():
                        print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Market Order #'+str(response_MarketOrder.body['orderFillTransaction'].id),response_MarketOrder.body['orderFillTransaction'].instrument,event.side,str(abs(response_MarketOrder.body['orderFillTransaction'].units)),'@',str(response_MarketOrder.body['orderFillTransaction'].price))
                        text='Market Order #'+str(response_MarketOrder.body['orderFillTransaction'].id)+' '+event.side+' '+response_MarketOrder.body['orderFillTransaction'].instrument+' '+str(response_MarketOrder.body['orderFillTransaction'].units)+'@'+str(response_MarketOrder.body['orderFillTransaction'].price)
                        self.send_Telegram(text)
                    elif 'orderCancelTransaction' in response_MarketOrder.body.keys():
                        print("response_MarketOrder.body['orderCancelTransaction']\n",response_MarketOrder.body['orderCancelTransaction'])
                        print("response_MarketOrder.body['orderCreateTransaction']\n",response_MarketOrder.body['orderCreateTransaction'])
                        # print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Order Cancel #',response_MarketOrder.body['orderCancelTransaction'].id,'type:',response_MarketOrder.body['orderCancelTransaction'].type,'reason:',response_MarketOrder.body['orderCancelTransaction'].reason)
                    else:
                        text='KeyError:orderFillTransaction doesn'+"'"+'t exist!'
                        print(datetime.fromtimestamp(int(datetime.now().timestamp())),text)
                        print(response_MarketOrder.body.keys())
                elif response_MarketOrder.status==400:
                    print("response_MarketOrder.body['orderRejectTransaction']\n",response_MarketOrder.body['orderRejectTransaction'])
                    # text='Status: '+str(response_MarketOrder.status)+' Reason: '+response_MarketOrder.reason
                    # print(datetime.fromtimestamp(int(datetime.now().timestamp())),text)
                    return
            # If open position exist
            else:
                # print(datetime.fromtimestamp(int(datetime.now().timestamp())),'open position exist')
                for position in response_OpenPositions.body['trades']:
                    if event.side=='SELL' and position.instrument==event.instrument and event.units>0 and position.currentUnits>0:
                        try:
                            response_ClosePosition = self.ctx.position.close(
                                self.account_id,
                                self.instruments,
                                longUnits="ALL"
                            )
                        except:
                            print(datetime.fromtimestamp(int(datetime.now().timestamp())),'error close longposition')
                            pass
                        if response_ClosePosition.status==200:
                            print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Position Closed #'+str(response_ClosePosition.body['longOrderFillTransaction'].id),response_ClosePosition.body['longOrderFillTransaction'].instrument,str(response_ClosePosition.body['longOrderFillTransaction'].units),'@',str(response_ClosePosition.body['longOrderFillTransaction'].price),'with PNL:',str(response_ClosePosition.body['longOrderFillTransaction'].pl),'accountBalance:',str(response_ClosePosition.body['longOrderFillTransaction'].accountBalance))
                            text='Position Closed #'+str(response_ClosePosition.body['longOrderFillTransaction'].id)+' '+response_ClosePosition.body['longOrderFillTransaction'].instrument+' '+str(response_ClosePosition.body['longOrderFillTransaction'].units)+'@'+str(response_ClosePosition.body['longOrderFillTransaction'].price)+' with PNL:'+str(response_ClosePosition.body['longOrderFillTransaction'].pl)+' '+'accountBalance:'+str(response_ClosePosition.body['longOrderFillTransaction'].accountBalance)
                            self.send_Telegram(text)
                    elif event.side=='BUY' and position.instrument==event.instrument and event.units<0 and position.currentUnits<0:
                        try:
                            response_ClosePosition = self.ctx.position.close(
                                self.account_id,
                                self.instruments,
                                shortUnits="ALL"
                            )       
                        except:
                            print(datetime.fromtimestamp(int(datetime.now().timestamp())),'error close longposition')
                            pass
                        if response_ClosePosition.status==200:   
                            print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Position Closed #'+str(response_ClosePosition.body['shortOrderFillTransaction'].id),response_ClosePosition.body['shortOrderFillTransaction'].instrument,str(response_ClosePosition.body['shortOrderFillTransaction'].units),'@',str(response_ClosePosition.body['shortOrderFillTransaction'].price),'with PNL:',str(response_ClosePosition.body['shortOrderFillTransaction'].pl),'accountBalance:',str(response_ClosePosition.body['shortOrderFillTransaction'].accountBalance))
                            text='Position Closed #'+str(response_ClosePosition.body['shortOrderFillTransaction'].id)+' '+response_ClosePosition.body['shortOrderFillTransaction'].instrument+' '+str(response_ClosePosition.body['shortOrderFillTransaction'].units)+'@'+str(response_ClosePosition.body['shortOrderFillTransaction'].price)+' with PNL:'+str(response_ClosePosition.body['shortOrderFillTransaction'].pl)+' '+'accountBalance:'+str(response_ClosePosition.body['shortOrderFillTransaction'].accountBalance)
                            self.send_Telegram(text)
        except:
            print(datetime.fromtimestamp(int(datetime.now().timestamp())),'error checked openposition')
            print("response_OpenPositions.body.keys()\n",response_OpenPositions.body.keys())
            print("response_OpenPositions.body['trades']\n",response_OpenPositions.body['trades'])
            pass
        return
        
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
    