# Input trade setup
# instrument = "TWIX_USD"
# instrument = "US30_USD"
# instrument = "NL25_EUR"
# instrument = "UK10YB_GBP"
# instrument = "JP225_USD"
# instrument = "XCU_USD"
# instrument = "EUR_USD"
# instrument = "XAG_USD"
instrument = "GBP_USD"

direction='BUY'


'''

check openposition error
close market handle
bid ask mid
multi-instruments

check balance and margin
account info:ID,base currency,total amount,balance remain to trade,leverage;optional:Realized and Unrealized PNL,margin used,open trades,open orders.
report after SL/TP

requirement:

SL/TP/Close position
toggle tradeable or not with timestamp.
type: HEARTBEAT

'''





import queue
import threading
from datetime import datetime
import time
from execution import Execution
from settings import STREAM_DOMAIN, API_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID,TF
from strategy import TestRandomStrategy
from streaming import StreamingForexPrices
from candles import historicalCandles
from instruments import InstrumentsInfo
import pandas as pd




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
    
    # Get Instruments List
    instru=InstrumentsInfo(API_DOMAIN,ACCESS_TOKEN,ACCOUNT_ID)
    instrumentsDict=instru.get_instruments()
    df_instruments=pd.DataFrame(columns=['name','type','displayName','pipLocation','minimumTradeSize','marginRate'])
    for i in sorted(instrumentsDict.keys()):
        df_instruments.loc[i]=i,instrumentsDict[i]['type'],instrumentsDict[i]['displayName'],instrumentsDict[i]['pipLocation'],instrumentsDict[i]['minimumTradeSize'],instrumentsDict[i]['marginRate']
    # df_instruments.to_csv('/Users/apple/Documents/code/PythonX86/OandaAPI/Output/df_instruments.csv', mode='w', index=1)
    
    if df_instruments.loc[instrument,'type']=='CFD' or df_instruments.loc[instrument,'type']=='METAL':
        units = df_instruments.loc[instrument,'minimumTradeSize']
    elif df_instruments.loc[instrument,'type']=='CURRENCY':
        units=1000*df_instruments.loc[instrument,'minimumTradeSize']
    
    # Creat the OANDA historical data class
    candles=historicalCandles(
         API_DOMAIN, ACCESS_TOKEN,instrument,TF
    )
    df=candles.connect_to_candles()
    
    # Create the OANDA market price streaming class
    # making sure to provide authentication commands
    prices = StreamingForexPrices(
        STREAM_DOMAIN, ACCESS_TOKEN,ACCOUNT_ID,
        instrument, events
    )
      
    # execution = Execution(API_DOMAIN, PORT,SSL,APPLICATION, ACCESS_TOKEN,DATE_FORMAT, ACCOUNT_ID,TF,instrument)
    execution = Execution(API_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID,instrument,df_instruments)
    
    # Create the strategy/signal generator, passing the
    # instrument, quantity of units and the events queue
    # strategy = TestRandomStrategy(instrument, units, events)
    strategy = TestRandomStrategy(instrument, units,events,df,df_instruments,direction,TF)

    # Create two separate threads: One for the trading loop
    # and another for the market price streaming class
    trade_thread = threading.Thread(target=trade, name='Trade',args=(events, strategy, execution))
    price_thread = threading.Thread(target=prices.stream_to_queue,name='Stream', args=[])

    # Start both threads
    trade_thread.start()
    price_thread.start()
    
