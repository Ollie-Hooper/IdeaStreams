import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression

class MultidimensionalOptimizedChamber(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2019, 1, 1)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        
        self.gold = self.AddCfd("XAUUSD", Resolution.Minute, Market.Oanda).Symbol
        self.yld = self.AddData(TenYrYield, "yld", Resolution.Daily).Symbol
        
        self.model = LinearRegression()
        
        self.fit_model()
        
        self.Schedule.On(self.DateRules.MonthStart("XAUUSD"), \
                 self.TimeRules.At(0, 0), \
                 self.fit_model)


    def fit_model(self):
        history = self.History([self.gold, self.yld], timedelta(365*1))
        
        gold_prices = history.loc[self.gold].unstack(level=1)["close"].apply(np.log)
        bond_yield = history.loc[self.yld].unstack(level=1)["value"]
        
        data = pd.DataFrame()

        data['gold'] = gold_prices
        data['yield'] = bond_yield

        data.dropna(inplace=True)
        
        y = data['gold'].values.reshape((-1, 1))
        x = data['yield'].values.reshape((-1, 1))
        
        self.model.fit(x, y)
        
    
    def OnData(self, data):
        
        if self.yld in data.Keys and self.gold in data.Keys:
            gold_price = data[self.gold].Value
            bond_yield = data[self.yld].Value
            
            predicted_price = np.exp(self.model.predict([[bond_yield]]))
            
            if predicted_price > gold_price:
                self.SetHoldings(self.gold, 1)
            else:
                self.SetHoldings(self.gold, 0)



class TenYrYield(PythonData):

    def GetSource(self, config, date, isLive):
        source = "https://www.dropbox.com/s/5rnszsadogc8byk/DFII10.csv?dl=1"
        return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile);

    def Reader(self, config, line, date, isLive):
        if not (line.strip() and line[0].isdigit()): return None

        data = line.split(',')
        yld = TenYrYield()
        yld.Symbol = config.Symbol
        yld.Time = datetime.strptime(data[0], '%Y-%m-%d')
        yld.Value = data[1]

        return yld
