import math
import pandas as pd

from io import StringIO


data_url = "https://www.dropbox.com/s/pwm8wlncayp1clh/trump_beta.csv?dl=1"


class MultidimensionalCalibratedAtmosphericScrubbers(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 6, 1)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        
        symbols = self.get_symbols()
        self.AddUniverseSelection( ManualUniverseSelectionModel(symbols) )
        
        self.AddAlpha( TrumpBetaAlphaModel() )
        
        self.SetPortfolioConstruction( EqualWeightingPortfolioConstructionModel() )
        
        self.SetExecution( ImmediateExecutionModel() )

    def get_symbols(self):
        constituents = pd.read_csv(StringIO(self.Download(data_url)), index_col='Date').columns
        return [Symbol.Create(c, SecurityType.Equity, Market.USA) for c in constituents]


class TrumpBetaAlphaModel:
    
    def __init__(self):
        self.thresh = 1/4

    def Update(self, algorithm, slice):
         insights = []
         
         trump_beta = pd.Series({k: v.Value for k, v in slice.Get[TrumpBeta]().items()})
         
         low_trump_beta = abs(trump_beta).sort_values()[-math.floor(self.thresh*len(trump_beta)):]
         
         for security in low_trump_beta.keys():
             if algorithm.Securities.ContainsKey(security):
                 insight = Insight.Price(security, timedelta(days = 7), InsightDirection.Up)
                 insights.append(insight)
         
         return insights

    def OnSecuritiesChanged(self, algorithm, changes):
        for added in changes.AddedSecurities:
            algorithm.AddData(TrumpBeta, added.Symbol)
        
        for removed in changes.RemovedSecurities:
            algorithm.RemoveSecurity(removed.Symbol)



class TrumpBeta(PythonData):

    def GetSource(self, config, date, isLive):
        return SubscriptionDataSource(data_url, SubscriptionTransportMedium.RemoteFile);


    def Reader(self, config, line, date, isLive):
        data = line.split(',')
        
        if not (line.strip() and line[0].isdigit()):
            self.columns = {data[i]: i for i in range(len(data))}
            return None
        
        ticker = config.Symbol.Value
        
        trump_beta = TrumpBeta()
        trump_beta.Symbol = Symbol.Create(ticker, SecurityType.Equity, Market.USA)
        trump_beta.EndTime = pd.to_datetime(data[self.columns['Date']]) + timedelta(days=1) # Make sure we only get this data AFTER trading day - don't want forward bias.
        
        value = data[self.columns[ticker]]
        
        if not value: return None
        
        trump_beta.Value = float(value)

        return trump_beta
