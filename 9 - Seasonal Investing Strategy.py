class TransdimensionalCalibratedChamber(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2000, 1, 1)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        
        self.market = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        self.AddUniverseSelection(
           FineFundamentalUniverseSelectionModel(self.SelectCoarse, self.SelectFine)
        )
        
        self.UniverseSettings.Resolution = Resolution.Daily
        
        self.in_consumer = True
        
        self.consumer_months = [11, 12, 1, 2, 3]

    def SelectCoarse(self, coarse):
        if self.Time.month not in self.consumer_months or (self.in_consumer and self.Portfolio.Invested):
            return []
        return [c.Symbol for c in coarse if c.Price > 5]
        
    def SelectFine(self, fine):
        return [x.Symbol for x in fine if x.AssetClassification.MorningstarSectorCode == MorningstarSectorCode.ConsumerCyclical]

    def into_market(self):
        self.Liquidate()
        self.SetHoldings(self.market, 1)
        self.in_consumer = False
    
    def into_consumer(self, securities):
        self.Liquidate()
        for s in securities:
            self.SetHoldings(s, 1 / len(securities))
        self.in_consumer = True
    
    
    def OnData(self, data):
        if self.Time.month not in self.consumer_months:
            if self.in_consumer:
                self.into_market()
            return
        
        securities = [s for s in data.Keys if s != self.market]
        
        if len(securities) < 1 or (self.in_consumer and self.Portfolio.Invested):
            return
        
        self.into_consumer(securities)
