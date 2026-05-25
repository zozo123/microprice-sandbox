"""
Parameter sweep: AS vs symmetric control market making.

Runs the same simulator as demo.py over a grid of (gamma, sigma) and
emits:
  - results.json   numeric summary for every cell
  - pnl_hist.png   P&L histograms at gamma in {0.1, 0.5}, reproducing
                   the paper's Figures 11 and 12
  - sweep.png      AS vs control: inventory-stdev reduction across
                   the (gamma, sigma) grid

Run inside an Islo sandbox; matplotlib gets installed there.
"""

import json
import math
import os
import random
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


S0       = 100.0
T        = 1.0
N        = 200
A_RATE   = 140.0
K_DECAY  = 1.5
EPISODES = int(os.environ.get("EPISODES", "3000"))
SEED     = 42


def run_episode(gamma, sigma, rng):
    dt = T / N
    s = S0
    x_as = x_ctl = 0.0
    q_as = q_ctl = 0

    for i in range(N):
        s += sigma * math.sqrt(dt) * rng.gauss(0.0, 1.0)
        t_left = T - i * dt

        r = s - q_as * gamma * sigma * sigma * t_left
        half = (
            gamma * sigma * sigma * t_left
            + (2.0 / gamma) * math.log1p(gamma / K_DECAY)
        )
        bid_as = r - half
        ask_as = r + half

        def hit(d):
            return 1.0 - math.exp(-A_RATE * math.exp(-K_DECAY * d) * dt)

        if rng.random() < hit(ask_as - s):
            x_as += ask_as; q_as -= 1
        if rng.random() < hit(s - bid_as):
            x_as -= bid_as; q_as += 1
        if rng.random() < hit(half):
            x_ctl += s + half; q_ctl -= 1
        if rng.random() < hit(half):
            x_ctl -= s - half; q_ctl += 1

    return x_as + q_as * s, q_as, x_ctl + q_ctl * s, q_ctl


def cell(gamma, sigma):
    rng = random.Random(SEED)
    as_p, as_q, c_p, c_q = [], [], [], []
    for _ in range(EPISODES):
        a, b, c, d = run_episode(gamma, sigma, rng)
        as_p.append(a); as_q.append(b)
        c_p.append(c);  c_q.append(d)
    return {
        "gamma": gamma,
        "sigma": sigma,
        "as":      {"pnl_mean": statistics.mean(as_p), "pnl_std": statistics.pstdev(as_p),
                    "q_mean":   statistics.mean(as_q), "q_std":   statistics.pstdev(as_q),
                    "samples":  as_p},
        "control": {"pnl_mean": statistics.mean(c_p),  "pnl_std": statistics.pstdev(c_p),
                    "q_mean":   statistics.mean(c_q),  "q_std":   statistics.pstdev(c_q),
                    "samples":  c_p},
    }


def hist_panel(results, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0), sharey=True)
    target_gammas = [0.1, 0.5]
    sigma_pick = 2.0
    for ax, g in zip(axes, target_gammas):
        cells = [r for r in results if abs(r["gamma"] - g) < 1e-9 and abs(r["sigma"] - sigma_pick) < 1e-9]
        if not cells:
            continue
        r = cells[0]
        bins = 40
        ax.hist(r["as"]["samples"],      bins=bins, alpha=0.65, label="Avellaneda-Stoikov", color="#1f7b93")
        ax.hist(r["control"]["samples"], bins=bins, alpha=0.55, label="symmetric control",  color="#e35e46")
        ax.set_title(rf"$\gamma$ = {g},  $\sigma$ = {sigma_pick}", fontsize=11)
        ax.set_xlabel("episode P&L")
        ax.grid(alpha=0.25, linewidth=0.5)
        ax.legend(frameon=False, fontsize=9)
    axes[0].set_ylabel("episodes")
    fig.suptitle("AS vs. symmetric control: per-episode P&L distribution", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def heatmap_panel(results, out_path):
    gammas = sorted({r["gamma"] for r in results})
    sigmas = sorted({r["sigma"] for r in results})
    inv_red = [[0.0] * len(gammas) for _ in sigmas]
    pnl_diff = [[0.0] * len(gammas) for _ in sigmas]
    for r in results:
        gi = gammas.index(r["gamma"])
        si = sigmas.index(r["sigma"])
        inv_red[si][gi]  = r["control"]["q_std"] / max(r["as"]["q_std"], 1e-9)
        pnl_diff[si][gi] = r["as"]["pnl_mean"] - r["control"]["pnl_mean"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    im0 = axes[0].imshow(inv_red, aspect="auto", origin="lower",
                         cmap="viridis",
                         extent=[gammas[0], gammas[-1], sigmas[0], sigmas[-1]])
    axes[0].set_title("inventory-stdev reduction  (control / AS)")
    axes[0].set_xlabel(r"risk-aversion $\gamma$")
    axes[0].set_ylabel(r"volatility $\sigma$")
    fig.colorbar(im0, ax=axes[0]).set_label("× tighter")

    im1 = axes[1].imshow(pnl_diff, aspect="auto", origin="lower",
                         cmap="RdBu_r",
                         extent=[gammas[0], gammas[-1], sigmas[0], sigmas[-1]])
    axes[1].set_title("mean P&L:  AS − control")
    axes[1].set_xlabel(r"risk-aversion $\gamma$")
    axes[1].set_ylabel(r"volatility $\sigma$")
    fig.colorbar(im1, ax=axes[1]).set_label("$")

    fig.suptitle("Parameter sweep across (γ, σ)", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def main():
    gammas = [0.05, 0.1, 0.25, 0.5, 0.75, 1.0]
    sigmas = [1.0, 1.5, 2.0, 2.5, 3.0]
    print(f"sweep: gammas={gammas} sigmas={sigmas} episodes={EPISODES}", file=sys.stderr)
    results = []
    for g in gammas:
        for s in sigmas:
            r = cell(g, s)
            results.append(r)
            print(f"  gamma={g:.2f} sigma={s:.2f}  "
                  f"AS pnl={r['as']['pnl_mean']:.2f}±{r['as']['pnl_std']:.2f} q_std={r['as']['q_std']:.2f}  |  "
                  f"ctl pnl={r['control']['pnl_mean']:.2f}±{r['control']['pnl_std']:.2f} q_std={r['control']['q_std']:.2f}",
                  file=sys.stderr)

    out = os.environ.get("OUT_DIR", "/tmp/out")
    os.makedirs(out, exist_ok=True)

    serializable = [
        {**{k: v for k, v in r.items() if k not in ("as", "control")},
         "as":      {k: v for k, v in r["as"].items() if k != "samples"},
         "control": {k: v for k, v in r["control"].items() if k != "samples"}}
        for r in results
    ]
    with open(os.path.join(out, "results.json"), "w") as f:
        json.dump(serializable, f, indent=2)
    hist_panel(results, os.path.join(out, "pnl_hist.png"))
    heatmap_panel(results, os.path.join(out, "sweep.png"))
    print(f"wrote {out}/results.json, pnl_hist.png, sweep.png", file=sys.stderr)


if __name__ == "__main__":
    main()
