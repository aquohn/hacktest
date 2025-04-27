# Investment Strategy Backtester

A simple, hackable framework for backtesting investment strategies, geared towards simple strategies that can be executed by a retail investor. Written in plain Python and shell, with the only external dependencies being `pandas` and `matplotlib`. Features include:
- Utilities for pulling and parsing tick data from free sources ([AlphaVantage](https://www.alphavantage.co/), [Financial Modeling Prep](https://site.financialmodelingprep.com/)) and index data ([MSCI](https://www.msci.com/indexes), [S&P](https://www.spglobal.com/spdji/en/index-family/equity/us-equity/))
- Modeling of IBKR transaction fees (using fees for Singapore users)
- Simple dashboard for tweaking strategy parameters and observing their impact

## Installation and Usage

First, register for the free data services of your choice and obtain API keys for them. Then, write these API keys, and the ticker symbols stocks whose data you wish to pull in, to `Data/dataconfig.mk` (following the example `Data/example_dataconfig.mk`). AlphaVantage and Financial Modeling Prep are supported out of the box; some tweaking of the Makefile would allow other sources to be supported. While in the `Data/` directory, pull in the data with `make` (using `make` makes it easier to pull the data in batches, which may be necessary due to free-tier API rate limits).

Install `pandas` and `matplotlib`:
```
python -m venv <VENV NAME>
source <VENV PATH>/bin/activate
pip install pandas matplotlib
```

Currently, the strategies are assumed to be parametrised by assigning weights to certain tickers. Specify the tickers to use in `config.py` (following the example `example_config.py`), then start
```
python -i investment.py
```

## Hacking

`ipython` and `ipdb` are recommended for hacking.

### Data Sources

To use different data sources:
- Modify `Data/Makefile` as mentioned above
- Extend the `Extractor` class in `data.py`
- Update the entry point in `investment.py` to use the new `Extractor`

### Strategies

As hinted above, the current design only supports strategies following a specific format:
- a `Strategy` object is initialised using the tick data, and an allocation of weights to tickers
- the `Strategy` object's `buysell` function evaluates the price data at each time step, to decide whether to buy or to sell
- If buying, calculate the total value of the portfolio, and calculate the fraction of that value which should go to that ticker. Purchase the corresponding number of shares.
- If selling, put any extra cash in a reserve fund (SGOV by default).

Trades use the closing price of the day, ignoring bid-ask spreads, and fractional shares are not supported. Margin interest is not accounted for, although this strategy should not allow the account balance to go negative unless things line up very nicely.

The `buysell` function will be called in sequence over the range of dates which the strategy is being evaluated over. Management of any internal state is left to the implementation of the `buysell` function.

Currently, only two strategies are implemented, buy-and-hold and a simple momentum strategy. Further strategies following this format can be implemented in `strategy.py`.

