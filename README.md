# microprice-sandbox

Reproducing **Sasson, Ho & Samson — *High Frequency Trading Strategies*** (Stanford MSE448, 2018) inside a fresh [Islo](https://islo.dev) sandbox.

> **Live writeup & charts:** https://zozo123.github.io/microprice-sandbox

The Avellaneda–Stoikov optimal market-maker steers its quotes around its current inventory; a symmetric control always quotes around the mid. AS roughly **halves inventory variance** and meaningfully **tightens P&L variance** — at the cost of some mean P&L at low risk-aversion and a premium at high risk-aversion.

## Run it

```sh
export ISLO_API_KEY=ak_…
git clone https://github.com/zozo123/microprice-sandbox && cd microprice-sandbox
./scripts/run_in_sandbox.sh
```

About 90 seconds end-to-end: warm an Islo lease, `pip install matplotlib` inside, run a 6 × 5 (γ, σ) sweep at 3 000 episodes/cell, tar the artifacts back, release the lease. Output lands in `assets/` (`results.json`, `pnl_hist.png`, `sweep.png`).

If you don't want crabbox + a lease, the simulator itself is pure stdlib and runs anywhere:

```sh
python3 scripts/demo.py
```

## Why a sandbox?

| problem | what a sandbox fixes |
|---|---|
| Jupyter kernel state leaking across parameter sweeps | each cell gets a fresh process |
| matplotlib version drift between machines | pin the image, not the laptop |
| `pip install` polluting the host | the host stays untouched |
| fanning out a parameter grid | one sandbox per cell, naturally |

## What's in here

- `scripts/demo.py` — pure-stdlib AS vs control simulator, prints a table
- `scripts/sweep.py` — (γ, σ) grid sweep; needs matplotlib (installs inside the sandbox)
- `scripts/run_in_sandbox.sh` — one-shot: warmup → run → release
- `assets/` — the most recent sandbox run's `results.json` and PNGs (served by GitHub Pages)
- `index.html` — the writeup at the URL above

## Caveats

This is a synthetic reproduction. The paper fits σ and the arrival decay κ on real AAPL and CVX L1 data; the absolute dollar magnitudes in their Tables 1 and 2 reflect those fits. I use the paper's structural model (GBM mid, exponential arrival rates) with stylized constants — the *qualitative* claim (AS halves inventory variance, tightens P&L variance) reproduces; absolute dollars do not, and shouldn't be expected to. The microprice section of the paper isn't reproduced here because it requires a real order book.

## References

1. Sasha Stoikov. *The micro-price: a high frequency estimator of future prices.* 2017.
2. Marco Avellaneda and Sasha Stoikov. *High frequency trading in a limit order book.* Quantitative Finance 8:217–224, 04 2008.
3. Sasson, Ho, Samson. *High Frequency Trading Strategies.* Stanford MSE448, 2018. [PDF](https://stanford.edu/class/msande448/2018/Final/Reports/gr1.pdf)

## License

MIT.
