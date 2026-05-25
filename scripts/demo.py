"""
Avellaneda-Stoikov market making vs symmetric quoting.

Reproduces §3 of Sasson/Ho/Samson, "High Frequency Trading Strategies"
(Stanford MSE448) using the paper's own assumptions:
  - mid price is geometric Brownian motion with volatility sigma  (eq. 15)
  - reservation price r(s,q,t) = s - q*gamma*sigma^2*(T-t)        (paper §3.1.2)
  - optimal half-spread  gamma*sigma^2*(T-t) + (2/gamma) ln(1 + gamma/k)
    (Avellaneda-Stoikov 2008, closed form for exponential arrivals)
  - market-order arrival intensity lambda(delta) = A * exp(-k*delta)  (eq. 24)
  - control strategy quotes symmetrically around the mid at the same
    half-spread, matching the paper's setup.

Inventory is mark-to-market at the terminal mid; we report mean and stdev
of P&L and inventory across many independent episodes, the same summary
the paper reports in Tables 1 and 2.
"""

import math
import random
import statistics

S0       = 100.0
SIGMA    = 2.0
T        = 1.0
N        = 200
A_RATE   = 140.0
K_DECAY  = 1.5
GAMMAS   = [0.1, 0.5]
EPISODES = 2000
SEED     = 42


def run_episode(gamma, rng):
    dt = T / N
    s = S0
    x_as = x_ctl = 0.0
    q_as = q_ctl = 0

    for i in range(N):
        s += SIGMA * math.sqrt(dt) * rng.gauss(0.0, 1.0)
        t_left = T - i * dt

        r = s - q_as * gamma * SIGMA * SIGMA * t_left
        half_spread = (
            gamma * SIGMA * SIGMA * t_left
            + (2.0 / gamma) * math.log1p(gamma / K_DECAY)
        )
        bid_as = r - half_spread
        ask_as = r + half_spread
        delta_b_as = s - bid_as
        delta_a_as = ask_as - s

        delta_ctl = half_spread

        def hit_prob(d):
            return 1.0 - math.exp(-A_RATE * math.exp(-K_DECAY * d) * dt)

        if rng.random() < hit_prob(delta_a_as):
            x_as += ask_as
            q_as -= 1
        if rng.random() < hit_prob(delta_b_as):
            x_as -= bid_as
            q_as += 1
        if rng.random() < hit_prob(delta_ctl):
            x_ctl += s + delta_ctl
            q_ctl -= 1
        if rng.random() < hit_prob(delta_ctl):
            x_ctl -= s - delta_ctl
            q_ctl += 1

    pnl_as  = x_as  + q_as  * s
    pnl_ctl = x_ctl + q_ctl * s
    return pnl_as, q_as, pnl_ctl, q_ctl


def summary(values):
    return statistics.mean(values), statistics.pstdev(values)


def main():
    rng = random.Random(SEED)
    print(f"AS vs control market making, episodes={EPISODES}, steps/episode={N}")
    print(f"sigma={SIGMA}  A={A_RATE}  k={K_DECAY}  T={T}\n")
    print(f"{'gamma':>6} {'strategy':>8} {'profit':>10} {'std(P)':>8} {'avg(q)':>8} {'std(q)':>8}")
    for gamma in GAMMAS:
        as_p, as_q, c_p, c_q = [], [], [], []
        for _ in range(EPISODES):
            a, b, c, d = run_episode(gamma, rng)
            as_p.append(a); as_q.append(b)
            c_p.append(c);  c_q.append(d)
        m_ap, s_ap = summary(as_p)
        m_aq, s_aq = summary(as_q)
        m_cp, s_cp = summary(c_p)
        m_cq, s_cq = summary(c_q)
        print(f"{gamma:>6.2f} {'AS':>8} {m_ap:>10.3f} {s_ap:>8.3f} {m_aq:>+8.3f} {s_aq:>8.3f}")
        print(f"{gamma:>6.2f} {'control':>8} {m_cp:>10.3f} {s_cp:>8.3f} {m_cq:>+8.3f} {s_cq:>8.3f}")
        edge_p = (m_ap - m_cp)
        edge_q = (s_cq - s_aq)
        print(f"       AS-vs-control: profit_delta={edge_p:+.3f}, "
              f"inv_stdev_reduction={edge_q:+.3f}\n")


if __name__ == "__main__":
    main()
