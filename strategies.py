"""
Simple momentum strategy: sell in a down month, buy after next up month.
"""
class MomentumStrategy(object):
    def __init__(self, tickers):
        self.momentum = {t: [] for t in tickers}

    def buysell(self, t, entry):
        self.momentum[t].append(float(entry["5. adjusted close"]))
        if len(self.momentum[t]) == 3:
            self.momentum[t] = self.momentum[t][1:] # only look at two most recent values

        m = self.momentum[t]
        l = len(m)
        if l < 2: # not enough data
            return True, True
        grad = (m[1] - m[0]) / m[0]
        if grad >= -0.05: # up/sideways/at most down 5%; buy or maintain
            return True, False
        else: # down; sell or don't buy
            return False, True

"""
Just buy and hold.
"""
class BAHStrategy(object):
    def __init__(self, tickers):
        pass

    def buysell(self, t, entry):
        return True, False

STRATNAMES = {"Momentum": MomentumStrategy, "Buy and Hold": BAHStrategy}

