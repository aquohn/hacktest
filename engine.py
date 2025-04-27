import pandas as pd
from math import ceil, floor

from fees import ibkr_txnfees, dividend

def getnearest(df, date):
    idx = df.index.get_indexer([date], method="nearest")
    return df.loc[df.index.take(idx)]

# TODO make holdings a data frame and unify with below
def latest_value(holdings, data, date):
    val = 0.0
    for t in holdings:
        if len(holdings[t]) == 0:
            continue
        if t == "Cash":
            val += holdings["Cash"][-1]
            continue
        pos = holdings[t][-1]
        val += pos * float(getnearest(data.loc[t], date)["4. close"].iloc[0])
    return val

def value(holdings, data, date):
    val = 0.0
    for t in holdings.index:
        if t == "Cash":
            val += holdings.loc["Cash"]
            continue
        val += holdings.loc[t] * float(getnearest(data.loc[t], date)["4. close"].iloc[0])
    return val

class Trade(object):
    def __init__(self, data, weights, Strategy, *,
                 reserve="SGOV", budget=10000, start=None, margin=-100):
        self.data = data
        self.set_weights(weights)
        self.univ = self.data[self.data.index.get_level_values("Ticker").isin(self.tickers)]
        self.reserve = reserve
        self.budget = budget
        self.margin = margin
        self.set_daterange(start)
        self.Strategy = Strategy

    def set_daterange(self, start):
        # get range of dates for each ticker
        dates = self.univ.index.to_frame()["Date"].groupby(level="Ticker", observed=True)
        startdates = dates.min()
        if start is None:
            start = startdates.max()
        end = dates.max().max()
        rangemask = (self.univ.index.levels[1] >= start) & (self.univ.index.levels[1] <= end)
        self.daterange = self.univ.index.levels[1].to_series()[rangemask].sort_values()

    def set_weights(self, weights):
        self.weights = weights
        self.tickers = [t for t, w in self.weights.items()]
        self.total_weight = sum([self.weights[t] for t in self.tickers])

    def num_to_hold(self, t, date, pfsize):
        price = float(self.univ.loc[(t, date)]["4. close"])
        num = int(floor(self.weights[t] / self.total_weight * pfsize / price))
        return num

    def compute_trade(self, date):
        """
        Update `holdings` with number of shares to buy and sell, and return expenditure for this trade.
        """
        expenditure = 0.0
        if all(len(self.holdings[t]) == 0 for t in self.tickers):
            pfsize = self.budget
        else:
            pfsize = latest_value(self.holdings, self.data, date)
        for t in self.tickers:
            prevholdings = self.holdings[t][-1] if len(self.holdings[t]) > 0 else 0
            if date not in self.univ.loc[t].index: # bail early if info not available
                self.holdings[t].append(prevholdings)
                continue

            entry = self.univ.loc[(t, date)]
            num = self.num_to_hold(t, date, pfsize)
            expenditure += dividend(t, prevholdings, float(entry["7. dividend amount"]))

            buy, sell = self.strategy.buysell(t, entry)
            price = float(entry["4. close"])
            if num - prevholdings > 0 and buy: # buy
                expenditure -= (num - prevholdings) * price
                # TODO only buy amount that will not put us below margin
                expenditure -= ibkr_txnfees(t, num, price, sell=False)
                self.holdings[t].append(num)
            elif prevholdings > 0 and sell: # sell
                expenditure += prevholdings * price
                expenditure -= ibkr_txnfees(t, prevholdings, price, sell=True)
                self.holdings[t].append(0)
            else:
                self.holdings[t].append(prevholdings)
        return expenditure

    def handle_reserve(self, date, expenditure):
        """
        Put spare cash in reserve (typically bond fund where cash is parked), or liquidate reserve if there is a shortfall.
        """
        balance = expenditure + (self.holdings["Cash"][-1] if len(self.holdings["Cash"]) > 0 else self.budget)
        reshold = self.holdings[self.reserve]
        try:
            resv = self.data.loc[self.reserve, date]
            balance += float(resv["7. dividend amount"]) * reshold[-1]
            price = float(resv["4. close"])
            if balance < self.margin:
                resv_tosell = min(reshold[-1], ceil(-1 * balance / price))
                if resv_tosell > 0:
                    balance += resv_tosell * price
                    balance -= ibkr_txnfees(self.reserve, resv_tosell, price, sell=True)
                reshold.append(reshold[-1] - resv_tosell)
            elif balance > 0:
                resv_tobuy = floor(balance / price)
                if resv_tobuy > 0:
                    balance -= resv_tobuy * price
                    balance -= ibkr_txnfees(self.reserve, resv_tobuy, price, sell=False)
                reshold.append(reshold[-1] + resv_tobuy)
            else:
                reshold.append(reshold[-1])
        except (KeyError, IndexError):
            reshold.append(reshold[-1] if len(reshold) > 0 else 0)
        self.holdings["Cash"].append(balance)

    def execute(self):
        """
        Execute a trading strategy and return its performance over time as a dataframe.

        FIXME assumes all tickers have same month end date. Snap to ME?
        """
        if self.total_weight == 0:
            self.holdings = {t: [0] * len(self.daterange) for t in self.tickers}
            return pd.DataFrame(self.holdings, index=self.daterange)

        self.holdings = {t: [] for t in self.tickers}
        self.holdings["Cash"] = []
        self.holdings[self.reserve] = []
        self.strategy = self.Strategy(self.tickers)

        for date in self.daterange:
            expenditure = self.compute_trade(date)
            self.handle_reserve(date, expenditure)

        return pd.DataFrame(self.holdings, index=self.daterange)
