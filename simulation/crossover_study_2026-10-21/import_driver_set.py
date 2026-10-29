#!/usr/bin/env python3
"""Turn a new REW driver-set capture (.mdat) into this study's input format.

Capture (one fixed mic position, 1 m on the woofer/tweeter midpoint axis,
common acoustic timing reference, nothing moved between sweeps):
woofer-only, tweeter-only and combined sweeps, ideally two of each.

    python3 import_driver_set.py NEW.mdat OUT_FOLDER \
        --roles W,W,T,T,C,C --chain chain.json

``--roles`` gives each record's role in file order (W woofer, T tweeter,
C combined).  ``chain.json`` describes the DSP active during the capture so
it can be divided out, e.g.
    {"woofer": {"xo": ["LR4", 3000], "trim_db": -4, "hp50_pair": true},
     "tweeter": {"xo": ["LR4", 3000], "trim_db": -10, "invert": false,
                 "delay_samples": 0, "peq": [[3500, 3.0, -2.0]]}}
Then run the study on it with:  PRIA_DRIVER_SET=OUT_FOLDER python3 <script>

Needs javaobj-py3 0.6.1 (data-only Java deserialisation; no REW code runs).
Uses the repository's existing REW reader and the same window recipe as
measurements/2026-09-30_crossover_corrected/analyze_corrected.py.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, shutil
import numpy as np
from common import MEAS, _half_tukey_window

spec = importlib.util.spec_from_file_location(
    "rew_reader", MEAS / "2026-09-29_first_bluetooth_baseline/analyze_rew.py")
rw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mdat")
    ap.add_argument("out")
    ap.add_argument("--roles", required=True)
    ap.add_argument("--chain", required=True)
    a = ap.parse_args()
    src, out = Path(a.mdat), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    roles = a.roles.split(",")
    with src.open("rb") as fh:
        objects = rw.javaobj.load(fh, use_numpy_arrays=True)
    recs = [rw.fields(o) for o in objects if hasattr(o, "classdesc") and o.classdesc.name == "roomeqwizard.MeasData"]
    if len(recs) != len(roles):
        raise SystemExit(f"{len(recs)} records in file but {len(roles)} roles given")
    meta = []
    for i, (m, role) in enumerate(zip(recs, roles), 1):
        ir = {k: rw.unbox(v) for k, v in rw.fields(m["irData"]).items()}
        wd = rw.fields(ir["windows"])
        f = m["startFreq"] + np.arange(m["dataLength"]) * m["freqStep"]
        spl, ph, imp = rw.array(m["splValues"]), rw.array(m["phaseValues"]), rw.array(ir["ir"])
        start, center, end = (wd[k] for k in ("preImpulseIndex", "winRefIndex", "postImpulseIndex"))
        sel = slice(round(f[0] / m["freqStep"]), round(f[0] / m["freqStep"]) + len(f))
        full = np.fft.rfft(imp * _half_tukey_window(len(imp), start, center, end))[sel]
        native = 10 ** (spl / 20) * np.exp(1j * np.deg2rad(ph))
        d = dict(frequency_hz=f, spl_db=spl, phase_deg=ph, impulse=imp, native=native)
        for ms in (3, 5, 8):
            short = np.fft.rfft(imp * _half_tukey_window(len(imp), center - 24, center, center + ms * 48))[sel]
            d[f"{ms}ms"] = native * short / full
        dist = rw.fields(m["distortionData"])
        d["noise_frequency_hz"], d["noise_spl_db"] = rw.array(dist["freqs"]), rw.array(dist["noiseFloorSPL"])
        np.savez_compressed(out / f"record_{i}.npz", **d)
        meta.append(dict(index=i, role=role, name=str(rw.scalar(m["shortDesc"])),
                         sample_rate=int(m["sampleRate"]), sweep_level_dbfs=float(rw.scalar(m["sweepLevel"])),
                         ir_snr_db=float(ir["signalToNoisedB"]), clock_ppm=float(ir["cumulativeClockRateAdjust"] * 1e6)))
    chain = json.loads(Path(a.chain).read_text())
    shutil.copy2(src, out / src.name)
    (out / "driver_set.json").write_text(json.dumps(dict(
        source=src.name, source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
        records=meta, capture_chain=chain), indent=1) + "\n")
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
