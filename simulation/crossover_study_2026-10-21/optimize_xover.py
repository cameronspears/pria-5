"""Constrained crossover optimisation + EQ-budget study.

Each branch is either a free 4th-order pair (one corner, two section Qs;
covers LR4, BW4 and in-between) or an LR8 (corner only).  Integer tweeter
delay (or woofer delay if negative), polarity and tweeter trim are searched.
Constraint: on-axis sine SPL at 1 m before the OT19 reaches Xmax >= LIMIT.
"""
import json, sys, itertools
import numpy as np
from scipy.optimize import differential_evolution, least_squares
sys.path.insert(0, '.')
from xover_model import *

LR8Q = (0.5412, 1.3066)


def branch(model, kind, family, fc, q1=0.7071, q2=0.7071):
    t = "lp" if kind == "lo" else "hp"
    if family == "4th":
        return rbj(t, fc, q1, model.g) * rbj(t, fc, q2, model.g)
    if family == "LR8":
        return (rbj(t, fc, LR8Q[0], model.g) * rbj(t, fc, LR8Q[1], model.g)) ** 2
    raise ValueError(family)


def unpack(x, fam_lo, fam_hi):
    fl, ql1, ql2, fh, qh1, qh2, tg = x
    return dict(fc_lo=fl, q_lo=(ql1, ql2), fc_hi=fh, q_hi=(qh1, qh2), t_gain=tg,
                fam_lo=fam_lo, fam_hi=fam_hi)


def build(model, p):
    lo = branch(model, "lo", p["fam_lo"], p["fc_lo"], *p["q_lo"])
    hi = branch(model, "hi", p["fam_hi"], p["fc_hi"], *p["q_hi"])
    return lo, hi


def optimise(model, limit, seed=1, k_vert_note=""):
    best = None
    for fam_lo, fam_hi in itertools.product(("4th", "LR8"), ("4th", "LR8")):
        for pol in (1, -1):
            for d in range(-2, 11):
                def obj(x):
                    p = unpack(x, fam_lo, fam_hi)
                    lo, hi = build(model, p)
                    m = model.evaluate(lo, hi, p["t_gain"], d, pol, w_gain_db=-4)
                    pen = max(0.0, limit - m["tweeter_limit"]) * 2.0
                    return score(m) + pen
                bounds = [(1300, 4500), (0.45, 1.4), (0.45, 1.4),
                          (1300, 4500), (0.45, 1.4), (0.45, 1.4), (-17, -7)]
                r = differential_evolution(obj, bounds, seed=seed, maxiter=60, popsize=12,
                                           tol=1e-6, polish=True)
                if best is None or r.fun < best[0]:
                    p = unpack(r.x, fam_lo, fam_hi)
                    best = (r.fun, p, d, pol)
    f, p, d, pol = best
    lo, hi = build(model, p)
    m = model.evaluate(lo, hi, p["t_gain"], d, pol, w_gain_db=-4)
    return dict(objective=float(f), delay_samples=d, polarity=pol,
                params={k: (list(v) if isinstance(v, tuple) else v) for k, v in p.items()},
                metrics=m, score=score(m))


def eq_budget(model, lo, hi, tg, d, pol, nmax=3, band=(1000, 12000)):
    """Greedy common PEQs (pre-crossover) that flatten the listening window."""
    filters = []
    out = []
    b = model.band(*band)

    def lw_err(eq):
        _, _, o = model.responses(lo, hi, tg, d, pol, -4, eq)
        lw = model.smooth(model.listening_window(o), 6)
        e = lw[b] - np.mean(lw[b])
        return e

    def eq_of(fl):
        eq = np.ones_like(model.g, complex)
        for f0, q, gdb in fl:
            eq = eq * rbj("peak", f0, q, model.g, gdb)
        return eq

    e0 = lw_err(None)
    out.append(dict(n=0, lw_rms=float(np.sqrt(np.mean(e0 ** 2))), filters=[]))
    for n in range(1, nmax + 1):
        best = None
        for f0 in np.geomspace(band[0], band[1], 16):
            x0 = [np.log(f0), 1.0, 0.0]
            r = least_squares(lambda x: lw_err(eq_of(filters + [(np.exp(x[0]), x[1], x[2])])), x0,
                              bounds=([np.log(band[0]), 0.5, -6], [np.log(band[1]), 4.0, 3]))
            if best is None or r.cost < best.cost:
                best = r
        filters.append((float(np.exp(best.x[0])), float(best.x[1]), float(best.x[2])))
        # re-polish all jointly
        def all_err(x):
            fl = [(np.exp(x[3*i]), x[3*i+1], x[3*i+2]) for i in range(len(filters))]
            return lw_err(eq_of(fl))
        x0 = np.ravel([[np.log(a), q, g] for a, q, g in filters])
        lb = np.ravel([[np.log(band[0]), 0.5, -6]] * len(filters))
        ub = np.ravel([[np.log(band[1]), 4.0, 3]] * len(filters))
        r = least_squares(all_err, x0, bounds=(lb, ub))
        filters = [(float(np.exp(r.x[3*i])), float(r.x[3*i+1]), float(r.x[3*i+2])) for i in range(len(filters))]
        e = all_err(r.x)
        eq = eq_of(filters)
        wv, tv, o = model.responses(lo, hi, tg, d, pol, -4, eq)
        on_rms, _ = model.flat_dev(db(o["axis"]), *band)
        out.append(dict(n=n, lw_rms=float(np.sqrt(np.mean(e ** 2))), on_rms=on_rms,
                        lw_ptp=float(np.ptp(e)),
                        filters=[dict(hz=round(a, 0), q=round(q, 2), gain_db=round(g, 2)) for a, q, g in filters]))
    return out


if __name__ == "__main__":
    model = Model(sys.argv[1] if len(sys.argv) > 1 else "3ms")
    res = {}
    for limit in (97.0, 99.0, 100.0, 101.0, 103.0):
        r = optimise(model, limit)
        res[str(limit)] = r
        m = r["metrics"]
        p = r["params"]
        print(f"limit>={limit}: lo {p['fam_lo']} {p['fc_lo']:.0f} Q{p['q_lo'][0]:.2f}/{p['q_lo'][1]:.2f} | hi {p['fam_hi']} {p['fc_hi']:.0f} Q{p['q_hi'][0]:.2f}/{p['q_hi'][1]:.2f} | tg {p['t_gain']:.2f} d {r['delay_samples']} pol {r['polarity']} | score {r['score']:.3f} on {m['on_rms']:.2f} lw {m['lw_rms']:.2f} vert {m['vert_rms']:.2f} vmin {m['vert_min']:.1f} tw {m['tweeter_limit']:.1f}@{m['tweeter_limit_hz']:.0f} xo {m['acoustic_xo_hz']:.0f}", flush=True)
    json.dump(res, open(f"optimised_{model.info and (sys.argv[1] if len(sys.argv) > 1 else '3ms')}.json", "w"), indent=1)
