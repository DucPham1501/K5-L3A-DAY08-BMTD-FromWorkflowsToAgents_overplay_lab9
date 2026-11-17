"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems: list[str] = []
    m = pr.get("manifest", {})
    for k, v in (pr.get("metrics") or {}).items():
        if isinstance(v, float) and not math.isfinite(v):
            problems.append(f"metric {k} is {v} (NaN/inf)")
    rows = pr.get("rows") or []
    keys = [(r.get("item_id"), r.get("seed")) for r in rows]
    want = m.get("items", 0) * len(m.get("seeds") or [])
    if len(rows) != want:
        problems.append(f"{len(rows)} rows, manifest says {m.get('items')} items x {len(m.get('seeds') or [])} seeds = {want}")
    dup = sorted({k for k in keys if keys.count(k) > 1}, key=str)
    if dup:
        problems.append(f"duplicate (item, seed) rows, e.g. {dup[0]}")
    bm = base.get("manifest", {})
    if (m.get("items"), sorted(m.get("seeds") or [])) != (bm.get("items"), sorted(bm.get("seeds") or [])):
        problems.append("manifest items/seeds differ from the baseline's")
    brows = {(r.get("item_id"), r.get("seed")) for r in base.get("rows") or []}
    if set(keys) != brows:
        problems.append(f"(item, seed) set differs from baseline: {len(set(keys) ^ brows)} cell(s) differ (cherry-picked or missing)")
    if pr.get("evaluator_failures"):
        problems.append(f"{len(pr['evaluator_failures'])} evaluator failure(s): {pr['evaluator_failures'][0]}")
    graded = [x for x in spec.get("metrics", []) if rows and x["id"] in rows[0]]
    for x in graded:
        missing = sum(1 for r in rows if r.get(x["id"]) is None)
        if missing:
            problems.append(f"{missing} row(s) with no value for graded metric {x['id']} (crashed grader)")
        vals = [r[x["id"]] for r in rows if r.get(x["id"]) is not None]
        reported = (pr.get("metrics") or {}).get(x["id"])
        if vals and isinstance(reported, (int, float)):
            actual = sum(vals) if x.get("kind") == "safety" else sum(vals) / len(vals)
            if abs(actual - reported) > 1e-3:
                problems.append(f"metric {x['id']} reports {reported} but its rows give {actual:.4f}")
    tags = lambda rep: {r.get("item_id"): sorted(r.get("slices") or []) for r in rep.get("rows") or []}
    tp, tb = tags(pr), tags(base)
    relabelled = sorted(i for i in tp if i in tb and tp[i] != tb[i])
    if relabelled:
        problems.append(f"slice tags differ from baseline for {', '.join(map(str, relabelled[:3]))}")
    if base_spec is not None and base_spec.get("eval_set_version") == spec.get("eval_set_version"):
        problems += _ratchet(spec.get("metrics", []), base_spec.get("metrics", []), "metric")
        problems += _ratchet(spec.get("slices", []) or [], base_spec.get("slices", []) or [], "slice",
                             key="name")
    return problems


def _ratchet(new: list[dict], old: list[dict], what: str, key: str = "id") -> list[str]:
    """Thresholds may only get stricter on the same eval-set version."""
    out: list[str] = []
    cur = {x[key]: x for x in new}
    for o in old:
        n = cur.get(o[key])
        if n is None:
            out.append(f"{what} {o[key]} was removed")
            continue
        if o.get("blocking") and not n.get("blocking"):
            out.append(f"{what} {o[key]} is no longer blocking")
        ot = o.get("threshold", o) if what == "metric" else o
        nt = n.get("threshold", n) if what == "metric" else n
        if "min" in ot and ("min" not in nt or nt["min"] < ot["min"]):
            out.append(f"{what} {o[key]} min lowered {ot['min']} -> {nt.get('min')}")
        if "max" in ot and ("max" not in nt or nt["max"] > ot["max"]):
            out.append(f"{what} {o[key]} max raised {ot['max']} -> {nt.get('max')}")
        if "max_increase" in ot and ("max_increase" not in nt or nt["max_increase"] > ot["max_increase"]):
            out.append(f"{what} {o[key]} max_increase raised")
        if ot.get("no_significant_drop") and not nt.get("no_significant_drop"):
            out.append(f"{what} {o[key]} dropped no_significant_drop")
    return out



def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for sl in spec.get("slices") or []:
        name, metric = sl["name"], sl["metric"]
        a, b = per_item(pr, metric, name), per_item(base, metric, name)
        sid = f"slice:{name}/{metric}"
        if not a:
            verdict, note, val = "MISSING", "no items in this slice", None
        else:
            val = sum(a.values()) / len(a)
            verdict, note = "ok", ""
            if "min" in sl and val < sl["min"]:
                verdict = "fail"
            keys = sorted(set(a) & set(b))
            if sl.get("no_significant_drop") and keys:
                d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                                   n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"
        bad = verdict in ("fail", "MISSING")
        if bad and sl.get("blocking"):
            blocked.append(sid)
        label = "ok" if not bad else ("BLOCK" if sl.get("blocking") else "warn")
        shown = "None" if val is None else f"{val:.4f}"
        lines.append(f"  {sid:<34} {shown:<8} n={len(a):<3} {note:<28} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
