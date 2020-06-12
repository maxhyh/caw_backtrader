import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt

import backtrader as bt

logdir = '/Users/yihuihuang/Desktop/Crypto/caw_backtrader/log/' # log path
datadir = '/Users/yihuihuang/Desktop/Crypto/caw_backtrader/data' # data path
reportdir = '/Users/yihuihuang/Desktop/Crypto/caw_backtrader/report' # report path
datafile = 'BTC_USDT_1h.csv' # data file
from_datetime = '2020-01-01 00:00:00' # start time 
to_datetime = '2020-04-01 00:00:00' # end time

class SMACross(bt.SignalStrategy):
    
    params = (
        ('pfast', 10),
        ('pslow', 20),
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma1 = bt.ind.SMA(period=self.p.pfast)
        self.sma2 = bt.ind.SMA(period=self.p.pslow)
        self.crossover = bt.ind.CrossOver(self.sma1, self.sma2)
        self.signal_add(bt.SIGNAL_LONG, self.crossover)

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.datas[0].close[0])

        # Check in the market
        if not self.position: 
            if self.crossover > 0: 
                self.log('Buy, %.2f' % self.datas[0].close[0])
                self.order = self.buy()
        
        elif self.crossover < 0:
            self.log('Close, %.2f' % self.datas[0].close[0])
            self.order = self.close()

    def stop(self):
        self.log('(MA_fast %2d, MA_slow %2d) Ending Value %.2f' %
                 (self.p.pfast, self.p.pslow, self.broker.getvalue()), doprint=True)

if __name__ == '__main__':

    cerebro = bt.Cerebro()

    cerebro.addstrategy(SMACross)

    data = pd.read_csv(
        os.path.join(datadir, datafile), index_col='datetime', parse_dates=True)
    data = data.loc[
        (data.index >= pd.to_datetime(from_datetime)) &
        (data.index <= pd.to_datetime(to_datetime))]

    datafeed = bt.feeds.PandasData(dataname=data)

    cerebro.adddata(datafeed)

    cerebro.broker.setcash(10000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.PercentSizer, percents=99)

    # Set the commission
    cerebro.broker.setcommission(commission=0.001)

    # Add loger
    params_lst = [str(v)
                  for k, v in cerebro.strats[0][0][0].params.__dict__.items()
                  if not k.startswith('_')]
    resfile = '_'.join([
        os.path.splitext(datafile)[0],
        cerebro.strats[0][0][0].__name__,
        '_'.join(params_lst), from_datetime.split(" ")[0], to_datetime.split(" ")[0]])
    logfile = resfile + '.csv'
    
    cerebro.addwriter(
        bt.WriterFile, 
        out=os.path.join(logdir,logfile),
        csv=True)


    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    plt.rcParams['figure.figsize'] = [13.8, 10]
    fig = cerebro.plot(style='candlestick', barup='green', bardown='red')
    figfile = resfile + '.png'
    fig[0][0].savefig(
	    os.path.join(reportdir, figfile),
	    dpi=480)