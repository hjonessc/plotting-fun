# plotting-fun

Stock chart generator — takes one or more ticker symbols, pulls a year of daily data and the most recent trading day at 5-min resolution, and saves a two-panel PNG to `results/`.

---

## Shared Dispatch Resources

- Profile & preferences: `~/Cowork/code/claude-dispatch/DISPATCH_PROFILE.md`
- Workflow patterns: `~/Cowork/code/claude-dispatch/docs/dispatch-workflows.md`
- PR standards: `~/Cowork/code/claude-dispatch/standards/pr-standards.md`
- Knowledge system: `~/Cowork/CLAUDE.md`

Read DISPATCH_PROFILE.md before starting any task in this repo.

---

## Project Structure

```
plotting-fun/
  plot.py          ← main script, accepts one or more ticker symbols
  requirements.txt ← yfinance, matplotlib
  results/         ← output PNGs, tracked in git (visible on GitHub)
  pr-standards.md  ← PR conventions
```

---

## Build & Test

```bash
# install deps (first time)
pip install -r requirements.txt

# run
python plot.py AAPL
python plot.py AAPL MSFT SPY
```

---

## Key Conventions

- `results/` is tracked in git — always commit and push new PNGs so they're visible on GitHub
- Y-axis is fitted to actual price range, never starts at zero
- No API key needed — uses yfinance (Yahoo Finance)
