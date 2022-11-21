from event import TickEvent
import v20

class StreamingForexPrices(object):
    def __init__(
        self, domain,access_token,
        account_id, instruments, events_queue
    ):
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.instruments = instruments
        self.events_queue = events_queue
        
    def connect_to_stream(self):
        try:
            ctx_stream = v20.Context(
                 self.domain,
                 443,
                 'true',
                 token=self.access_token,
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
        for msg_type, msg in response.parts():
            if msg_type == 'pricing.ClientPrice' and msg.status=='tradeable' and msg.closeoutAsk is not None:    
                # print(msg)
                instrument = msg.instrument
                time = msg.time
                bid = msg.closeoutBid # or bids.price?
                ask = msg.closeoutAsk
                tev = TickEvent(instrument, time, bid, ask)
                self.events_queue.put(tev)
                # print(msg)
              
            
        return
                
                
            
                
