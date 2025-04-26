import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.widgets import Button, Slider

from strategies import MomentumStrategy, STRATNAMES
from data import AVExtractor, SPXExtractor, ACWIExtractor
from engine import trade, value
from config import TICKERS, AV_PATH, FMP_PATH, TO_COMPARE

import ipdb

class StrategyComparison(object):
    def __init__(self, tickers, data, indices):
        self.fig, self.ax = plt.subplots()
        self.fig.set_size_inches(12, 12)
        self.ax.set_xlabel('Time')
        self.data = data
        self.weights = {t: 0 for t in tickers}
        self.sliders = {}
        self.budget = 10000
        self.stratnavs = {}

        # may make into parameters later
        sliderheight = 0.05

        self.fig.subplots_adjust(bottom=sliderheight * (len(tickers) + 2))
        # 2 for the top and bottom margins of the sliders

        for name, strat in STRATNAMES.items():
            holds = self.strategy(strategy=strat)
            daterange = holds.index
            nav = [value(holds.loc[date], self.data, date) for date in daterange]
            self.stratnavs[name], = self.ax.plot(daterange, nav, label=name)

        for index, values in indices.items():
            baseline = values.loc[daterange[0]].iloc[0]
            self.ax.plot(daterange, values.loc[daterange].div(baseline).mul(self.budget), label=index)

        height = 0.0
        for t in tickers:
            slideraxes = self.fig.add_axes([0.25, sliderheight + height, 0.65, 0.03])
            self.sliders[t] = Slider(ax=slideraxes, label=t, valmin=0, valmax=10, valinit=self.weights[t])
            self.sliders[t].on_changed(self.update_weights_callback(t))
            height += sliderheight
        self.ax.legend()

    def strategy(self, strategy=MomentumStrategy):
        return trade(self.weights, self.data, strategy, budget=self.budget)

    def update_weights_callback(self, t):
        return lambda w: self.update_weights(t, w)

    def update_weights(self, ticker, newweight):
        self.weights[ticker] = newweight
        for name, strat in STRATNAMES.items():
            holds = trade(self.weights, self.data, strat)
            daterange = holds.index
            nav = [value(holds.loc[date], self.data, date) for date in daterange]
            self.stratnavs[name].set_ydata(nav)
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    acwi = ACWIExtractor("Data/", ["ACWI"]).format_data()
    spx = SPXExtractor("Data/", ["SPX"]).format_data()
    d = AVExtractor(AV_PATH, TICKERS).format_data()
    indices = {"SPX": spx, "AWCI": acwi}
    SC = StrategyComparison(TO_COMPARE, d, indices)
    plt.show(block=False)

