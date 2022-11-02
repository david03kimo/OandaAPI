vscode


import sys
sys.path.append('/Users/apple/Documents/code/PythonX86/OandaAPI/Settings')
import v20
import pandas as pd
import configparser

config = configparser.ConfigParser()
config.read('/Users/apple/Documents/code/PythonX86/OandaAPI/Settings/config.cfg')

ctx=v20.Context(
    config['oanda']['hostname'],
    config['oanda']['port'],
    config['oanda']['ssl'],
    application=config['oanda']['application'],
    token=config['oanda']['access_token'],
    datetime_format=config['oanda']['date_format']
)

instrument='AUD_USD'
kwargs={}

kwargs['granularity']='M1'
kwargs['price']='MBA'

response=ctx.instrument.candles(instrument,**kwargs)


