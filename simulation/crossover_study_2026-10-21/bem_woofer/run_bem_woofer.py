"""Woofer baffle-step / directivity of the real cabinet shape, by BEM.

Reuses the validated exterior BEM of development/hf_bem_2026_09_04 (Burton-
Miller, Bempp-cl 0.4.2, checked against analytic cases) and its 'flush'
cabinet mesh (142 x 230 x 142 mm, woofer at y = -34 mm = 81 mm above the
bottom, tweeter at 153.2 mm).  The ND91 cone is a uniform piston of 30.4 cm^2
on the mesh's recessed woofer disc; everything else is rigid (PRs inactive:
they only matter below ~150 Hz where radiation is omnidirectional anyway).

Output: complex far-field coefficients for a 1 m^3/s volume velocity, and
the ratio to a free-field monopole (0 dB = full-space radiation, about +6 dB
= half-space).  Sweep 150 Hz-3 kHz (see note at `freqs`).  Limitation: the current build is ~180 mm deep, not 142 mm.
"""
import json, sys, time
from pathlib import Path
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
BEMDIR = HERE.parents[2] / "hf_bem_2026_09_04"
sys.path.insert(0, str(BEMDIR))
import bempp_cl.api as bem  # noqa: E402
from bempp_cl.api.operators.boundary import helmholtz as bh, sparse  # noqa: E402
from bempp_cl.api.operators.far_field import helmholtz as ff  # noqa: E402

bem.DEFAULT_DEVICE_INTERFACE = "numba"
C = 343.0


def solve(mesh, velocity, frequency, directions, tol=1e-4):
    """Same Burton-Miller formulation as hf_bem_2026_09_04/bem_solver.solve,
    with a GMRES tolerance of 1e-4 (that study's 2e-6 stalls at low
    frequency where the cabinet is acoustically small).  1e-4 relative
    residual is far below what matters for response levels in dB."""
    active = velocity != 0
    grid = bem.Grid(mesh.vertices.T, mesh.faces.T, domain_indices=np.where(active, 1, 2))
    pspace = bem.function_space(grid, "P", 1)
    qspace = bem.function_space(grid, "DP", 0, segments=[1])
    k = 2 * np.pi * frequency / C
    identity = sparse.identity(pspace, pspace, pspace)
    iq = sparse.identity(qspace, pspace, pspace)
    K = bh.double_layer(pspace, pspace, pspace, k)
    W = bh.hypersingular(pspace, pspace, pspace, k)
    V = bh.single_layer(qspace, pspace, pspace, k)
    Kp = bh.adjoint_double_layer(qspace, pspace, pspace, k)
    eta = 1j / k
    A = .5 * identity - K + eta * W
    rightop = -(V + eta * (.5 * iq + Kp))
    coef = np.zeros(qspace.global_dof_count, dtype=complex)
    coef[qspace.local2global[active, 0]] = 1j * 2 * np.pi * frequency * RHO * velocity[active]
    q = bem.GridFunction(qspace, coefficients=coef)
    rhs = rightop * q
    p, info, res, it = bem.linalg.gmres(A, rhs, tol=tol, restart=200, maxiter=2000, use_strong_form=True,
                                        return_residuals=True, return_iteration_count=True)
    if info or not np.isfinite(p.coefficients).all():
        raise RuntimeError(f"GMRES failed: {info}, {res[-1]}")
    far = (ff.double_layer(pspace, directions, k) * p - ff.single_layer(qspace, directions, k) * q).ravel()
    return {"far_real": far.real.tolist(), "far_imag": far.imag.tolist(),
            "explicit_relative_residual": float(res[-1]), "iterations": int(it)}

RHO = 1.204
d = np.load(BEMDIR / "meshes/flush_0f782cbd4ed1.npz")
meta = json.loads(str(d["meta"]))
mesh = trimesh.Trimesh(d["vertices"], d["faces"], process=False)
c = mesh.triangles_center * 1000
r = np.hypot(c[:, 0], c[:, 1] - meta["wy_mm"])
mask = (np.abs(c[:, 2] - (-3.7)) < 0.05) & (r <= 31.11)
area = mesh.area_faces[mask].sum()
vel = mask.astype(float) / area                    # volume velocity 1 m^3/s

# directions: horizontal and vertical arcs + an equal-area sphere for power
dirs, tags = [], []
for a in range(0, 181, 10):                      # horizontal (x>0 side), 0..180
    t = np.radians(a); dirs.append([np.sin(t), 0, np.cos(t)]); tags.append(f"h{a}")
for a in range(-90, 91, 10):                     # vertical, + = up
    if a == 0:
        continue
    t = np.radians(a); dirs.append([0, np.sin(t), np.cos(t)]); tags.append(f"v{a}")
n_sph = 400
i = np.arange(n_sph) + 0.5
phi = np.arccos(1 - 2 * i / n_sph); th = np.pi * (1 + 5 ** 0.5) * i
sph = np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]
dirs = np.vstack([np.array(dirs), sph]); tags += [f"s{k}" for k in range(n_sph)]
D = dirs.T.copy()

# Below ~150 Hz the cabinet is acoustically tiny (radiation is omnidirectional,
# 0 dB re monopole) and this Burton-Miller formulation converges very slowly,
# so the sweep starts at 150 Hz; the analysis holds the 150 Hz value below that.
freqs = np.round(np.geomspace(150, 3000, 22), 2)
out = dict(meta=meta, piston_area_m2=float(area), tags=tags, directions=dirs.tolist(), results=[])
t0 = time.time()
for f in freqs:
    res = solve(mesh, vel, float(f), D)
    far = np.array(res["far_real"]) + 1j * np.array(res["far_imag"])
    mono = 2 * np.pi * f * RHO / (4 * np.pi)
    out["results"].append(dict(frequency_hz=float(f), far_real=far.real.tolist(), far_imag=far.imag.tolist(),
                               rel_monopole_db=(20 * np.log10(np.abs(far) / mono)).tolist(),
                               residual=res["explicit_relative_residual"]))
    on = 20 * np.log10(abs(far[0]) / mono)
    print(f"{f:8.1f} Hz on-axis re free-field monopole {on:+6.2f} dB  ({time.time() - t0:.0f} s)", flush=True)
    json.dump(out, open(HERE / "bem_woofer_results.json", "w"))
print("done")
