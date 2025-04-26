import json, csv
import pandas as pd
from datetime import datetime as dt

class Extractor(object):
    """
    Extract time series data from multiple JSON files under `path`.

    :param tickers: an iterable of strings, which are the names of files from which we wish to extract data.
    :param path: path to the JSONs containing the ticker data, such that `build_path(path, t)`
    (default: `path + t + ".json"`), for each ticker `t`, is the path to its corresponding JSON.
    """
    def __init__(self, path, tickers):
        self.path = path
        self.tickers = tickers
        self.tickdata = {}

        for t in tickers:
            tpath = self.build_path(path, t)
            try:
                with open(tpath) as file:
                    data = json.loads(file.read())
            except FileNotFoundError:
                print("Warning: File not found:", tpath)
                continue
            ts = self.extract_ticks(data)
            if ts is not None:
                self.tickdata[t] = ts
            else:
                print("Warning: Failed to parse", tpath)

    @staticmethod
    def build_path(path, t):
        return path + t + ".json"

    @staticmethod
    def extract_ticks(data):
        """
        To be overridden with a function which parses the result of `json.loads()`, and `None`
        if it fails to parse the JSON.
        """
        raise NotImplementedError("No implementation for extract_ticks() in this class!")

    def format_data(self):
        """
        To be overridden with a function which formats the expected tick data appropriately.
        """
        raise NotImplementedError("No implementation for format_data() in this class!")

class PriceExtractor(Extractor):
    def format_data(self):
        """
        Formats `self.tickdata`, which is assumed to be a dictionary of dictionaries,
        in the form `date: {tick_type: tick}`, into a data frame.
        """
        # construct df with correct index but dict entries
        df = pd.DataFrame.from_dict(self.tickdata, orient="index").stack().to_frame()
        # convert dict entries to table
        df = pd.DataFrame(df[0].values.tolist(), df.index)
        # convert index to correct types
        lvls = df.index.levels
        df.index = df.index.set_levels([pd.CategoricalIndex(lvls[0]), pd.DatetimeIndex(lvls[1])]).set_names(["Ticker", "Date"])
        df.index = df.index.sort_values()
        return df

class AVExtractor(PriceExtractor):
    @staticmethod
    def extract_ticks(data):
        return data.get("Monthly Adjusted Time Series")

class FMPExtractor(PriceExtractor):
    @staticmethod
    def extract_ticks(data):
        return data.get("historical")

class ACWIExtractor(Extractor):
    @staticmethod
    def extract_ticks(data):
        td = {}
        ts = data["data"]["indexes"][3]["performanceHistory"]
        for t in ts:
            date = dt.strptime(t["date"], "%Y-%m-%d")
            td[date] = float(t["value"])
        return td

    def format_data(self):
        return pd.DataFrame.from_dict(self.tickdata[self.tickers[0]], orient="index", columns=["Value"])

class SPXExtractor(Extractor):
    @staticmethod
    def extract_ticks(data):
        td = {}
        ts = data["indexLevelsHolder"]["indexLevels"]
        for t in ts:
            date = dt.strptime(t["formattedEffectiveDate"], "%d-%b-%Y")
            td[date] = float(t["indexValue"])
        return td

    def format_data(self):
        return pd.DataFrame.from_dict(self.tickdata[self.tickers[0]], orient="index", columns=["Value"])
