from event import TickEvent
import v20
import numpy as np

class StreamingForexPrices(object):
    def __init__(
        # self, domain,port,ssl, application,access_token,date_format,
        self, domain,port,ssl, application,access_token,
        account_id, instruments, events_queue
    ):
        self.domain = domain
        self.port=port
        self.ssl=ssl
        self.application=application
        self.access_token = access_token
        # self.date_format=date_format
        self.account_id = account_id
        self.instruments = instruments
        self.events_queue = events_queue
        
    def connect_to_stream(self):
        try:
            ctx_stream = v20.Context(
                 self.domain,
                 self.port,
                 self.ssl,
                 application=self.application,
                 token=self.access_token,
                #  datetime_format=self.date_format
            )
        
            resp = ctx_stream.pricing.stream(
                 self.account_id,
                 snapshot=True,
                 instruments=self.instruments
            )
            
            return resp
        except Exception as e:
            print("Caught exception when connecting to stream\n" + str(e))
        
        return

    def stream_to_queue(self):
        response = self.connect_to_stream()
        moreThanOnce=False
        for msg_type, msg in response.parts():
            if msg_type == 'pricing.ClientPrice' and msg.closeoutAsk is not None:    
                # print(msg)
                instrument = msg.instrument
                time = msg.time
                bid = msg.closeoutBid # or bids.price?
                ask = msg.closeoutAsk
                tev = TickEvent(instrument, time, bid, ask)
                self.events_queue.put(tev)
                if msg.status!='tradeable' and msg.type=='PRICE' and not moreThanOnce:
                    print(msg)
                    print(instrument,'is not tradeable')
                    moreThanOnce=True
            
        return
                
                
            
                
