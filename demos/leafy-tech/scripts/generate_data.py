"""Generate the fictional Leafy Tech data set into data/*.json.

    python demos/leafy-tech/scripts/generate_data.py

Leafy Tech is a fictional IT reseller. Vendors use Microsoft's sample brand names (Fabrikam,
Wingtip, Litware, Proseware, Adatum). No real company, customer or price appears here.

The random seed is fixed, so every run produces the same data and the expected answers in
stage/prompts.txt stay true. The Willow Bend Health records are written by hand because the
demo's math depends on them.
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
from pathlib import Path

from bson import json_util

ROOT = Path(__file__).resolve().parent.parent
AS_OF = dt.datetime(2026, 11, 1)          # "last 12 months" is counted back from here
WAREHOUSES = ["Chicago", "Dallas", "Reno"]
QUOTE_NUMBER = "Q-2026-4471"
CUSTOMER = "Willow Bend Health"
AM = "Nina Patel"
ACCOUNT_MANAGERS = [AM, "Marcus Webb", "Elena Ruiz", "Tom Becker", "Priya Raman", "Jake Sorensen",
                    "Aisha Grant", "Luis Ortega"]

rng = random.Random(4471)


def stock(rows: list[tuple[str, int, int]]) -> list[dict]:
    return [{"warehouse": w, "on_hand": h, "reserved": r, "available": h - r} for w, h, r in rows]


def product(sku, name, vendor, category, list_price, cost, description, rows=(), status="active", **extra):
    return {"sku": sku, "name": name, "vendor": vendor, "category": category,
            "list_price": list_price, "cost": cost, "status": status,
            "description": description, "stock": stock(list(rows)), **extra}


# The six products the Willow Bend quote touches. Their prices drive the math.
QUOTE_PRODUCTS = [
    product("FB-MB14C", "Fabrikam MedBook 14 Clinical", "Fabrikam", "Laptops", 1800, 1350,
            "A 14-inch notebook made for hospital floors. The sealed antimicrobial chassis stands up to "
            "repeated cleaning with disinfectant wipes. Two hot-swappable batteries keep it running through "
            "long clinical rounds without a shutdown, and it is drop-tested to four feet. Locks onto mobile "
            "workstations.",
            [("Chicago", 150, 0), ("Dallas", 240, 100), ("Reno", 30, 0)]),
    product("WT-CD1", "Wingtip CartDock G1", "Wingtip", "Docks", 200, 140,
            "First-generation locking dock for mobile workstations. Fits the G1 cart mount only. "
            "Discontinued by the vendor; replaced by the CartDock G2.",
            [("Chicago", 0, 0), ("Dallas", 12, 0), ("Reno", 0, 0)], status="end_of_life", replaced_by="WT-CD2"),
    product("WT-CD2", "Wingtip CartDock G2", "Wingtip", "Docks", 220, 155,
            "Locking dock with charging and network pass-through. Fits the G2 cart mount.",
            [("Chicago", 420, 0), ("Dallas", 180, 0), ("Reno", 60, 0)]),
    product("FB-W3", "Fabrikam 3-Year Onsite Warranty", "Fabrikam", "Warranties", 120, 80,
            "Three years of next-business-day onsite repair for Fabrikam notebooks."),
    product("FB-W4", "Fabrikam 4-Year Onsite Warranty", "Fabrikam", "Warranties", 160, 105,
            "Four years of next-business-day onsite repair for Fabrikam notebooks."),
    product("LT-IMG", "Leafy Tech Imaging and Asset Tagging", "Leafy Tech", "Services", 45, 30,
            "Leafy Tech loads the customer's standard software image on each device and applies an asset "
            "tag before shipping. Priced per device."),
]

# Close neighbours of the MedBook, so the meaning search has real competition.
DECOYS = [
    product("FB-MB13C", "Fabrikam MedBook 13 Clinical", "Fabrikam", "Laptops", 1500, 1140,
            "The previous 13-inch clinical notebook. Wipeable keyboard and a single battery. "
            "Suited to shared desks on hospital wards.", [("Dallas", 25, 0)], status="end_of_life",
            replaced_by="FB-MB14C"),
    product("FB-FP13", "Fabrikam FieldPro 13 Rugged", "Fabrikam", "Laptops", 2400, 1820,
            "A fully rugged notebook for utility crews and field technicians. Sealed against rain, mud and "
            "dust, with a sunlight-readable screen and a carry handle for work outdoors.",
            [("Chicago", 60, 0), ("Reno", 45, 0)]),
    product("FB-MT11", "Fabrikam MedTab 11", "Fabrikam", "Tablets", 1100, 830,
            "An 11-inch tablet for bedside charting. Light enough to carry in one hand, with a barcode "
            "scanner for wristbands and medication labels.", [("Chicago", 90, 0), ("Dallas", 70, 0)]),
    product("FB-AIO22", "Fabrikam CareView 22 All-in-One", "Fabrikam", "Desktops", 1300, 960,
            "A 22-inch all-in-one computer for nurses' stations. Fanless design with an easy-clean "
            "glass front, mounted on a wall arm.", [("Dallas", 110, 0), ("Reno", 40, 0)]),
    product("FB-WH16", "Fabrikam WarehouseMate 16", "Fabrikam", "Laptops", 1650, 1230,
            "A forklift-mounted notebook for distribution centers. Vibration-resistant, with a glove-friendly "
            "touchscreen and a battery that works in cold storage.", [("Chicago", 35, 0)]),
    product("AD-CART1", "Adatum RoundsCart Mobile Workstation", "Adatum", "Peripherals", 950, 700,
            "A height-adjustable mobile workstation with a G2 mount, a large power pack and a "
            "scanner holder for clinical teams.", [("Chicago", 80, 0), ("Dallas", 55, 0)]),
]

# (category, vendor, series, base list price, sentence about who it is for)
LINES = [
    ("Laptops", "Fabrikam", "EliteLine", 1400, "Thin and light business notebook for executives who travel weekly."),
    ("Laptops", "Fabrikam", "OfficeBook", 950, "A dependable notebook for everyday office work and video calls."),
    ("Laptops", "Fabrikam", "EduBook", 480, "A low-cost classroom notebook with a spill-resistant keyboard for students."),
    ("Laptops", "Fabrikam", "CreatorPro", 2600, "A workstation notebook with a discrete graphics card for engineers and video editors."),
    ("Desktops", "Fabrikam", "TowerPro", 1050, "A business tower with room for expansion cards and extra drives."),
    ("Desktops", "Fabrikam", "MiniDesk", 720, "A palm-sized desktop that mounts behind a monitor to save desk space."),
    ("Monitors", "Wingtip", "ClearView", 340, "A flicker-free office monitor with a height-adjustable stand."),
    ("Monitors", "Wingtip", "UltraWide", 780, "A curved ultrawide display for traders and analysts who watch many windows."),
    ("Docks", "Wingtip", "DeskDock", 190, "A desktop docking station that powers a notebook and two monitors from one cable."),
    ("Peripherals", "Wingtip", "QuietKeys", 70, "A low-noise wireless keyboard and mouse set for open offices."),
    ("Peripherals", "Wingtip", "HuddleCam", 640, "A wide-angle conference room camera with a built-in speaker bar."),
    ("Networking", "Litware", "AirPoint", 420, "A ceiling-mounted Wi-Fi access point for offices and schools."),
    ("Networking", "Litware", "CoreSwitch", 2900, "A stackable network switch for wiring closets and branch offices."),
    ("Networking", "Litware", "EdgeGate", 1800, "A branch firewall and router that connects remote sites back to headquarters."),
    ("Servers", "Adatum", "RackServe", 6800, "A two-socket rack server for virtualization and databases."),
    ("Storage", "Adatum", "VaultArray", 14500, "An all-flash storage array with snapshots and replication for backups."),
    ("Security", "Proseware", "ShieldEndpoint", 58, "Endpoint protection software that stops ransomware on laptops and desktops. Priced per device per year."),
    ("Security", "Proseware", "ShieldMail", 34, "Email security that blocks phishing before it reaches an inbox. Priced per user per year."),
    ("Security", "Proseware", "ShieldID", 46, "Multi-factor sign-in and password protection for staff accounts. Priced per user per year."),
    ("Services", "Leafy Tech", "Install", 1200, "Onsite installation by a Leafy Tech engineer. Priced per day."),
]
SIZES = ["S", "M", "L", "X", "Plus", "Max", "Pro", "Air"]
GENS = [2, 3, 4, 5]


def catalog() -> list[dict]:
    items = QUOTE_PRODUCTS + DECOYS
    n = 100
    for category, vendor, series, base, sentence in LINES:
        for gen in GENS:
            for size in rng.sample(SIZES, 4):
                n += 1
                price = round(base * (0.8 + 0.12 * gen) * rng.uniform(0.92, 1.12))
                rows = [] if category in ("Services", "Security") else \
                    [(w, h, min(h, rng.choice([0, 0, 0, 5, 10]))) for w in WAREHOUSES if (h := rng.randint(0, 300))]
                items.append(product(f"{vendor[:2].upper()}-{n}", f"{vendor} {series} {gen} {size}", vendor, category,
                                     price, round(price * rng.uniform(0.72, 0.84)),
                                     f"{sentence} Generation {gen}, {size} configuration.", rows))
    return items


NAME_A = ["Cedar", "Harbor", "Juniper", "Silver", "Prairie", "Summit", "Birch", "Lakeshore", "Redwood", "Fox",
          "Ironwood", "Stone", "Meadow", "Copper", "Hollow", "Bluff", "Aspen", "Granite", "Clover", "Sable"]
NAME_B = ["Creek", "Point", "Valley", "Ridge", "Falls", "Crossing", "Park", "Grove", "Landing", "Heights"]
SUFFIX = {
    "Healthcare": ["Health", "Medical Center", "Family Clinics", "Regional Hospital"],
    "Education": ["School District", "Community College", "Academy"],
    "Government": ["County", "City Services", "Water Authority"],
    "Financial Services": ["Credit Union", "Savings Bank", "Advisors"],
    "Manufacturing": ["Fabrication", "Tool and Die", "Plastics"],
    "Retail": ["Outfitters", "Markets", "Home Supply"],
    "Legal": ["Law Group", "Legal Partners"],
}
STATES = ["IL", "TX", "CA", "OH", "MN", "WI", "NV", "CO", "GA", "PA", "AZ", "MI"]


def customers(products: list[dict]) -> list[dict]:
    pool = [p for p in products if p["category"] in ("Laptops", "Desktops", "Tablets")]
    seen, out = {CUSTOMER}, []
    while len(out) < 299:
        industry = rng.choice(list(SUFFIX))
        name = f"{rng.choice(NAME_A)} {rng.choice(NAME_B)} {rng.choice(SUFFIX[industry])}"
        if name in seen:
            continue
        seen.add(name)
        devices = []
        for _ in range(rng.randint(2, 5)):
            p = rng.choice(pool)
            purchased = dt.datetime(rng.randint(2022, 2025), rng.randint(1, 12), rng.randint(1, 28))
            term = rng.choice([3, 4])
            devices.append({"sku": p["sku"], "product": p["name"], "category": p["category"],
                            "qty": rng.randint(10, 180), "purchased": purchased,
                            "warranty_end": purchased.replace(year=purchased.year + term)})
        out.append({"customer_id": f"C-{1001 + len(out)}", "name": name, "industry": industry,
                    "state": rng.choice(STATES), "account_manager": rng.choice(ACCOUNT_MANAGERS),
                    "devices": devices, "buys_security": rng.random() < 0.6})
    out.append({"customer_id": "C-1400", "name": CUSTOMER, "industry": "Healthcare", "state": "IL",
                "account_manager": AM, "buys_security": True,
                "devices": [
                    {"sku": "FB-MB13C", "product": "Fabrikam MedBook 13 Clinical", "category": "Laptops", "qty": 640,
                     "purchased": dt.datetime(2023, 1, 15), "warranty_end": dt.datetime(2027, 1, 15)},
                    {"sku": "FB-AIO22", "product": "Fabrikam CareView 22 All-in-One", "category": "Desktops",
                     "qty": 120, "purchased": dt.datetime(2024, 6, 3), "warranty_end": dt.datetime(2028, 6, 3)},
                ]})
    return out


def orders(products: list[dict], custs: list[dict]) -> list[dict]:
    pool = [p for p in products if p["status"] == "active" and p["category"] != "Warranties"]
    out, n = [], 50000
    for c in custs:
        allowed = [p for p in pool if c["buys_security"] or p["category"] != "Security"]
        for _ in range(rng.randint(4, 16)):
            n += 1
            date = AS_OF - dt.timedelta(days=rng.randint(1, 720))
            discount = rng.choice([0, 3, 5, 8, 10])
            lines = []
            for p in rng.sample(allowed, rng.randint(1, 3)):
                qty = rng.randint(1, 8) if p["list_price"] > 3000 else rng.randint(5, 120)
                unit = round(p["list_price"] * (1 - discount / 100), 2)
                lines.append({"sku": p["sku"], "product": p["name"], "category": p["category"], "qty": qty,
                              "unit_price": unit, "extended": round(unit * qty, 2)})
            out.append({"order_number": f"SO-{n}", "customer_id": c["customer_id"], "customer": c["name"],
                        "account_manager": c["account_manager"], "order_date": date, "lines": lines,
                        "total": round(sum(x["extended"] for x in lines), 2),
                        "status": rng.choices(["delivered", "cancelled"], [19, 1])[0]})
    # Willow Bend is an active account, so it needs an order in the last 12 months.
    lines = [{"sku": "FB-MT11", "product": "Fabrikam MedTab 11", "category": "Tablets", "qty": 300,
              "unit_price": 990.0, "extended": 297000.0},
             {"sku": "AD-CART1", "product": "Adatum RoundsCart Mobile Workstation", "category": "Peripherals",
              "qty": 200, "unit_price": 855.0, "extended": 171000.0}]
    out.append({"order_number": "SO-49001", "customer_id": "C-1400", "customer": CUSTOMER, "account_manager": AM,
                "order_date": dt.datetime(2026, 3, 10), "lines": lines, "total": 468000.0, "status": "delivered"})
    return out


def add_spend(custs: list[dict], ords: list[dict]) -> None:
    categories = sorted({x["category"] for o in ords for x in o["lines"]})
    start = AS_OF - dt.timedelta(days=365)
    for c in custs:
        by_cat = dict.fromkeys(categories, 0.0)
        for o in ords:
            if o["customer_id"] == c["customer_id"] and o["order_date"] >= start and o["status"] == "delivered":
                for x in o["lines"]:
                    by_cat[x["category"]] += x["extended"]
        c["spend_by_category"] = {k: round(v) for k, v in by_cat.items()}
        c["spend_last_12_months"] = round(sum(by_cat.values()))
        del c["buys_security"]


def quote_line(n: int, p: dict, qty: int, discount: int) -> dict:
    unit = round(p["list_price"] * (1 - discount / 100), 2)
    return {"line": n, "sku": p["sku"], "product": p["name"], "qty": qty, "list_price": p["list_price"],
            "discount_pct": discount, "unit_price": unit, "extended": round(unit * qty, 2)}


def quotes(products: list[dict], custs: list[dict]) -> list[dict]:
    by_sku = {p["sku"]: p for p in products}
    lines = [quote_line(i, by_sku[s], 500, 14) for i, s in enumerate(["FB-MB14C", "WT-CD1", "FB-W3", "LT-IMG"], 1)]
    out = [{"quote_number": QUOTE_NUMBER, "customer_id": "C-1400", "customer": CUSTOMER, "account_manager": AM,
            "status": "draft", "created": dt.datetime(2026, 11, 2), "valid_until": dt.datetime(2026, 12, 2),
            "title": "Clinical laptop refresh", "deal_registration_id": None, "lines": lines,
            "total": round(sum(x["extended"] for x in lines), 2)}]
    pool = [p for p in products if p["status"] == "active" and p["category"] not in ("Warranties", "Services")]
    for i in range(60):
        c = rng.choice(custs[:-1])
        discount = rng.choice([0, 5, 8, 10])
        ls = [quote_line(j, p, rng.randint(5, 80), discount) for j, p in enumerate(rng.sample(pool, rng.randint(1, 4)), 1)]
        created = dt.datetime(2026, rng.randint(8, 10), rng.randint(1, 28))
        out.append({"quote_number": f"Q-2026-{4000 + i}", "customer_id": c["customer_id"], "customer": c["name"],
                    "account_manager": c["account_manager"], "status": rng.choice(["sent", "won", "lost"]),
                    "created": created, "valid_until": created + dt.timedelta(days=30), "title": "Hardware order",
                    "deal_registration_id": f"DR-{70000 + i}" if rng.random() < 0.5 else None, "lines": ls,
                    "total": round(sum(x["extended"] for x in ls), 2)})
    return out


def main() -> None:
    products = catalog()
    custs = customers(products)
    ords = orders(products, custs)
    add_spend(custs, ords)
    qts = quotes(products, custs)
    out = ROOT / "data"
    out.mkdir(exist_ok=True)
    for name, docs in (("products", products), ("customers", custs), ("orders", ords), ("quotes", qts)):
        (out / f"{name}.json").write_text(json_util.dumps(docs, indent=1))
        print(f"{name}: {len(docs)}")


if __name__ == "__main__":
    # No options: this only makes --help print the description instead of running.
    argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    main()
