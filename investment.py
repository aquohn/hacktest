import json, csv

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, Slider

from datetime import datetime as dt

TICKERS = ["PTL", "BIBL", "BLES", "FDLS", "GLRY", "IBD", "ISMD", "RISN", "WWJD", "KOCG", "AVEGX", "AVEDX", "CATH", "CEFA",
           "CSPX.L", "VUAA.L", "VWRA.L", "IWDA.L"]
FMP_PATH = "Data/FMP/"
AV_PATH = "Data/AV/"

def extract_fmp(path, tickers):
    fmpcloses = {}
    fmpdays = {}
    fmpendcloses = {}

    for t in tickers:
        with open(path + t + ".json") as file:
            data = json.loads(file.read())
        fmpcloses[t] = {}
        fmpdays[t] = {}
        fmpts = data.get("historical")
        if fmpts:
            for datum in fmpts:
                day = datum["date"]
                fmpcloses[t][day] = datum["adjClose"]

                # record days of each month
                y, m, d = day.split("-")
                ym = y + "-" + m
                if ym in fmpdays[t]:
                    fmpdays[t][ym].append(int(d))
                else:
                    fmpdays[t][ym] = [int(d)]

    for t, days in fmpdays.items():
        fmpendcloses[t] = {}
        for ym, ds in days.items():
            lastday = ym + "-" + ("%02d" % max(ds))
            lastdate = dt.strptime(lastday, "%Y-%m-%d")
            fmpendcloses[t][lastday] = fmpcloses[t][lastday]

    return fmpendcloses

def extract_av(path, tickers):
    avdata = {}

    for t in tickers:
        with open(path + t + ".json") as file:
            data = json.loads(file.read())
        avdata[t] = {}
        avts = data.get("Monthly Adjusted Time Series")
        if avts:
            for day, prices in avts.items():
                date = dt.strptime(day, "%Y-%m-%d")
                avdata[t][date] = {ptype: float(price) for ptype, price in prices.items()}

    return avdata

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
    return d

"""
Get the earliest date of each ticker in `d`.
"""
def starts(d):
    dates = []
    for v in d:
        dates.append(min(v.keys()));
    return dates

"""
Given an dict `d` of the format `{ticker: {date: price}}`, return a dict where prices
before `start` are truncated. For the default `start=None`, takes the earliest date
where all tickers have data.
"""
def fromstart(d, start=None):
    if start is None:
        start = max(starts(d.values()))
    td = d.copy()
    for t, v in d.items():
        td[t] = {}
        if min(v.keys()) >= start:
            continue
        for date, p in v.items():
            if date >= start:
                td[t][date] = p

    return td

"""
Simple momentum strategy: sell in a down month and buy SGOV, buy after next up month.
"""
def momentum(weights, data, budget=1000, start=None):
    startdates = starts(d.values())
    if start is None:
        start = max(startdates)
    holdings = {t: [] for t, w in weights.items() if w > 0}
    cash = [0.0]
    # allocate initial holdings
    total_weight = sum([weights[t] for t in holdings.keys()])
    for t in holdings.keys():
        w = weights[t]
        num = int(ceil(w / total_weight * budget))




def buyandhold(weights, data):

def main():
    acwi = extract_csv("Data/ACWI.csv", "%b %d, %Y", 1)
    spx = extract_csv("Data/SPX.csv", "%m/%d/%Y", 1)
    d = extract_av(AV_PATH, TICKERS)

    fig, ax = plt.subplots()
    ax.set_xlabel('Time')
    fig.subplots_adjust(bottom=0.5)

    indices = {"SPX": spx, "AWCI": awci}



if __name__ == "__main__":
    main()
