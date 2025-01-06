import talib
import numpy as np
import pandas as pd

# Criar dados de exemplo
open = np.array([1, 2, 3, 4, 5], dtype=float)
high = np.array([2, 3, 4, 5, 6], dtype=float)
low = np.array([0.5, 1.5, 2.5, 3.5, 4.5], dtype=float)
close = np.array([1.5, 2.5, 3.5, 4.5, 5.5], dtype=float)

# Detectar padrão Engulfing Bullish
engulfing = talib.CDLENGULFING(open, high, low, close)
print("Engulfing Bullish:", engulfing)