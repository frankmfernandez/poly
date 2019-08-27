from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import numpy as np
import backtrader as bt
from datetime import datetime
import time

 
# IMPORTANT!
# ----------
# Register for an API at:
# https://www.alphavantage.co/support/#api-key
# Then insert it here.
Apikey = 'U82PCE20QT55OXLL'
 
def alpha_vantage_eod(symbol_list, compact=False, debug=False, *args, **kwargs):
    '''
    Helper function to download Alpha Vantage Data.
 
    This will return a nested list with each entry containing:
        [0] pandas dataframe
        [1] the name of the feed.
    '''
    data_list = list()
 
    size = 'compact' if compact else 'full'
 
    count = 0
    total = len(symbol_list)
 
    for symbol in symbol_list:
        count += 1
 
        print('\nDownloading: {}'.format(symbol))
        print('Symbol: {} of {}'.format(count, total, symbol))
        print('-'*80)
 
        # Submit our API and create a session
        alpha_ts = TimeSeries(key=Apikey, output_format='pandas')
 
        data, meta_data = alpha_ts.get_daily(symbol=symbol, outputsize=size)
 
        #Convert the index to datetime.
        data.index = pd.to_datetime(data.index)
        data.columns = ['Open', 'High', 'Low', 'Close','Volume']
 
        if debug:
            print(data)
 
        data_list.append((data, symbol))
 
        # Sleep to avoid hitting API limit
        print('Sleeping |', end='', flush=True)
        for x in range(12):
            print('=', end='', flush=True)
            time.sleep(1)
        print('| Done!')
 
    return data_list
 
class TestStrategy(bt.Strategy):
 
    def __init__(self):
 
        self.inds = dict()
        self.inds['RSI'] = dict()
        self.inds['SMA'] = dict()
 
        for i, d in enumerate(self.datas):
 
            # For each indicator we want to track it's value and whether it is
            # bullish or bearish. We can do this by creating a new line that returns
            # true or false.
 
            # RSI
            self.inds['RSI'][d._name] = dict()
            self.inds['RSI'][d._name]['value']  = bt.indicators.RSI(d, period=14)
            self.inds['RSI'][d._name]['bullish'] = self.inds['RSI'][d._name]['value']  > 50
            self.inds['RSI'][d._name]['bearish'] = self.inds['RSI'][d._name]['value']  < 50
 
            # SMA
            self.inds['SMA'][d._name] = dict()
            self.inds['SMA'][d._name]['value']  = bt.indicators.SMA(d, period=20)
            self.inds['SMA'][d._name]['bullish'] = d.close > self.inds['SMA'][d._name]['value']
            self.inds['SMA'][d._name]['bearish'] = d.close < self.inds['SMA'][d._name]['value']
 
    def stop(self):
        '''
        Called when backtrader is finished the backtest. Here we will just get
        the final values at the end of testing for each indicator.
        '''
 
        # Assuming all symbols are going to have the same data on the same days.
        # If that is not the case and you are mixing assets from different classes,
        # regions or exchanges, then you might want to conisder adding an extra
        # column to the final results.
        print('{}: Results'.format(self.datas[0].datetime.date()))
        print('-'*80)
 
 
        results = dict()
        for key, value in self.inds.items():
            results[key] = list()
 
            for nested_key, nested_value in value.items():
 
                if nested_value['bullish'] == True or nested_value['bearish'] == True:
                    results[key].append([nested_key, nested_value['bullish'][0],
                            nested_value['bearish'][0], nested_value['value'][0]])
 
 
        # Create and print the header
        headers = ['Indicator','Symbol','Bullish','Bearish','Value']
        print('|{:^10s}|{:^10s}|{:^10s}|{:^10s}|{:^10s}|'.format(*headers))
        print('|'+'-'*10+'|'+'-'*10+'|'+'-'*10+'|'+'-'*10+'|'+'-'*10+'|')
 
        # Sort and print the rows
        for key, value in results.items():
            #print(value)
            value.sort(key= lambda x: x[0])# Sort by Ticker
 
            for result in value:
                print('|{:^10s}|{:^10s}|{:^10}|{:^10}|{:^10.2f}|'.format(key, *result))
 
 
# Create an instance of cerebro
cerebro = bt.Cerebro()
 
# Add our strategy
cerebro.addstrategy(TestStrategy)
 
# Download our data from Alpha Vantage.
symbol_list =['MSFT']
data_list = alpha_vantage_eod(
                symbol_list,
                compact=True,
                debug=False)
 
for i in range(len(data_list)):
 
    data = bt.feeds.PandasData(
                dataname=data_list[i][0], # This is the Pandas DataFrame
                name=data_list[i][1], # This is the symbol
                timeframe=bt.TimeFrame.Days,
                compression=1
                )
 
    #Add the data to Cerebro
    cerebro.adddata(data)
 
print('\nStarting Analysis')
print('-'*80)
# Run the strategy
cerebro.run()