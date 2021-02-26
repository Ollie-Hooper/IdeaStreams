class HipsterVioletRabbit(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2014, 9, 10)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        self.AddUniverse(self.MyCoarseFilterFunction, self.MyFineFundamentalFunction)

        self.month = None

    def MyCoarseFilterFunction(self, coarse):
        return [c.Symbol for c in coarse if c.DollarVolume > 1e7]

    def MyFineFundamentalFunction(self, fine):
        tech = [x for x in fine if x.AssetClassification.MorningstarSectorCode == MorningstarSectorCode.Technology]

        unprofitable = [x for x in tech if
                        x.FinancialStatements.IncomeStatement.NormalizedIncomeAsReported.ThreeMonths <= 0]

        sorted_revenue = sorted(unprofitable, key=lambda f: f.FinancialStatements.IncomeStatement.TotalRevenue.OneMonth,
                                reverse=True)

        return [f.Symbol for f in sorted_revenue[:50]]

    def OnData(self, data):
        if self.month == self.Time.month:
            return

        self.month = self.Time.month

        securities = data.Keys
        n_securities = len(securities)

        for s in securities:
            self.SetHoldings(s, 1 / n_securities)
