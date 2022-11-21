'''

check balance and margin

requirement:
SL/TP/Close position
import instruments
toggle tradeable or not with timestamp.
multi-instruments
bid ask mid
breakdown prelow and than breakup prehigh and exit at breakdown prelow
pre 3 day high getting lower and lower and than breakup the pre day high.

'''

import queue
# from queue import Queue
import threading
import time

from execution import Execution
# from settings import STREAM_DOMAIN, API_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID,PORT,SSL,APPLICATION,DATE_FORMAT,TF
from settings import STREAM_DOMAIN, API_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID,PORT,SSL,APPLICATION,TF
from strategy import TestRandomStrategy
from streaming import StreamingForexPrices
# from candles import CandlesForexPrices

# Input trade setup
instrument = "JP225_USD"
units = 0.5

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
            # except events.empty():
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

    
    
    # # Creat the OANDA historical data class
    # historicalCandles=CandlesForexPrices(
    #      API_DOMAIN, PORT,SSL,APPLICATION,ACCESS_TOKEN, DATE_FORMAT,TF,ACCOUNT_ID,
    #      instrument, events
    # )
    
    
    # Create the OANDA market price streaming class
    # making sure to provide authentication commands
    prices = StreamingForexPrices(
        STREAM_DOMAIN, PORT,SSL,APPLICATION,ACCESS_TOKEN,ACCOUNT_ID,
        instrument, events
    )
      
    # execution = Execution(API_DOMAIN, PORT,SSL,APPLICATION, ACCESS_TOKEN,DATE_FORMAT, ACCOUNT_ID,TF,instrument)
    execution = Execution(API_DOMAIN, PORT,SSL,APPLICATION, ACCESS_TOKEN, ACCOUNT_ID,TF,instrument)
    df=execution.connect_to_candles()
    
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
    
