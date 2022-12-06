from settings import STREAM_DOMAIN, API_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID
from tradeSetup import INSTRUMENT,DIRECTION,ORDERCOUNT,TIMEFRAME1,TIMEFRAME2,TIMEFRAME3,RISKAMOUT,IFSIGNALEXIT
import pandas as pd
import queue
import threading
import time
from execution import Execution
from strategy import TestRandomStrategy
from streaming import StreamingForexPrices
from candles import historicalCandles
from instruments import InstrumentsInfo
from oandaRESTAPI import OandaAPI

class TradeSetup:
    def __init__(self):
        self.instrument=INSTRUMENT[:len(INSTRUMENT)-3].upper()+'_'+INSTRUMENT[-3:].upper()
        self.direction=DIRECTION.upper()
        self.ordercount=ORDERCOUNT
        self.timeFrame1=TIMEFRAME1
        self.timeFrame2=TIMEFRAME2
        self.timeFrame3=TIMEFRAME3
        self.riskAmout=RISKAMOUT
        self.ifSignalExit=IFSIGNALEXIT
        # 記錄原值做比較是否改變，有則提醒
        return

def trade(events, strategy, execution):
    """
    Carries out an infinite while loop that polls the
    events queue and directs each event to either the
    strategy component of the execution handler. The
    loop will then pause for "heartbeat" seconds and
    continue.
    """
    while True:
        try:
            event = events.get(False)
        except queue.Empty:
            # print(datetime.fromtimestamp(int(datetime.now().timestamp())),'Queue Empty')
            pass
        else:
            if event is not None:
                if event.type == 'TICK':
                    strategy.calculate_signals(event)
                elif event.type == 'ORDER':
                    execution.execute_order(event)
        time.sleep(heartbeat)

if __name__ == "__main__":
    heartbeat = 0.5  # Half a second between polling
    events = queue.Queue()
    
    # import TradeSetup
    ts=TradeSetup()
    
    # Get Account Details
    api=OandaAPI()
    response_account=api.get_account()
    accountDetails=response_account[1]
    
    # Get Instruments List
    instru=InstrumentsInfo(API_DOMAIN,ACCESS_TOKEN,ACCOUNT_ID)
    instrumentsDict=instru.get_instruments()
    df_instruments=pd.DataFrame(columns=['name','type','displayName','pipLocation','minimumTradeSize','marginRate'])
    for i in sorted(instrumentsDict.keys()):
        df_instruments.loc[i]=i,instrumentsDict[i]['type'],instrumentsDict[i]['displayName'],instrumentsDict[i]['pipLocation'],instrumentsDict[i]['minimumTradeSize'],instrumentsDict[i]['marginRate']
    # df_instruments.to_csv('/Users/apple/Documents/code/PythonX86/OandaAPI/Output/df_instruments.csv', mode='w', index=1)
    
    # if df_instruments.loc[ts.instrument,'type']=='CFD' or df_instruments.loc[ts.instrument,'type']=='METAL':
    #     units = df_instruments.loc[ts.instrument,'minimumTradeSize']
    # elif df_instruments.loc[ts.instrument,'type']=='CURRENCY':
    #     units=1000*df_instruments.loc[ts.instrument,'minimumTradeSize']
    
    # Creat the OANDA historical data class
    candles=historicalCandles(
         API_DOMAIN, ACCESS_TOKEN,ts.instrument,ts.timeFrame1
    )
    df=candles.connect_to_candles()
    
    # Create the OANDA market price streaming class
    # making sure to provide authentication commands
    prices = StreamingForexPrices(
        STREAM_DOMAIN, ACCESS_TOKEN,ACCOUNT_ID,
        ts.instrument, events
    )
      
    execution = Execution(API_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID,ts.instrument,df_instruments)
    
    # Create the strategy/signal generator, passing the
    # instrument, quantity of units and the events queue
    # strategy = TestRandomStrategy(instrument, units, events)
    strategy = TestRandomStrategy(accountDetails,ts.instrument,events,df,df_instruments,ts.direction,ts.timeFrame1)

    # Create two separate threads: One for the trading loop
    # and another for the market price streaming class
    trade_thread = threading.Thread(target=trade, name='Trade',args=(events, strategy, execution))
    price_thread = threading.Thread(target=prices.stream_to_queue,name='Stream', args=[])

    # Start both threads
    trade_thread.start()
    price_thread.start()
    
