import json, csv

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.widgets import Button, Slider

from datetime import datetime as dt

import ipdb

TICKERS = ["PTL", "BIBL", "BLES", "FDLS", "GLRY", "IBD", "ISMD", "RISN", "WWJD", "KOCG", "AVEGX", "AVEDX", "CATH", "CEFA",
           "CSPX.L", "VUAA.L", "VWRA.L", "IWDA.L", "SGOV"]
FMP_PATH = "Data/FMP/"
AV_PATH = "Data/AV/"

"""
IBKR txn fees. Assume worst case if range is given.
"""
GBP_TO_USD = 1.22 # TODO use historical data
GSTP1 = 1.09 # GST + 1.00

def ibkr_txnfees(ticker, amount, value, sell=False):
    if ticker[-2:] == ".L":
        return lse_fixed(amount, value, sell)
    else:
        return us_fixed(amount, value, sell)

def us_reg(amount, value, sell=False):
    reg = 0.0000278 * value + 0.0000469 * amount
    if sell:
        reg += 0.000166 * amount
    return reg

def us_fixed(amount, value, sell=False):
    broker = min(max(0.005 * amount, 1.00), 0.01 * value) * GSTP1
    return broker + us_reg(amount, value, sell)

def us_tiered(amount, value, sell=False):
    broker = min(max(0.0035 * amount, 0.35), 0.01 * value) * GSTP1
    exchange = 0.0030 * amount
    # not sure if passthrough applies to GST but just in case
    passthrough = (0.000175 + 0.000563) * broker
    clearing = 0.00020 * amount
    return broker + exchange + passthrough + clearing + us_reg(amount, value, sell)

def lse_fixed(amount, value, sell=False):
    broker = max(0.05 / 100 * amount, 4.00) * GSTP1
    return broker

def lse_tiered(amount, value, sell=False):
    broker = min(max(0.05 / 100 * value, 0.35), 39.00) * GSTP1
    exchange = max(0.000045 * value, 0.10 * GBP_TO_USD)
    clearing = 0.06 * GBP_TO_USD
    return broker + exchange + clearing

"""
Calculate dividends with withholding tax.
"""
def dividend(ticker, holding, divdamt):
    if ticker[:-2] == ".L":
        rate = 0.15
    else:
        rate = 0.30
    return holding * divdamt * (1 - rate)

"""
Extract price data of `tickers` from JSONs at `path`, where `extract` extracts
prices in the form `date: {price_type: price}` from the result of `json.loads`.
"""
def extract_prices(path, tickers, extract):
    prices = {}

    for t in tickers:
        try:
            with open(path + t + ".json") as file:
                data = json.loads(file.read())
        except FileNotFoundError:
            print("Warning: File not found for", t)
        ts = extract(data)
        if ts is not None:
            prices[t] = ts
        else:
            print("Warning: Failed to parse", t)

    # construct df with correct index but dict entries
    df = pd.DataFrame.from_dict(prices, orient="index").stack().to_frame()
    # convert dict entries to table
    df = pd.DataFrame(df[0].values.tolist(), df.index)
    # convert index to correct types
    lvls = df.index.levels
    df.index = df.index.set_levels([pd.CategoricalIndex(lvls[0]), pd.DatetimeIndex(lvls[1])]).set_names(["Ticker", "Date"])
    df.index = df.index.sort_values()
    return df

def extract_fmp(path, tickers):
    return extract_prices(path, tickers, lambda data: data.get("historical"))

def extract_av(path, tickers):
    return extract_prices(path, tickers, lambda data: data.get("Monthly Adjusted Time Series"))

def extract_csv(path, datefmt, priceidx, dateidx = 0):
    d = {}
    with open(path) as data:
        dreader = csv.reader(data)
        for l in dreader:
            try:
                date = dt.strptime(l[dateidx], datefmt)
            except ValueError:
                continue # not a date entry
            d[date] = float(l[priceidx])
    return pd.DataFrame.from_dict(d, orient="index", columns=["Value"])

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
Simple momentum strategy: sell in a down month and buy SGOV, buy after next up month.

