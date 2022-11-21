
import v20


class Instruments():
    def __init__(self,domain,token,account_id):
        self.domain=domain
        self.token=token
        self.account_id=account_id

    def get_instruments(self):
        ctx=v20.Context(
             self.domain,
             token=self.token
        )
        response = ctx.account.instruments(self.account_id)
        instruments = response.get("instruments", "200")
        
        instrument={}
        for instu in instruments:
            instrument[instu.name]={
                 'type':instu.type,
                 'displayName':instu.displayName,
                 'pipLocation':instu.pipLocation,
                 'minimumTradeSize':instu.minimumTradeSize,
                 'marginRate': instu.marginRate
                 }
        return instrument
            
        
        '''
        .name
        .type
        .pipLocation:"{:.4f}".format(float(10 ** instrument.pipLocation))
        .marginRate: "{:.0f}:1 ({})".format(1.0 / float(instrument.marginRate),instrument.marginRate)
        
        '''
        return