'''

check balance and margin
close market handle

requirement:
SL/TP/Close position

toggle tradeable or not with timestamp.
multi-instruments
bid ask mid
breakdown prelow and than breakup prehigh and exit at breakdown prelow
pre 3 day high getting lower and lower and than breakup the pre day high.

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
from instruments import Instruments

# Input trade setup
instrument = "USD_HUF"
units = 5000

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
    symbols=Instruments(API_DOMAIN,ACCESS_TOKEN,ACCOUNT_ID)
    symbolInfo=symbols.get_instruments()
    
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
    execution = Execution(API_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID,instrument)
    
    # Create the strategy/signal generator, passing the
    # instrument, quantity of units and the events queue
    # strategy = TestRandomStrategy(instrument, units, events)
    strategy = TestRandomStrategy(instrument, units,events,df,TF)

    # Create two separate threads: One for the trading loop
    # and another for the market price streaming class
    trade_thread = threading.Thread(target=trade, args=(events, strategy, execution))
    price_thread = threading.Thread(target=prices.stream_to_queue, args=[])

    # Start both threads
    trade_thread.start()
    price_thread.start()
    
