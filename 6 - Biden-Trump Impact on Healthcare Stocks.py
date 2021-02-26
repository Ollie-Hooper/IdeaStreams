import json
import pandas as pd


class HorizontalOptimizedThrustAssembly(QCAlgorithm):

    def Initialize(self):
        self.odds_data = self.load_odds_data()
        
        self.SetStartDate(2020, 3, 13)  # Set Start Date
        self.SetEndDate(self.odds_data.index.max().year, self.odds_data.index.max().month, self.odds_data.index.max().day)
        self.SetCash(100000)  # Set Strategy Cash
        
        self.UniverseSettings.Resolution = Resolution.Daily
        
        self.AddUniverseSelection(
           FineFundamentalUniverseSelectionModel(self.SelectCoarse, self.SelectFine)
        )
        
        self.AddAlpha(BidenTrumpOddsAlpha(self))
        
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())
        
        self.SetExecution(ImmediateExecutionModel())
    
    def SelectCoarse(self, coarse):
        filter_price = [c for c in coarse if c.Price > 5]
        sorted_dollar_volume = sorted([c for c in filter_price if c.HasFundamentalData], key=lambda c: c.Volume, reverse=True)
        return [c.Symbol for c in sorted_dollar_volume][:100]

    def SelectFine(self, fine):
        self.healthcare = [f for f in fine if f.AssetClassification.MorningstarSectorCode == MorningstarSectorCode.Healthcare]
        self.high_eps = sorted([f for f in fine if f not in self.healthcare], key=lambda f: f.EarningReports.NormalizedBasicEPS.OneMonth, reverse=True)[:len(self.healthcare)]
        return [*[f.Symbol for f in self.healthcare], *[f.Symbol for f in self.high_eps]]


    def load_odds_data(self):
        request = self.Download('https://www.realclearpolitics.com/json/odds/event_1_final.json?1595265370902')

        biden = pd.DataFrame({date['date_r']: [float(c['value']) for c in date['candidates'] if c['id'] == '4'] for date in json.loads(request)['poll']['rcp_avg']}).T[0]
        trump = pd.DataFrame({date['date_r']: [float(c['value']) for c in date['candidates'] if c['id'] == '1'] for date in json.loads(request)['poll']['rcp_avg']}).T[0]

        df = pd.DataFrame()
        df['Biden'] = biden
        df['Trump'] = trump
        df['Diff'] = biden - trump
        
        df.index = pd.to_datetime(df.index, utc=True).shift(2, freq='d').map(lambda x: x.replace(hour=0, minute=0, second=0))
        
        return df


class BidenTrumpOddsAlpha:
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        
        self.lookback = 5
        self.thresh = 0.1

    def Update(self, algorithm, slice):
        insights = []
        
        today = self.algorithm.odds_data.loc[algorithm.Time, 'Diff']
        previous = self.algorithm.odds_data.loc[algorithm.Time - timedelta(self.lookback), 'Diff']
        pct_change = (today - previous) / previous
        
        if abs(pct_change) > self.thresh:
            healthcare_direction = InsightDirection.Up if pct_change > 0 else InsightDirection.Down
            high_eps_direction = InsightDirection.Down if pct_change > 0 else InsightDirection.Up
            
            for security in self.algorithm.healthcare:
                insights.append(Insight.Price(security.Symbol, timedelta(self.lookback), healthcare_direction))
            
            for security in self.algorithm.high_eps:
                insights.append(Insight.Price(security.Symbol, timedelta(self.lookback), high_eps_direction))
        
        return insights

    def OnSecuritiesChanged(self, algorithm, changes):
        pass
