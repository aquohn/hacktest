GBP_TO_USD = 1.22 # TODO use historical data
GSTP1 = 1.09 # GST + 1.00

"""
IBKR txn fees. Assume worst case if range is given.
"""
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

