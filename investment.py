import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.widgets import Button, Slider

from strategies import MomentumStrategy, STRATNAMES
from data import AVExtractor, SPXExtractor, ACWIExtractor
from engine import Trade, value
from config import TICKERS, AV_PATH, FMP_PATH, TO_COMPARE

import ipdb

class StrategyComparison(object):
    def __init__(self, tickers, data, indices, budget=10000):
        self.fig, self.ax = plt.subplots()
        self.fig.set_size_inches(12, 12)
        self.ax.set_xlabel('Time')
        self.data = data
        self.weights = {t: 0 for t in tickers}
        self.sliders = {}
        self.budget = budget
        self.stratnavs = {}
        self.strattrades = {}

        # may make into parameters later
        sliderheight = 0.05

        self.fig.subplots_adjust(bottom=sliderheight * (len(tickers) + 2))
        # 2 for the top and bottom margins of the sliders

        for name, strat in STRATNAMES.items():
            self.strattrades[name] = Trade(self.data, self.weights, strat, budget=self.budget)
            holds = self.strattrades[name].execute()
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

    def update_weights_callback(self, t):
        return lambda w: self.update_weights(t, w)

    def update_weights(self, ticker, newweight):
        # ipdb.set_trace()
        self.weights[ticker] = newweight
        for name, strat in STRATNAMES.items():
            self.strattrades[name].set_weights(self.weights)
            holds = self.strattrades[name].execute()
            daterange = holds.index
            nav = [value(holds.loc[date], self.data, date) for date in daterange]
            self.stratnavs[name].set_ydata(nav)
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

if __name__ == "__main__":
    acwi = ACWIExtractor("Data/", ["ACWI"]).format_data()
    spx = SPXExtractor("Data/", ["SPX"]).format_data()
    d = AVExtractor(AV_PATH, TICKERS).format_data()
    indices = {"SPX": spx, "AWCI": acwi}
    SC = StrategyComparison(TO_COMPARE, d, indices, budget=100000)
    plt.show()

