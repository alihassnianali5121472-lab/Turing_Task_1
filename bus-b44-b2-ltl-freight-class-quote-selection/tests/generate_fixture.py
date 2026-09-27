#!/usr/bin/env python3
"""Fixture generator + reference solver for the LTL class-and-award task.

Build-time only: it is never copied into the image (the Dockerfile copies
environment/input/ alone). One command regenerates the disclosed inputs, the
golden deliverables and the expected values in tests/verifier.json:

    python3 tests/generate_fixture.py            # write everything
    python3 tests/generate_fixture.py --check    # rebuild in memory, assert invariants, diff

The solver reads nothing but the files it writes to environment/input/ (it
re-parses them from disk), so the key is derived from the disclosed set only.
`solve(..., wrong=...)` renders the declared wrong readings for the README's
difficulty-design section and the discrimination probes.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "environment" / "input"
GOLD = ROOT / "solution" / "files"
VERIFIER = ROOT / "tests" / "verifier.json"

TRAILER_HEIGHT_IN = 96

# --------------------------------------------------------------------------------------
# density scale (NMFC 13-sub scale, effective 2025-07-19)
# --------------------------------------------------------------------------------------
BANDS = [  # (min inclusive, max exclusive, class)
    ("50", None, "50"),
    ("35", "50", "55"),
    ("30", "35", "60"),
    ("22.5", "30", "65"),
    ("15", "22.5", "70"),
    ("12", "15", "85"),
    ("10", "12", "92.5"),
    ("8", "10", "100"),
    ("6", "8", "125"),
    ("4", "6", "175"),
    ("2", "4", "250"),
    ("1", "2", "300"),
    ("0", "1", "400"),
]

# --------------------------------------------------------------------------------------
# classification items (markdown table); basis DENSITY or a fixed class
# --------------------------------------------------------------------------------------
ITEMS = [
    ("24150", "Hardware, fasteners, fittings, bolts, nuts, screws, in boxes on pallets", "density"),
    ("48620", "Chemicals, industrial, NOI, liquid, in closed metal or plastic drums", "density"),
    ("61320", "Floor or wall tile, ceramic, in boxes or crates", "density"),
    ("79260", "Displays, store or window, retail, KD or SU, in boxes or crates", "density"),
    ("82240", "Furniture, upholstered, SU, in boxes or crates", "density"),
    ("87730", "Glassware, laboratory or scientific, in boxes", "100"),
    ("110550", "Shelving, steel, KD, flat, banded on skids", "density"),
    ("116030", "Botanicals, dried, loose or in bags, not compressed", "125"),
    ("133330", "Paper, printing or writing, in rolls", "density"),
    ("156610", "Foam articles, expanded polystyrene, shaped, packed", "150"),
    ("158850", "Lubricating oil or grease, in drums", "density"),
]

# --------------------------------------------------------------------------------------
# carriers
# --------------------------------------------------------------------------------------
CARRIERS = ["C-ARW", "C-BLT", "C-CRS", "C-DLT", "C-EXL"]
ROUTING_ORDER = ["C-ARW", "C-DLT", "C-EXL", "C-CRS", "C-BLT"]  # routing-guide preference

SERVICES = {  # liftgate_offered, liftgate_fee, appt_offered, appt_fee
    "C-ARW": ("YES", "95.00", "YES", "45.00"),
    "C-BLT": ("NO", "0.00", "YES", "60.00"),
    "C-CRS": ("YES", "75.00", "NO", "0.00"),
    "C-DLT": ("YES", "130.00", "YES", "55.00"),
    "C-EXL": ("YES", "85.00", "YES", "40.00"),
}

HOLIDAYS = {  # dates the carrier's terminals neither pick up nor deliver
    "C-ARW": ["2026-10-12", "2026-11-11", "2026-11-26"],
    "C-BLT": ["2026-11-26", "2026-11-27"],
    "C-CRS": ["2026-10-12", "2026-11-26"],
    "C-DLT": ["2026-11-26"],
    "C-EXL": ["2026-10-12", "2026-11-11", "2026-11-26"],
}

LANES = {  # carrier -> {zone: transit business days}
    "C-ARW": {"Z1": 2, "Z2": 3, "Z3": 3, "Z4": 4},
    "C-BLT": {"Z1": 1, "Z2": 2, "Z3": 2},
    "C-CRS": {"Z1": 3, "Z2": 4, "Z3": 4, "Z4": 5},
    "C-DLT": {"Z1": 1, "Z2": 2, "Z4": 3},
    "C-EXL": {"Z1": 2, "Z2": 2, "Z3": 3, "Z4": 3},
}

CLASS_MULT = {"50": "1.00", "55": "1.08", "60": "1.16", "65": "1.25", "70": "1.34",
              "85": "1.52", "92.5": "1.62", "100": "1.75", "125": "2.05", "150": "2.30",
              "175": "2.55", "250": "3.30", "300": "3.90", "400": "4.80"}
GROUPS = [0, 500, 1000, 2000]
GROUP_MULT = {0: "1.00", 500: "0.83", 1000: "0.69", 2000: "0.57"}

# sheet_id, carrier, effective, discount_pct, min_charge, class-50 L5C base, classes, group-mult override
SHEETS = [
    ("ARW-2609", "C-ARW", "2026-09-14", "68", "118.00", "61.40",
     ["50", "55", "60", "65", "70", "85", "92.5", "100", "125", "150", "175"], None),
    ("ARW-2610", "C-ARW", "2026-10-19", "72", "110.00", "59.80",
     ["50", "55", "60", "65", "70", "85", "92.5", "100", "125", "150", "175", "250"], None),
    ("BLT-2609", "C-BLT", "2026-09-14", "66", "125.00", "58.90",
     ["50", "55", "60", "65", "70", "85", "100", "125", "175", "250"], None),
    ("CRS-2609", "C-CRS", "2026-09-14", "71", "132.00", "60.20",
     ["55", "60", "65", "70", "85", "92.5", "100", "125", "150", "175", "250", "300"], None),
    ("CRS-2610", "C-CRS", "2026-10-13", "67", "132.00", "61.00",
     ["55", "60", "65", "70", "85", "92.5", "100", "125", "150", "175", "250", "300"], None),
    ("DLT-2608", "C-DLT", "2026-08-31", "70", "104.00", "60.10",
     ["50", "55", "60", "65", "70", "85", "92.5", "100", "125", "175"], None),
    ("DLT-2609", "C-DLT", "2026-09-14", "65", "118.00", "63.50",
     ["50", "55", "60", "65", "70", "85", "92.5", "100", "125", "150"], None),
    ("EXL-2609", "C-EXL", "2026-09-14", "69", "140.00", "62.70",
     ["60", "65", "70", "85", "92.5", "100", "125", "150", "175", "250", "300", "400"], None),
]

# --------------------------------------------------------------------------------------
# consignees and shipments
# --------------------------------------------------------------------------------------
CONSIGNEES = {  # zone, dock, appointment
    "CN-104": ("Z1", "YES", "NO"),
    "CN-117": ("Z2", "NO", "NO"),
    "CN-122": ("Z3", "YES", "YES"),
    "CN-138": ("Z1", "NO", "YES"),
    "CN-141": ("Z4", "YES", "NO"),
    "CN-156": ("Z2", "YES", "YES"),
    "CN-163": ("Z3", "NO", "NO"),
    "CN-170": ("Z4", "NO", "YES"),
    "CN-185": ("Z2", "YES", "NO"),
    "CN-192": ("Z1", "YES", "NO"),
}

# shipment_id, pickup, deliver_by, consignee, status, declared class
SHIPMENTS = []
# unit rows: shipment, revision, unit_id, item, shape, L, W, H, D, weight, note
UNITS = []


def ship(sid, pickup, deliver_by, cons, declared, status="BOOK"):
    SHIPMENTS.append((sid, pickup, deliver_by, cons, status, declared))


def unit(sid, rev, uid, item, shape, dims, pieces, wt, note=""):
    UNITS.append((sid, rev, uid, item, shape, dims, pieces, wt, note))


def build_cases():
    SHIPMENTS.clear()
    UNITS.clear()
    # --- filled in by the case table below --------------------------------------------
    from cases import CASES  # noqa: E402  (local module next to this file)
    for c in CASES:
        ship(*c["ship"])
        for u in c["units"]:
            unit(c["ship"][0], *u)


# --------------------------------------------------------------------------------------
# writing the disclosed inputs
# --------------------------------------------------------------------------------------
def rate_rows():
    rows = []
    for sheet_id, carrier, eff, disc, amc, base, classes, _ in SHEETS:
        for cls in classes:
            for g in GROUPS:
                r = (Decimal(base) * Decimal(CLASS_MULT[cls]) * Decimal(GROUP_MULT[g])).quantize(
                    Decimal("0.01"), ROUND_HALF_UP)
                rows.append((sheet_id, cls, g, f"{r:.2f}"))
    return rows


def csv_text(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def write_inputs(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    files["shipments.csv"] = csv_text(
        ["shipment_id", "pickup_date", "deliver_by", "consignee_id", "status", "bol_class"],
        [(s[0], s[1], s[2], s[3], s[4], s[5]) for s in SHIPMENTS])
    files["handling_units.csv"] = csv_text(
        ["shipment_id", "bol_revision", "unit_id", "nmfc_item", "unit_type", "dimensions_in",
         "pieces", "weight_lb", "handling_note"],
        [tuple("" if v is None else v for v in u) for u in UNITS])
    files["consignees.csv"] = csv_text(
        ["consignee_id", "delivery_zone", "dock_available", "appointment_required"],
        [(k, *v) for k, v in CONSIGNEES.items()])
    files["density_classes.csv"] = csv_text(
        ["min_density_pcf", "max_density_pcf", "freight_class"],
        [(lo, hi or "", cls) for lo, hi, cls in BANDS])
    files["rate_sheets.csv"] = csv_text(
        ["sheet_id", "carrier_id", "effective_date", "discount_pct", "absolute_min_charge_usd"],
        [(s[0], s[1], s[2], s[3], s[4]) for s in SHEETS])
    files["carrier_rates.csv"] = csv_text(
        ["sheet_id", "freight_class", "weight_group_min_lb", "rate_per_cwt"], rate_rows())
    files["carrier_lanes.csv"] = csv_text(
        ["carrier_id", "delivery_zone", "transit_days"],
        [(c, z, t) for c in CARRIERS for z, t in LANES[c].items()])
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    (out / "classification_items.md").write_text(items_md(), encoding="utf-8")
    (out / "carrier_profiles.md").write_text(profiles_md(), encoding="utf-8")


def items_md():
    lines = ["# Classification items", "",
             "The items our shippers bill under. Where the basis says *density scale*, the class",
             "comes off `density_classes.csv`; otherwise the item carries the class shown.", "",
             "| Item | Description | Basis |", "|---|---|---|"]
    for item, desc, basis in ITEMS:
        b = "density scale" if basis == "density" else f"class {basis}"
        lines.append(f"| {item} | {desc} | {b} |")
    return "\n".join(lines) + "\n"


def profiles_md():
    lines = ["# Carrier profiles", "",
             "Accessorial service each carrier offers on our account, and the flat fee it bills",
             "per shipment. A fee of 0.00 against a service that is not offered means nothing.", "",
             "| Carrier | Liftgate offered | Liftgate fee (USD) | Appointment offered | Appointment fee (USD) |",
             "|---|---|---|---|---|"]
    for c in CARRIERS:
        lo, lf, ao, af = SERVICES[c]
        lines.append(f"| {c} | {lo} | {lf} | {ao} | {af} |")
    lines += ["", "## Terminal holidays", "",
              "Days the carrier's terminals are closed: no pickups and no deliveries.", "",
              "| Carrier | Closed |", "|---|---|"]
    for c in CARRIERS:
        lines.append(f"| {c} | {', '.join(HOLIDAYS[c])} |")
    lines += ["", "## Routing-guide order", "",
              "Our routing guide ranks the carriers, most preferred first: " +
              ", ".join(ROUTING_ORDER) + "."]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------
# reference solver — reads the disclosed inputs back from disk
# --------------------------------------------------------------------------------------
WRONG_READINGS = {
    "raw_inches": "dimensions used as measured, fractions not rounded up",
    "drum_volume": "a drum cubed as a cylinder (pi r^2 h) instead of its overall box",
    "stack_keyword": "only notes containing the word 'stack' treated as no-freight-on-top",
    "ignore_nostack": "no-freight-on-top units cubed at their own height",
    "unit_density": "each unit classed on its own density; the shipment takes the highest class",
    "all_revisions": "every revision's units counted instead of the latest revision only",
    "dup_units": "a repeated unit row counted twice",
    "declared_class": "the class on the bill of lading used as the class",
    "latest_sheet": "each carrier's newest rate sheet used regardless of pickup date",
    "no_deficit": "no rating at a heavier weight group's minimum",
    "min_before_discount": "minimum charge compared to the undiscounted charge",
    "calendar_days": "transit counted in calendar days",
    "no_holidays": "carrier holidays ignored",
    "upper_bound_in": "a density on a band bound takes the lighter band",
    "keep_cancelled": "cancelled shipments quoted",
    "tie_routing": "equal totals broken by routing-guide order before delivery date",
    "no_pieces": "a line's cube taken for one piece although it covers several",
    "carton_dims": "cartons on a larger pallet cubed on the carton dimensions alone",
    "pallet_replaces": "the pallet or skid footprint used in place of the goods' own where the goods are larger",
    "sheet_strict": "a sheet effective on the pickup date treated as not yet in force",
}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def d2(x: Fraction) -> Decimal:
    """Round an exact value half-up to cents."""
    return (Decimal(x.numerator) / Decimal(x.denominator)).quantize(Decimal("0.01"), ROUND_HALF_UP)


def parse_md_table(text, header_first):
    rows, on = [], False
    for line in text.splitlines():
        if line.startswith("| " + header_first):
            on = True
            hdr = [c.strip() for c in line.strip("|").split("|")]
            continue
        if on:
            if not line.startswith("|"):
                break
            if set(line.replace("|", "").strip()) <= set("-: "):
                continue
            rows.append(dict(zip(hdr, [c.strip() for c in line.strip("|").split("|")])))
    return rows


NOSTACK_PHRASES = ("do not stack", "no stacking", "top load only", "nothing on top",
                   "no freight on top")


def is_nostack(note: str, wrong) -> bool:
    n = note.lower()
    if "ignore_nostack" in wrong:
        return False
    if "stack_keyword" in wrong:
        return "stack" in n and "max" not in n
    return any(p in n for p in NOSTACK_PHRASES)


def ceil_in(x: Fraction) -> int:
    return -((-x.numerator) // x.denominator)


def overall_dims(u, wrong):
    """Overall (L, W, H) of one piece in inches, before rounding up; drums as (D, D, H)."""
    import re
    txt = u["dimensions_in"].lower()
    m = re.fullmatch(r"\s*([\d.]+)\s*dia\s*x\s*([\d.]+)\s*h\s*", txt)
    if m:
        d, h = Fraction(m.group(1)), Fraction(m.group(2))
        return ("drum", d, d, h)
    l, w, h = (Fraction(x.strip()) for x in txt.split("x"))
    note = u["handling_note"].lower()
    m = re.search(r"on a (\d+) x (\d+) (?:pallet|skid) with (\d+) in deck", note)
    if m and "carton_dims" not in wrong:
        pl, pw, deck = (Fraction(m.group(k)) for k in (1, 2, 3))
        if "pallet_replaces" in wrong:
            l, w, h = pl, pw, h + deck
        else:
            l, w, h = max(l, pl), max(w, pw), h + deck
    return ("box", l, w, h)


def unit_cube_in3(u, wrong, per_piece=False) -> Fraction:
    """Cubic inches of one handling-unit line as the carrier measures it."""
    kind, l, w, h = overall_dims(u, wrong)
    if "raw_inches" not in wrong:
        l, w, h = (Fraction(ceil_in(x)) for x in (l, w, h))
    if is_nostack(u["handling_note"], wrong):
        h = Fraction(TRAILER_HEIGHT_IN)
    if kind == "drum" and "drum_volume" in wrong:
        import math
        cube = Fraction(math.pi) / 4 * l * l * h
    else:
        cube = l * w * h
    n = 1 if (per_piece or "no_pieces" in wrong) else int(u["pieces"])
    return cube * n


def band_class(density: Decimal, bands, wrong) -> str:
    for b in bands:
        lo = Decimal(b["min_density_pcf"])
        hi = Decimal(b["max_density_pcf"]) if b["max_density_pcf"] else None
        if "upper_bound_in" in wrong:
            if lo < density and (hi is None or density <= hi):
                return b["freight_class"]
            if lo == 0 and density == 0:
                return b["freight_class"]
        else:
            if lo <= density and (hi is None or density < hi):
                return b["freight_class"]
    raise ValueError(density)


def next_bday(day, closed):
    day += dt.timedelta(days=1)
    while day.weekday() >= 5 or day in closed:
        day += dt.timedelta(days=1)
    return day


def solve(inp: Path, wrong=frozenset()):
    wrong = frozenset(wrong)
    ships = read_csv(inp / "shipments.csv")
    units = read_csv(inp / "handling_units.csv")
    cons = {r["consignee_id"]: r for r in read_csv(inp / "consignees.csv")}
    bands = read_csv(inp / "density_classes.csv")
    sheets = read_csv(inp / "rate_sheets.csv")
    rates = read_csv(inp / "carrier_rates.csv")
    lanes = read_csv(inp / "carrier_lanes.csv")
    items = {r["Item"]: r["Basis"] for r in parse_md_table((inp / "classification_items.md").read_text(), "Item")}
    prof_text = (inp / "carrier_profiles.md").read_text()
    services = {r["Carrier"]: r for r in parse_md_table(prof_text, "Carrier | Liftgate")}
    closed = {r["Carrier"]: {dt.date.fromisoformat(x.strip()) for x in r["Closed"].split(",") if x.strip()}
              for r in parse_md_table(prof_text, "Carrier | Closed")}
    order_line = [l for l in prof_text.splitlines() if l.startswith("Our routing guide")][0]
    routing = [c.strip(" .") for c in order_line.split(":", 1)[1].split(",")]

    rate_tab = {}
    for r in rates:
        rate_tab.setdefault(r["sheet_id"], {}).setdefault(r["freight_class"], {})[int(r["weight_group_min_lb"])] = Fraction(r["rate_per_cwt"])
    lane_tab = {(r["carrier_id"], r["delivery_zone"]): int(r["transit_days"]) for r in lanes}
    carriers = sorted({s["carrier_id"] for s in sheets})

    by_ship = {}
    for u in units:
        by_ship.setdefault(u["shipment_id"], []).append(u)

    out_rows, detail = [], {}
    for s in ships:
        sid = s["shipment_id"]
        if s["status"] != "BOOK" and "keep_cancelled" not in wrong:
            continue
        us = by_ship[sid]
        if "all_revisions" not in wrong:
            top = max(int(u["bol_revision"]) for u in us)
            us = [u for u in us if int(u["bol_revision"]) == top]
        if "dup_units" not in wrong:
            seen, dd = set(), []
            for u in us:
                key = (u["bol_revision"], u["unit_id"])
                if key in seen:
                    continue
                seen.add(key)
                dd.append(u)
            us = dd
        weight = sum(Fraction(u["weight_lb"]) for u in us)
        cube_in3 = sum(unit_cube_in3(u, wrong) for u in us)
        density = d2(weight * 1728 / cube_in3)
        item_set = {u["nmfc_item"] for u in us}
        assert len(item_set) == 1, sid
        basis = items[item_set.pop()]
        if "declared_class" in wrong:
            fclass = s["bol_class"]
        elif basis.startswith("class "):
            fclass = basis.split()[1]
        elif "unit_density" in wrong:
            cls = []
            for u in us:
                dn = d2(Fraction(u["weight_lb"]) * 1728 / unit_cube_in3(u, wrong))
                cls.append(band_class(dn, bands, wrong))
            fclass = max(cls, key=lambda c: float(c))
        else:
            fclass = band_class(density, bands, wrong)
        pickup = dt.date.fromisoformat(s["pickup_date"])
        deliver_by = dt.date.fromisoformat(s["deliver_by"])
        c = cons[s["consignee_id"]]
        need_lift = c["dock_available"] == "NO"
        need_appt = c["appointment_required"] == "YES"
        quotes = []
        for car in carriers:
            my = [x for x in sheets if x["carrier_id"] == car]
            if "latest_sheet" in wrong:
                cand = my
            else:
                cand = [x for x in my if dt.date.fromisoformat(x["effective_date"]) < pickup
                        or ("sheet_strict" not in wrong and dt.date.fromisoformat(x["effective_date"]) == pickup)]
            if not cand:
                continue
            sh = max(cand, key=lambda x: x["effective_date"])
            tab = rate_tab[sh["sheet_id"]].get(fclass)
            if tab is None:
                continue
            zone = c["delivery_zone"]
            if (car, zone) not in lane_tab:
                continue
            transit = lane_tab[(car, zone)]
            cl = set() if "no_holidays" in wrong else closed[car]
            if pickup.weekday() >= 5 or pickup in cl:
                continue
            if "calendar_days" in wrong:
                deliv = pickup + dt.timedelta(days=transit)
            else:
                deliv = pickup
                for _ in range(transit):
                    deliv = next_bday(deliv, cl)
            if deliv > deliver_by:
                continue
            sv = services[car]
            if need_lift and sv["Liftgate offered"] != "YES":
                continue
            if need_appt and sv["Appointment offered"] != "YES":
                continue
            groups = sorted(tab)
            own = max(g for g in groups if g <= weight)
            charge = tab[own] * weight / 100
            if "no_deficit" not in wrong:
                for g in groups:
                    if g > own:
                        charge = min(charge, tab[g] * g / 100)
            disc = Fraction(sh["discount_pct"]) / 100
            amc = Fraction(sh["absolute_min_charge_usd"])
            if "min_before_discount" in wrong:
                lh = d2(max(charge, amc) * (1 - disc))
            else:
                lh = max(d2(charge * (1 - disc)), Decimal(sh["absolute_min_charge_usd"]))
            acc = Decimal("0")
            if need_lift:
                acc += Decimal(sv["Liftgate fee (USD)"])
            if need_appt:
                acc += Decimal(sv["Appointment fee (USD)"])
            quotes.append(dict(carrier=car, deliv=deliv, lh=lh, acc=acc, tot=lh + acc,
                               sheet=sh["sheet_id"], raw=charge * (1 - disc)))
        if quotes:
            if "tie_routing" in wrong:
                key = lambda q: (q["tot"], routing.index(q["carrier"]), q["deliv"])
            else:
                key = lambda q: (q["tot"], q["deliv"], routing.index(q["carrier"]))
            best = min(quotes, key=key)
            row = [sid, density, fclass, best["carrier"], best["lh"], best["acc"], best["tot"]]
        else:
            best = None
            row = [sid, density, fclass, "NONE", Decimal("0"), Decimal("0"), Decimal("0")]
        out_rows.append(row)
        detail[sid] = dict(weight=weight, cube=cube_in3 / 1728, density=density, fclass=fclass,
                           quotes=quotes, best=best, exact_density=weight * 1728 / cube_in3)
    awarded = [r for r in out_rows if r[3] != "NONE"]
    results = {
        "awarded_shipment_count": len(awarded),
        "linehaul_total_usd": float(sum(r[4] for r in awarded)),
        "accessorial_total_usd": float(sum(r[5] for r in awarded)),
        "quote_total_usd": float(sum(r[6] for r in awarded)),
    }
    return out_rows, results, detail


def diag(inp):
    rows, res, det = solve(inp)
    for r in rows:
        d = det[r[0]]
        qs = " ".join(f"{q['carrier'][2:]}:{q['tot']}@{q['deliv'].strftime('%d')}" for q in sorted(d['quotes'], key=lambda q: q['tot']))
        print(f"{r[0]} w={float(d['weight']):7.1f} dens={float(d['exact_density']):8.4f} cls={r[2]:>5} -> {r[3]:6} {r[6]:>8} | {qs}")
    print(res)
    base = {r[0]: r for r in rows}
    for w in WRONG_READINGS:
        wr, wres, _ = solve(inp, {w})
        diffs = [x[0] for x in wr if x[0] not in base or [str(v) for v in base[x[0]]] != [str(v) for v in x]]
        missing = [k for k in base if k not in {x[0] for x in wr}]
        print(f"  {w:20} changes {len(diffs)+len(missing)} rows: {diffs+missing}")


def invariants(inp):
    """Fairness invariants; any violation raises."""
    rows, res, det = solve(inp)
    bounds = sorted({Fraction(b[0]) for b in BANDS} | {Fraction(b[1]) for b in BANDS if b[1]})
    errs = []
    for sid, d in det.items():
        x = d["exact_density"]
        for b in bounds:
            if x != b and abs(x - b) < Fraction(2, 100):
                errs.append(f"{sid}: density {float(x):.4f} near bound {b}")
        if (x * 1000) % 10 == 5 and (x * 1000).denominator == 1:
            errs.append(f"{sid}: density half-cent")
        for q in d["quotes"]:
            v = q["raw"] * 100
            if v.denominator == 2:
                errs.append(f"{sid}/{q['carrier']}: discounted charge on a half cent")
        tots = sorted(d["quotes"], key=lambda q: q["tot"])
        for a, b in zip(tots, tots[1:]):
            gap = b["tot"] - a["tot"]
            if Decimal("0") < gap < Decimal("0.50"):
                errs.append(f"{sid}: near-tie {a['carrier']} {a['tot']} vs {b['carrier']} {b['tot']}")
        if len(tots) > 1 and tots[0]["tot"] == tots[1]["tot"]:
            if tots[0]["deliv"] == tots[1]["deliv"]:
                errs.append(f"{sid}: tie on total and delivery")
    seen = {}
    for s in SHEETS:
        k = (s[1], s[2])
        if k in seen:
            errs.append(f"duplicate effective date {k}")
        seen[k] = 1
    for u in UNITS:
        pass
    if errs:
        raise SystemExit("INVARIANT FAILURES:\n  " + "\n  ".join(errs))
    print("invariants ok")


def fmt_num(v):
    """Canonical numeral for the verifier: no trailing zeros."""
    d = Decimal(str(v))
    t = format(d.normalize(), "f")
    return t


def write_gold(inp: Path, out: Path):
    import openpyxl
    rows, res, _ = solve(inp)
    out.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Quotes"
    ws.append(["shipment_id", "density_pcf", "freight_class", "carrier_id", "linehaul_usd",
               "accessorial_usd", "total_cost_usd"])
    for r in rows:
        ws.append([r[0], float(r[1]), float(r[2]), r[3], float(r[4]), float(r[5]), float(r[6])])
    wb.save(out / "quote_selection.xlsx")
    (out / "results.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    return rows, res


SHEET_WHY = ("Entailed by submission_format.md: a worksheet named `Quotes` with the header "
             "`shipment_id, density_pcf, freight_class, carrier_id, linehaul_usd, accessorial_usd, "
             "total_cost_usd` in that order, one row for every shipment being quoted and no others, in "
             "the order shipments.csv lists them; and by quoting_rules.md sections 1-6, which fix each "
             "shipment's density, class, awarded carrier (or NONE) and the three money columns.")


def write_verifier(rows, res, path: Path):
    cols = ["shipment_id", "density_pcf", "freight_class", "carrier_id", "linehaul_usd",
            "accessorial_usd", "total_cost_usd"]
    exp_rows = {}
    for r in rows:
        exp_rows[r[0]] = {"density_pcf": fmt_num(r[1]), "freight_class": fmt_num(r[2]),
                          "carrier_id": r[3], "linehaul_usd": fmt_num(r[4]),
                          "accessorial_usd": fmt_num(r[5]), "total_cost_usd": fmt_num(r[6])}
    spec = {
        "task_id": "bus-b44_b2-ltl-freight-class-quote-selection",
        "verifiers": [
            {"name": "quote_sheet_rows",
             "metadata": {"tag": "core",
                          "how_justification": (
                              "Reads quote_selection.xlsx sheet 'Quotes' with xlsx.read_rows and applies "
                              "table_equals keyed on shipment_id: every graded cell of every quoted shipment "
                              "(numbers compared numerically within 0.006, text case- and whitespace-"
                              "insensitive), the row population locked to the quoted shipments as a multiset "
                              "(a missing, extra or duplicated row fails), the delivered order equal to "
                              "shipments.csv order, and the column set closed to the stated header."),
                          "why_justification": SHEET_WHY},
             "source": {"type": "file", "file": {"type": "xlsx", "command": "read_rows",
                                                 "arguments": {"path": "quote_selection.xlsx", "sheet": "Quotes"}}},
             "assertion": {"type": "deterministic",
                           "expected": {"id_column": "shipment_id", "rows": exp_rows,
                                        "row_set": [r[0] for r in rows], "row_set_ordered": True,
                                        "columns": cols,
                                        "cell_types": {"carrier_id": "text"},
                                        "numeric_tolerance": 0.006},
                           "deterministic": {"path": "$.rows", "comparison": "table_equals"}}},
            {"name": "quote_sheet_single_table",
             "metadata": {"tag": "core",
                          "how_justification": (
                              "Reads quote_selection.xlsx sheet 'Quotes' with xlsx.read_rows and requires "
                              "rows_after_table == 0: no second table-shaped block (two or more populated "
                              "cells in the table's columns) under the quote table."),
                          "why_justification": ("Entailed by submission_format.md: one row for every shipment "
                                                "being quoted 'and nothing else on the sheet under the table'. "
                                                "Without it a second, alternative table below the first could "
                                                "hedge the award.")},
             "source": {"type": "file", "file": {"type": "xlsx", "command": "read_rows",
                                                 "arguments": {"path": "quote_selection.xlsx", "sheet": "Quotes"}}},
             "assertion": {"type": "deterministic", "expected": 0,
                           "deterministic": {"path": "$.rows_after_table", "comparison": "equals"}}},
            {"name": "results_figures",
             "metadata": {"tag": "core",
                          "how_justification": (
                              "Reads results.json with json.read_file and applies object_equals over the four "
                              "keys with the key set closed: the count exactly, the three dollar totals within "
                              "0.01."),
                          "why_justification": ("Entailed by submission_format.md (a JSON object with exactly "
                                                "these four numeric keys) and quoting_rules.md section 7, which "
                                                "defines the count of awarded shipments and the three totals "
                                                "over the awarded shipments.")},
             "source": {"type": "file", "file": {"type": "json", "command": "read_file",
                                                 "arguments": {"path": "results.json"}}},
             "assertion": {"type": "deterministic",
                           "expected": {"keys": {
                               "awarded_shipment_count": {"value": res["awarded_shipment_count"], "tolerance": None},
                               "linehaul_total_usd": {"value": res["linehaul_total_usd"], "tolerance": 0.01},
                               "accessorial_total_usd": {"value": res["accessorial_total_usd"], "tolerance": 0.01},
                               "quote_total_usd": {"value": res["quote_total_usd"], "tolerance": 0.01}},
                               "closed": True},
                           "deterministic": {"path": "$", "comparison": "object_equals"}}},
        ],
    }
    path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")


GENERATED = ["shipments.csv", "handling_units.csv", "consignees.csv", "density_classes.csv",
             "rate_sheets.csv", "carrier_rates.csv", "carrier_lanes.csv",
             "classification_items.md", "carrier_profiles.md"]


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    build_cases()
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    write_inputs(tmp)
    invariants(tmp)
    if "--diag" in sys.argv:
        diag(tmp)
    elif "--check" in sys.argv:
        bad = [n for n in GENERATED if (tmp / n).read_bytes() != (INPUT / n).read_bytes()]
        print("inputs match" if not bad else f"inputs DIFFER: {bad}")
    else:
        for old in ("carrier_services.csv", "commodity_exceptions.csv"):
            (INPUT / old).unlink(missing_ok=True)
        write_inputs(INPUT)
        rows, res = write_gold(INPUT, GOLD)
        write_verifier(rows, res, VERIFIER)
        print("wrote inputs, gold and verifier.json", res)