FIXME assumes all tickers have same month end date. Snap to ME?
FIXME handle weight = 0
"""
def momentum(weights, data, budget=10000, start=None):
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

    holdings = {t: [] for t in tickers}
    holdings["Cash"] = []
    holdings["SGOV"] = []
    momentum = {t: [] for t in tickers}

    def num_to_hold(t, date, pfsize):
        price = float(univ.loc[(t, date)]["4. close"])
        num = int(np.ceil(weights[t] / total_weight * pfsize / price))
        return num

    # return (buy, sell)
    def buysell(m):
        l = len(m)
        if l < 2: # not enough data
            return True, True
        grad = (m[1] - m[0]) / m[0]
        if grad >= -0.05: # up/sideways; buy or maintain
            return True, False
        else: # down; sell or don't buy
            return False, True

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
            momentum[t].append(float(entry["5. adjusted close"]))
            if len(momentum[t]) == 3:
                momentum[t] = momentum[t][1:] # only look at two most recent values

            buy, sell = buysell(momentum[t])
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

        # account for cash
        balance = expenditure + (holdings["Cash"][-1] if len(holdings["Cash"]) > 0 else budget)
        # TODO buy SGOV
        holdings["Cash"].append(balance)

    return pd.DataFrame(holdings, index=daterange)

# def buyandhold(weights, data):

class Strategy(object):
    def __init__(self, tickers, data, indices):
        self.fig, self.ax = plt.subplots()
        self.fig.set_size_inches(12, 12)
        self.ax.set_xlabel('Time')
        self.data = data
        self.weights = {t: 0 for t in tickers}
        self.sliders = {}
        self.budget = 10000

        # may make into parameters later
        sliderheight = 0.05

        self.fig.subplots_adjust(bottom=sliderheight * (len(tickers) + 2))
        # 2 for the top and bottom margins of the sliders

        strat = self.strategy()
        daterange = strat.index
        for index, values in indices.items():
            baseline = values.loc[daterange[0]].iloc[0]
            self.ax.plot(daterange, values.loc[daterange].div(baseline).mul(self.budget), label=index)
        nav = [value(strat.loc[date], self.data, date) for date in daterange]
        self.stratnav, = self.ax.plot(daterange, nav, label="Strategy")

        height = 0.0
        for t in tickers:
            slideraxes = self.fig.add_axes([0.25, sliderheight + height, 0.65, 0.03])
            self.sliders[t] = Slider(ax=slideraxes, label=t, valmin=0, valmax=10, valinit=self.weights[t])
            self.sliders[t].on_changed(self.update_weights_callback(t))
            height += sliderheight
        self.ax.legend()

    def strategy(self):
        return momentum(self.weights, self.data, budget=self.budget)

    def update_weights_callback(self, t):
        return lambda w: self.update_weights(t, w)

    def update_weights(self, ticker, newweight):
        self.weights[ticker] = newweight
        strat = momentum(self.weights, self.data)
        daterange = strat.index
        nav = [value(strat.loc[date], self.data, date) for date in daterange]
        self.stratnav.set_ydata(nav)
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    acwi = extract_csv("Data/ACWI.csv", "%b %d, %Y", 1)
    spx = extract_csv("Data/SPX.csv", "%m/%d/%Y", 1)
    d = extract_av(AV_PATH, TICKERS)
    indices = {"SPX": spx, "AWCI": acwi}
    S = Strategy([
                  "PTL", # largest 500
                  "BIBL", # top 100 by Biblical score
                  "WWJD", # international
                  "KOCG", "AVEDX", # "AVEGX", # Catholic
                  "CATH", "CEFA", # "Catholic values"
                  "CSPX.L", "VWRA.L", # "IWDA.L", "VUAA.L", # global indices
                 ], d, indices)
    plt.show(block=False)

