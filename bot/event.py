# class Event(object):
#     pass

# class TickEvent(Event):
class TickEvent:
    def __init__(self, instrument, time, bid, ask):
        self.type = 'TICK'
        self.instrument = instrument
        self.time = time
        self.bid = bid
        self.ask = ask

# class OrderEvent(Event):
class OrderEvent:
    def __init__(self, instrument, units, order_type, side,sl,tp):
        self.type = 'ORDER'
        self.instrument = instrument
        self.units = units
        self.order_type = order_type
        self.side = side
        self.SL=sl
        self.TP=tp
        