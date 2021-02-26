class VentralCalibratedComputer(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2017, 1, 1)  # Set Start Date
        self.SetCash(10)  # Set Strategy Cash
        self.btc = self.AddCrypto("BTCUSD", Resolution.Daily).Symbol
        
        self.max = self.MAX(self.btc, 365)
        self.high = -1
        
        self.invested = 0
        
        self.Schedule.On(self.DateRules.Every(DayOfWeek.Monday), self.TimeRules.At(12, 0), self.deposit)

    def deposit(self):
        self.Portfolio.CashBook["USD"].AddAmount(10)
        self.invested += 10
        
        self.Plot("Strategy Equity", "Amount Invested", self.invested)
        
        if self.high < self.max.Current.Value:
            self.high = self.max.Current.Value
            self.stop_investing = self.Time + timedelta(182)
        
        if self.Time < self.stop_investing:
            self.SetHoldings(self.btc, 1)
