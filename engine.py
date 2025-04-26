import pandas as pd
import numpy as np

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

"""
Main function to execute a trading strategy.

FIXME assumes all tickers have same month end date. Snap to ME?
"""
def trade(weights, data, strategyf, budget=10000, start=None):
    tickers = [t for t, w in weights.items()]
    univ = data[data.index.get_level_values("Ticker").isin(tickers)]

    # get range of dates for each ticker
    dates = univ.index.to_frame()["Date"].groupby(level="Ticker", observed=True)
    startdates = dates.min()
    if start is None:
        start = startdates.max()
    end = dates.max().max()
    rangemask = (univ.index.levels[1] >= start) & (univ.index.levels[1] <= end)
    daterange = univ.index.levels[1].to_series()[rangemask].sort_values()

    # check holdings
    total_weight = sum([weights[t] for t in tickers])
    if total_weight == 0:
        holdings = {t: [0] * len(daterange) for t in tickers}
        return pd.DataFrame(holdings, index=daterange)

    strategy = strategyf(tickers) # initialise strategy
    holdings = {t: [] for t in tickers}
    holdings["Cash"] = []
    holdings["SGOV"] = []

    def num_to_hold(t, date, pfsize):
        price = float(univ.loc[(t, date)]["4. close"])
        num = int(np.ceil(weights[t] / total_weight * pfsize / price))
        return num

    for date in daterange:
        expenditure = 0.0
        pfsize = latest_value(holdings, data, date)
        for t in tickers:
            prevholdings = holdings[t][-1] if len(holdings[t]) > 0 else 0
            if date not in univ.loc[t].index: # bail early if info not available
                holdings[t].append(prevholdings)
                continue

            entry = univ.loc[(t, date)]
            num = num_to_hold(t, date, pfsize)
            expenditure += dividend(t, prevholdings, float(entry["7. dividend amount"]))

            buy, sell = strategy.buysell(t, entry)
            price = float(entry["4. close"])
            if num - prevholdings > 0 and buy: # buy
                expenditure -= (num - prevholdings) * price
                expenditure -= ibkr_txnfees(t, num, price, sell=False)
                holdings[t].append(num)
            elif prevholdings > 0 and sell: # sell
                expenditure += prevholdings * price
                expenditure -= ibkr_txnfees(t, num, price, sell=True)
                holdings[t].append(0)
            else:
                holdings[t].append(prevholdings)

        # account for cash and SGOV (where cash is parked)
        balance = expenditure + (holdings["Cash"][-1] if len(holdings["Cash"]) > 0 else budget)
        try:
            sgov = data.loc["SGOV", date]
            balance += float(sgov["7. dividend amount"]) * holdings["SGOV"][-1]
            price = float(sgov["4. close"])
            if balance < -100:
                sgov_tosell = min(holdings["SGOV"][-1], np.ceil(-1 * balance / price))
                if sgov_tosell > 0:
                    balance += sgov_tosell * price
                    balance -= ibkr_txnfees(t, sgov_tosell, price, sell=True)
                holdings["SGOV"].append(holdings["SGOV"][-1] - sgov_tosell)
            else:
                sgov_tobuy = np.ceil(balance / price)
                if sgov_tobuy > 0:
                    balance -= sgov_tobuy * price
                    balance -= ibkr_txnfees(t, sgov_tobuy, price, sell=False)
                holdings["SGOV"].append(holdings["SGOV"][-1] + sgov_tobuy)
        except (KeyError, IndexError):
            holdings["SGOV"].append(holdings["SGOV"][-1] if len(holdings["SGOV"]) > 0 else 0)
        holdings["Cash"].append(balance)

    return pd.DataFrame(holdings, index=daterange)
