# plotting-fun

Quick stock chart generator. Give it a ticker, get a PNG. No API key needed — uses Yahoo Finance via `yfinance`.

## Output

Each plot is saved to `results/<TICKER>.png` and tracked in git, so charts are visible directly on the GitHub repo page after pushing.

Each chart has two panels:
- **Top**: past year of daily closing prices with 52-week high/low markers and YTD % change
- **Bottom**: most recent trading day at 5-minute resolution with open price reference line

## Usage

```bash
pip install -r requirements.txt

# Single ticker
python plot.py AAPL

# Multiple tickers
python plot.py AAPL MSFT TSLA SPY
```

## Results

Plots are committed to `results/` so they render on GitHub without any Pages setup. Just push and browse.

## Notes

- If the market is closed, the intraday panel shows the most recent trading day's data
- Y-axis never starts at zero — range is fitted to the actual price action with padding
- Accepts any ticker symbol yfinance supports (stocks, ETFs, indices like ^GSPC)
