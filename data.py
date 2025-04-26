import json, csv
import pandas as pd
from datetime import datetime as dt

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
