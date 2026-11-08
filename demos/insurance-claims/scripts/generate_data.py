"""Generate the Contoso Mutual demo dataset: claims + policies.

Deterministic (fixed seed), so the expected answers in DEMO_SCRIPT.md stay true
every time you regenerate. Writes MongoDB Extended JSON to data/.

From the repo root:
    .venv/bin/python demos/insurance-claims/scripts/generate_data.py

All people, companies, addresses and policies are fictional.
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
from pathlib import Path

from bson import json_util

if __name__ == "__main__":
    # Parse before the module-level generation below runs, so --help prints and exits
    # without building anything. There are no options.
    argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data"
SEED = 20261102
AS_OF = dt.datetime(2026, 11, 2)

rng = random.Random(SEED)

# --------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------

CITIES = {
    # city: (county, zips, dwelling value range, in hail footprint)
    "Plano": ("Collin", ["75093", "75024", "75025"], (380_000, 820_000), True),
    "Frisco": ("Collin", ["75034", "75035"], (420_000, 950_000), True),
    "McKinney": ("Collin", ["75070", "75071"], (340_000, 700_000), True),
    "Allen": ("Collin", ["75002", "75013"], (350_000, 680_000), True),
    "Dallas": ("Dallas", ["75214", "75218", "75230"], (300_000, 900_000), True),
    "Garland": ("Dallas", ["75040", "75044"], (240_000, 420_000), True),
    "Irving": ("Dallas", ["75038", "75063"], (280_000, 560_000), True),
    "Fort Worth": ("Tarrant", ["76109", "76132"], (260_000, 640_000), False),
    "Arlington": ("Tarrant", ["76016", "76017"], (250_000, 480_000), False),
    "Denton": ("Denton", ["76205", "76210"], (260_000, 520_000), False),
    "Houston": ("Harris", ["77005", "77019"], (350_000, 900_000), False),
    "Katy": ("Fort Bend", ["77494"], (300_000, 600_000), False),
    "Austin": ("Travis", ["78704", "78731"], (420_000, 950_000), False),
    "Round Rock": ("Williamson", ["78664"], (300_000, 520_000), False),
}
HAIL_CITIES = [c for c, v in CITIES.items() if v[3]]

STREETS = [
    "Briar Hollow Ln", "Pecan Grove Dr", "Willow Bend Ct", "Cedar Ridge Rd", "Live Oak St",
    "Bluebonnet Trl", "Meadowbrook Dr", "Stonegate Blvd", "Prairie View Ln", "Sycamore Ct",
    "Lakeshore Dr", "Hidden Creek Way", "Magnolia Pl", "Riverbend Dr", "Whispering Pines Ln",
    "Shady Elm Ct", "Copper Canyon Rd", "Spring Valley Rd", "Timberline Dr", "Mockingbird Ln",
]
FIRST = [
    "James", "Olivia", "Michael", "Sophia", "David", "Emma", "Robert", "Ava", "William", "Mia",
    "Carlos", "Isabella", "Anthony", "Hannah", "Kevin", "Grace", "Brian", "Lauren", "Eric", "Nina",
    "Tyler", "Megan", "Andre", "Leah", "Victor", "Chloe", "Raj", "Aisha", "Hector", "Julia",
    "Owen", "Tara", "Marcus", "Fatima", "Ben", "Rachel", "Diego", "Wendy", "Samir", "Holly",
]
LAST = [
    "Nguyen", "Patel", "Johnson", "Garcia", "Miller", "Davis", "Martinez", "Wilson", "Anderson",
    "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Harris", "Clark", "Lewis", "Walker",
    "Hall", "Young", "King", "Wright", "Lopez", "Hill", "Scott", "Green", "Adams", "Baker",
    "Campbell", "Mitchell", "Roberts", "Carter", "Phillips", "Evans", "Turner", "Torres", "Parker",
    "Collins", "Edwards", "Stewart", "Morris", "Murphy", "Cook", "Rogers", "Morgan", "Cooper",
]

ADJUSTERS = {
    # name: (role, home counties)
    "Maya Chen": ("Desk Adjuster", ["Collin"]),
    "Jordan Reyes": ("Field Adjuster", ["Collin", "Denton"]),
    "Priya Nair": ("Desk Adjuster", ["Dallas"]),
    "Marcus Bell": ("Senior Adjuster", ["Dallas", "Tarrant"]),
    "Elena Kowalski": ("Desk Adjuster", ["Tarrant", "Denton"]),
    "Sam Whitaker": ("Senior Adjuster", ["Harris", "Fort Bend"]),
    "Luis Ortega": ("Desk Adjuster", ["Travis", "Williamson"]),
}

WATER_CONTRACTORS = [
    "Lone Star Restoration", "Bluebonnet Water Mitigation", "Trinity Dry-Out Co.",
    "Prairie Home Restoration", "Metroplex Mitigation Services",
]
ROOF_CONTRACTORS = [
    "Red River Roofing", "Cedar Creek Roofing & Exteriors", "North Texas Roof Works",
    "Pecan Valley Construction",
]
FIRE_CONTRACTORS = ["Ashford Fire & Smoke Restoration", "Pecan Valley Construction"]
BAD_ACTOR = "LeafyDry Restoration LLC"

ENDORSEMENTS = {
    "HO-WB-10": ("Water Backup and Sump Discharge or Overflow", 10_000),
    "HO-WB-25": ("Water Backup and Sump Discharge or Overflow", 25_000),
    "HO-SPP": ("Scheduled Personal Property", 15_000),
    "HO-ID": ("Identity Fraud Expense", 25_000),
    "HO-OL": ("Ordinance or Law (10% of Coverage A)", None),
    "HO-RCC": ("Replacement Cost on Personal Property", None),
}

CAT_CODE = "CAT-2026-17"
CAT_NAME = "North Texas Hailstorm, Oct 14-15 2026"

ROOMS = ["living room", "family room", "kitchen", "dining room", "den", "primary bedroom",
         "guest bedroom", "home office", "hallway", "breakfast nook"]
SIDES = ["north", "south", "east", "west", "back", "front"]

# Loss descriptions, written the way a policyholder phrases a first notice of loss.
DESCRIPTIONS = {
    "Hail": [
        "Hail the size of golf balls hit our neighborhood during the storm. The roof has missing granules and several cracked shingles, and the gutters on the {side} side are dented. A roofer came by and said the whole roof should be replaced.",
        "Large hail shattered two skylights and the {room} window. Rain got in before we could tarp it and the carpet is soaked.",
        "After the hailstorm we noticed dents all over the garage door and the metal roof vents. The {side} fence boards are split too.",
        "The storm broke the {room} window and dented the siding on the {side} side. Water came in around the window frame during the heavy rain that followed.",
        "Hail punched holes in the patio cover and stripped paint off the {side} side of the house. A neighbor's roofer says our shingles are bruised.",
        "During the storm water started dripping from the {room} ceiling. The roofer found hail damage and cracked flashing around the chimney that let the rain in.",
        "Our roof is about twelve years old and the hail left soft spots all over it. Now there is a brown water stain on the {room} ceiling after the rain.",
        "Hail damaged the AC condenser fins and broke the {room} skylight. We have a tarp on the roof for now.",
        "About fifteen minutes of heavy hail. Shingles are cracked, the ridge cap is damaged and two solar panels on the {side} side have cracked glass.",
        "Hail dented our gutters and downspouts and knocked holes in the vinyl siding on the {side} wall. The roof inspector counted more than ten hits per square.",
    ],
    "Wind": [
        "High winds tore off a section of shingles over the {room} and a large limb from the neighbor's oak fell on the {side} side of the roof.",
        "A straight-line wind gust blew down about sixty feet of our wood fence and threw the patio umbrella through the {room} window.",
        "The wind lifted the flashing on the {side} side and peeled back part of the roof. Rain came in at the top of the {room} wall.",
        "A tree in the front yard was uprooted during the storm and landed on the carport.",
        "Wind ripped the awning off the back of the house and the metal frame cracked the {room} window.",
        "Strong winds blew several shingles off and part of the soffit is hanging down over the driveway.",
    ],
    "Water - Plumbing": [
        "The water heater in the garage split open while we were home on Saturday. Water spread into the laundry room and the {room} and soaked the baseboards and carpet.",
        "The hose behind the dishwasher came loose and flooded the kitchen floor. We caught it within an hour but the laminate is cupping.",
        "Our washing machine supply hose burst in the middle of a load. Water ran across the laundry room into the hallway and the {room}.",
        "A pipe under the kitchen sink burst while I was cooking dinner. I shut off the main right away but the sink cabinet and the floor in front of it are ruined.",
        "The ice maker line behind the refrigerator cracked and leaked onto the hardwood floors. The boards started buckling within a day.",
        "The plumber found a slab leak after our water bill doubled. They had to jackhammer the floor in the {room} to reach the line.",
        "The toilet in the hall bathroom overflowed when the fill valve stuck. Water went under the vanity and into the {room} next to it. We were home and mopped it up quickly.",
        "The upstairs AC drain pan overflowed and water dripped through the {room} ceiling while we were watching TV. We turned the system off right away.",
    ],
    "Water - Sewer Backup": [
        "During the heavy rain the city sewer backed up through our downstairs shower and toilet. Dirty water covered the bathroom and the {room} floor.",
        "Sewage came up through the floor drain in the laundry room after the storm. We threw out the rugs and the bottom of the drywall is wet.",
        "The main sewer line backed up and wastewater came out of the bathtub drain and spread into the hallway.",
        "Tree roots blocked our sewer line and it backed up into both downstairs bathrooms.",
    ],
    "Fire": [
        "A grease fire started on the stove and spread to the cabinets and range hood. There is smoke damage throughout the downstairs.",
        "Lightning hit the house during a storm and started a fire in the attic. The fire department put it out but the {room} ceiling is damaged from smoke and water.",
        "A dryer vent fire in the laundry room. Smoke and soot spread into the {room} and the hallway.",
        "An electrical fire started in the garage near the workbench. The garage door, a chest freezer and our tools were destroyed.",
        "A candle left burning caught the curtains in the {room} on fire. The wall and window frame are charred.",
    ],
    "Theft": [
        "Someone forced the back door while we were at work and took a laptop, two TVs and jewelry from the primary bedroom.",
        "Our garage was left open overnight and a bicycle, a pressure washer and power tools were stolen.",
        "Someone broke into the shed in the backyard and took the lawn mower, a generator and fishing gear.",
        "We came home from vacation to a broken {room} window. Electronics and a small safe with cash and watches were missing.",
    ],
    "Freeze": [
        "During the winter freeze a pipe in the attic burst and water poured through the {room} ceiling. We were home and shut the water off at the street.",
        "A frozen pipe on an exterior wall split during the cold snap. Water got into the wall cavity and under the {room} flooring.",
        "The pipes to the outdoor kitchen and pool equipment froze and cracked during the hard freeze.",
        "We lost power during the ice storm and a pipe in the garage ceiling burst when it thawed.",
    ],
    "Liability": [
        "A guest slipped on our wet pool deck and broke their wrist. They are asking us to cover the medical bills.",
        "Our dog bit the neighbor's child on the hand while the kids were playing in our backyard.",
        "A limb from a tree in our yard fell on the neighbor's car and they want us to pay for the repair.",
        "A delivery driver tripped on a cracked step on our front walkway and hurt their knee.",
    ],
}

# Background volume by peril and the months it occurs in.
PERIL_PLAN = [
    # peril, count, months, claimed range, cycle days range
    ("Hail", 26, [3, 4, 5, 6], (7_000, 34_000), (18, 60)),
    ("Wind", 22, [1, 3, 4, 5, 6, 8, 9], (2_000, 22_000), (12, 45)),
    ("Water - Plumbing", 46, list(range(1, 11)), (4_000, 32_000), (15, 55)),
    ("Water - Sewer Backup", 12, [3, 5, 6, 9], (3_500, 21_000), (10, 40)),
    ("Fire", 12, list(range(1, 11)), (14_000, 210_000), (30, 90)),
    ("Theft", 18, list(range(1, 11)), (1_200, 17_000), (10, 35)),
    ("Freeze", 16, [1, 2], (5_000, 38_000), (20, 60)),
    ("Liability", 10, list(range(1, 11)), (2_500, 55_000), (30, 100)),
]
# Hail and wind claims from the Oct 14-15 storm. The two Shady Elm Ct sewer backups
# further down also carry the CAT code, so 110 claims in all have CAT-2026-17.
CAT_CLAIMS = 108


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

used_policy_ids: set[str] = set()


HERO_CLAIM = "CLM-2026-10482"


def assign_claim_numbers(claims: list[dict]) -> None:
    """Number claims in report order with small gaps, like a real sequence.

    The sequence is anchored so the hero claim lands on HERO_CLAIM, which the
    Teams script and the OneDrive documents refer to by number.
    """
    claims.sort(key=lambda c: c["date_reported"])
    n, numbers = 0, []
    for _ in claims:
        n += rng.choice([1, 1, 1, 2, 2, 3])
        numbers.append(n)
    hero_idx = next(i for i, c in enumerate(claims) if c.pop("_hero", False))
    shift = int(HERO_CLAIM[-5:]) - numbers[hero_idx]
    for c, num in zip(claims, numbers):
        cid = f"CLM-2026-{num + shift:05d}"
        c["_id"] = c["claim_number"] = cid


def policy_id() -> str:
    while True:
        pid = f"POL-HO-{rng.randint(700_000, 799_999)}"
        if pid not in used_policy_ids:
            used_policy_ids.add(pid)
            return pid


def r500(x: float) -> int:
    return int(round(x / 500.0)) * 500


def r50(x: float) -> int:
    return int(round(x / 50.0)) * 50


def rand_date(month: int, year: int = 2026) -> dt.datetime:
    day = rng.randint(1, 28)
    return dt.datetime(year, month, day, rng.randint(6, 22), rng.choice([0, 15, 30, 45]))


def person() -> str:
    return f"{rng.choice(FIRST)} {rng.choice(LAST)}"


def address(city: str) -> dict:
    county, zips, _, _ = CITIES[city]
    return {
        "street": f"{rng.randint(100, 9899)} {rng.choice(STREETS)}",
        "city": city,
        "county": county,
        "state": "TX",
        "zip": rng.choice(zips),
    }


def adjuster_for(county: str) -> str:
    options = [n for n, (_, counties) in ADJUSTERS.items() if county in counties]
    return rng.choice(options or list(ADJUSTERS))


def make_policy(insured: str, addr: dict, *, endorsements: list[str] | None = None,
                inception: dt.datetime | None = None, dwelling: int | None = None,
                deductible: int | None = None, wind_hail_pct: float | None = None) -> dict:
    lo, hi = CITIES[addr["city"]][2]
    a = dwelling or r500(rng.uniform(lo, hi) / 5) * 5
    if inception is None:
        inception = dt.datetime(rng.randint(2012, 2025), rng.randint(1, 12), 1)
    # Annual term renews on the inception month/day.
    eff = inception.replace(year=2026)
    if eff > AS_OF:
        eff = eff.replace(year=2025)
    if endorsements is None:
        endorsements = []
        if rng.random() < 0.35:
            endorsements.append(rng.choice(["HO-WB-10", "HO-WB-25"]))
        for code in ["HO-SPP", "HO-ID", "HO-OL", "HO-RCC"]:
            if rng.random() < 0.25:
                endorsements.append(code)
    pid = policy_id()
    return {
        "_id": pid,
        "policy_number": pid,
        "form": "HO-3",
        "named_insured": insured,
        "property_address": addr,
        "inception_date": inception,
        "effective_date": eff,
        "expiration_date": eff.replace(year=eff.year + 1),
        "coverage": {
            "A_dwelling": a,
            "B_other_structures": a // 10,
            "C_personal_property": a // 2,
            "D_loss_of_use": a // 5,
            "E_personal_liability": rng.choice([300_000, 500_000]),
            "F_medical_payments": 5_000,
        },
        "deductibles": {
            "all_peril": deductible or rng.choice([1_000, 1_500, 2_500, 2_500, 5_000]),
            "wind_hail_pct": wind_hail_pct if wind_hail_pct is not None else rng.choice([0.01, 0.01, 0.02]),
        },
        "endorsements": [
            {"code": c, "description": ENDORSEMENTS[c][0], "limit": ENDORSEMENTS[c][1]}
            for c in endorsements
        ],
        "annual_premium": r50(a * rng.uniform(0.0085, 0.0125)),
        "agent": rng.choice(["Contoso Direct", "Hill Country Agency", "Metroplex Insurance Partners",
                             "Gulf Coast Agency Group"]),
    }


def deductible_for(policy: dict, peril: str) -> int:
    if peril in ("Hail", "Wind"):
        return int(policy["coverage"]["A_dwelling"] * policy["deductibles"]["wind_hail_pct"])
    if peril == "Liability":
        return 0
    return policy["deductibles"]["all_peril"]


def has_water_backup(policy: dict) -> bool:
    return any(e["code"].startswith("HO-WB") for e in policy["endorsements"])


def notes_for(status: str, adjuster: str, reported: dt.datetime, closed: dt.datetime | None,
              denial: str | None) -> list[dict]:
    notes = [{"date": reported + dt.timedelta(hours=rng.randint(3, 26)), "author": adjuster,
              "note": "First contact with insured. Explained claim process and requested photos."}]
    if status != "Pending Documents":
        notes.append({"date": reported + dt.timedelta(days=rng.randint(2, 6)), "author": adjuster,
                      "note": "Inspection completed. Scope written against the Contoso Pricing Guide."})
    if status == "Pending Documents":
        notes.append({"date": reported + dt.timedelta(days=rng.randint(2, 6)), "author": adjuster,
                      "note": "Waiting on contractor invoice and proof of ownership from insured."})
    if closed and status == "Closed - Paid":
        notes.append({"date": closed, "author": adjuster, "note": "Payment issued. File closed."})
    if closed and status == "Closed - Denied":
        notes.append({"date": closed, "author": adjuster, "note": f"Claim denied: {denial}. Letter sent."})
    return notes


# --------------------------------------------------------------------------
# Claim builders
# --------------------------------------------------------------------------

claims: list[dict] = []
policies: list[dict] = []


def build_claim(*, peril: str, loss: dt.datetime, city: str | None = None,
                claimed_range=(5_000, 20_000), cycle=(15, 50), cat: bool = False) -> None:
    city = city or rng.choice(list(CITIES))
    insured = person()
    addr = address(city)
    pol = make_policy(insured, addr)
    policies.append(pol)
    reported = loss + dt.timedelta(days=rng.choice([0, 1, 1, 1, 2, 2, 3, 5, 8]), hours=rng.randint(1, 8))
    if reported > AS_OF - dt.timedelta(days=1):
        reported = AS_OF - dt.timedelta(days=1, hours=rng.randint(1, 10))
    adjuster = adjuster_for(addr["county"])
    claimed = r50(rng.uniform(*claimed_range))
    contractor = None
    guide = None
    if peril in ("Water - Plumbing", "Water - Sewer Backup", "Freeze") and rng.random() < 0.8:
        contractor = rng.choice(WATER_CONTRACTORS)
    elif peril in ("Hail", "Wind") and rng.random() < 0.6:
        contractor = rng.choice(ROOF_CONTRACTORS)
    elif peril == "Fire" and rng.random() < 0.8:
        contractor = rng.choice(FIRE_CONTRACTORS)
    if contractor:
        guide = r50(claimed / rng.uniform(0.94, 1.14))

    # Coverage decision
    deductible = deductible_for(pol, peril)
    covered_basis = min(claimed, guide) if guide else claimed * rng.uniform(0.85, 1.0)
    denial = None
    if peril == "Water - Sewer Backup" and not has_water_backup(pol):
        denial = "Water backup excluded under HO-3; no HO-WB endorsement on policy"
    elif covered_basis <= deductible:
        denial = "Covered damage does not exceed the deductible"
    elif peril == "Water - Plumbing" and rng.random() < 0.12:
        denial = "Continuous or repeated seepage over 14 days (HO-3 Section I exclusion)"
    elif peril == "Theft" and rng.random() < 0.1:
        denial = "No police report provided within policy conditions"

    # Coverage denials close fast; everything else takes the peril's cycle time.
    cycle_days = rng.randint(3, 10) if denial else rng.randint(*cycle)
    closed_date = reported + dt.timedelta(days=cycle_days, hours=rng.randint(1, 7))
    is_closed = closed_date < AS_OF - dt.timedelta(days=1)

    if is_closed:
        status = "Closed - Denied" if denial else "Closed - Paid"
        if peril == "Water - Sewer Backup" and status == "Closed - Paid":
            limit = next(e["limit"] for e in pol["endorsements"] if e["code"].startswith("HO-WB"))
            paid = min(limit, r50(covered_basis - deductible))
        else:
            paid = 0 if denial else r50(covered_basis - deductible)
        reserve = 0
    else:
        closed_date = None
        status = rng.choices(["Open", "Under Review", "Pending Documents"], [0.55, 0.25, 0.2])[0]
        paid = 0
        reserve = max(500, r500((covered_basis - deductible) * rng.uniform(0.85, 1.05)))
        denial = None

    desc = rng.choice(DESCRIPTIONS[peril]).format(room=rng.choice(ROOMS), side=rng.choice(SIDES))
    claims.append({
        "_id": None,
        "claim_number": None,
        "policy_number": pol["policy_number"],
        "insured_name": insured,
        "property_address": addr,
        "line_of_business": "Homeowners",
        "peril": peril,
        "cat_event": {"code": CAT_CODE, "name": CAT_NAME} if cat else None,
        "date_of_loss": loss,
        "date_reported": reported,
        "date_closed": closed_date,
        "status": status,
        "assigned_adjuster": adjuster,
        "claimed_amount": claimed,
        "reserve_amount": reserve,
        "paid_amount": paid,
        "deductible_applied": deductible,
        "contractor": {"name": contractor, "estimate_amount": claimed} if contractor else None,
        "pricing_guide_estimate": guide,
        "assignment_of_benefits": bool(contractor) and rng.random() < 0.08,
        "denial_reason": denial if status == "Closed - Denied" else None,
        "loss_description": desc,
        "adjuster_notes": notes_for(status, adjuster, reported, closed_date, denial),
    })


# Background claims, Jan-Oct 2026
for peril, count, months, claimed_range, cycle in PERIL_PLAN:
    for _ in range(count):
        build_claim(peril=peril, loss=rand_date(rng.choice(months)),
                    claimed_range=claimed_range, cycle=cycle)

# The Oct 14-15 hailstorm (CAT-2026-17)
for _ in range(CAT_CLAIMS):
    peril = "Hail" if rng.random() < 0.8 else "Wind"
    loss = dt.datetime(2026, 10, rng.choice([14, 14, 14, 15]), rng.randint(16, 23), rng.choice([0, 30]))
    build_claim(peril=peril, loss=loss, city=rng.choice(HAIL_CITIES),
                claimed_range=(6_000, 38_000) if peril == "Hail" else (2_000, 20_000),
                cycle=(9, 40), cat=True)


# --------------------------------------------------------------------------
# The story: LeafyDry Restoration water losses in Collin County
# --------------------------------------------------------------------------
# Seven claims, Aug-Oct 2026. Same shape every time: homeowner away, water
# through a ceiling below an upstairs bathroom, LeafyDry on site within the
# hour, assignment of benefits signed that night, full tear-out recommended,
# estimate well above the Contoso Pricing Guide. Worded differently each time
# so a keyword search does not find them all but a semantic search does.

LEAFYDRY = [
    dict(city="Frisco", loss=dt.datetime(2026, 8, 23, 19, 0), days_to_report=1,
         insured="Natalie and Greg Whitfield", status="Closed - Paid", closed_after=19,
         claimed=34_600, guide=25_900, adjuster="Maya Chen", deductible=1_500,
         desc="Got back from a work trip and the living room ceiling was sagging and dripping. The guest bath is directly above it. A water mitigation company a neighbor had used, LeafyDry, came out the same evening and said all the drywall downstairs and the bathroom subfloor need to come out."),
    dict(city="McKinney", loss=dt.datetime(2026, 9, 6, 21, 30), days_to_report=2,
         insured="Brandon Keller", status="Closed - Paid", closed_after=17,
         claimed=38_950, guide=27_800, adjuster="Jordan Reyes", deductible=2_500,
         desc="Our family was at the lake for Labor Day weekend. When we got home the dining room ceiling had a big brown bulge and water was running down the wall. LeafyDry Restoration had a truck in the driveway in about forty minutes and recommended full demolition of the dining room and the hall bathroom above it."),
    dict(city="Allen", loss=dt.datetime(2026, 9, 20, 22, 15), days_to_report=1,
         insured="Linda Hartman", status="Closed - Paid", closed_after=21,
         claimed=29_400, guide=21_700, adjuster="Maya Chen", deductible=1_000,
         desc="I was out of state for my daughter's wedding and my house sitter called about water coming out of the light fixture in the den. The restoration contractor who showed up that night said the toilet supply line upstairs failed and everything underneath has to be gutted."),
    dict(city="Plano", loss=dt.datetime(2026, 10, 3, 20, 45), days_to_report=1,
         insured="Steven and Amy Lindqvist", status="Open", closed_after=None,
         claimed=44_200, guide=31_100, adjuster="Maya Chen", deductible=2_500,
         desc="Came back from a weekend in Austin and found part of the family room ceiling had collapsed. The shower valve in the upstairs bath had been leaking. LeafyDry was recommended by someone in our HOA and arrived right away. They say the cabinets, floors and drywall all have to be replaced."),
    dict(city="Frisco", loss=dt.datetime(2026, 10, 11, 23, 0), days_to_report=1,
         insured="Derek Mullen", status="Pending Documents", closed_after=None,
         claimed=36_750, guide=26_400, adjuster="Jordan Reyes", deductible=1_500,
         inception=dt.datetime(2026, 8, 20),
         desc="Returned home after a few days away and saw water stains spreading across the kitchen ceiling and dripping near the island. The mitigation crew found a leak under the upstairs vanity and said the whole area including the subfloor must be removed."),
    # The hero claim
    dict(city="Plano", loss=dt.datetime(2026, 10, 18, 21, 10), days_to_report=1,
         insured="Daniel and Rachel Brennan", status="Under Review", closed_after=None,
         claimed=41_850, guide=32_500, adjuster="Maya Chen", deductible=2_500,
         street="2214 Briar Hollow Ln", zip="75093", policy="POL-HO-778301", hero=True,
         inception=dt.datetime(2019, 5, 1), dwelling=485_000,
         endorsements=["HO-SPP", "HO-RCC"],
         desc="We were away at my sister's for the weekend and came home Sunday night to water pouring through the kitchen ceiling. Part of the drywall had come down onto the counters. A restoration crew from LeafyDry was there within the hour and told us the whole kitchen and the upstairs bathroom floor have to be torn out. We have two little kids and no working kitchen right now."),
    dict(city="Plano", loss=dt.datetime(2026, 10, 25, 22, 30), days_to_report=1,
         insured="Henry and Joanne Pruitt", status="Open", closed_after=None,
         claimed=39_300, guide=28_600, adjuster="Maya Chen", deductible=2_500,
         desc="We were out of town visiting the grandkids. When we got back the ceiling under the primary bathroom had caved in over the breakfast nook. A restoration company got there fast and is recommending we tear out the nook, the kitchen soffits and the bathroom floor."),
]

for s in LEAFYDRY:
    addr = address(s["city"])
    if "street" in s:
        addr["street"], addr["zip"] = s["street"], s["zip"]
    pol = make_policy(s["insured"], addr, endorsements=s.get("endorsements"),
                      inception=s.get("inception"), dwelling=s.get("dwelling"),
                      deductible=s["deductible"], wind_hail_pct=0.01)
    if "policy" in s:
        used_policy_ids.discard(pol["_id"])
        pol["_id"] = pol["policy_number"] = s["policy"]
        used_policy_ids.add(s["policy"])
    policies.append(pol)
    reported = s["loss"] + dt.timedelta(days=s["days_to_report"], hours=-10)
    closed = reported + dt.timedelta(days=s["closed_after"]) if s["closed_after"] else None
    paid = s["claimed"] - s["deductible"] if s["status"] == "Closed - Paid" else 0
    reserve = 0 if closed else r500(s["claimed"] * 0.85)
    notes = [
        {"date": reported + dt.timedelta(hours=4), "author": s["adjuster"],
         "note": "First contact with insured. Insured states they were away from home when the loss was discovered."},
        {"date": reported + dt.timedelta(hours=5), "author": s["adjuster"],
         "note": f"Assignment of benefits to {BAD_ACTOR} received, signed on the date of loss."},
    ]
    if closed:
        notes.append({"date": closed, "author": s["adjuster"],
                      "note": "Contractor estimate accepted. Payment issued to LeafyDry Restoration LLC under AOB. File closed."})
    elif s["status"] == "Pending Documents":
        notes.append({"date": reported + dt.timedelta(days=4), "author": s["adjuster"],
                      "note": "Requested moisture mapping and plumber's invoice from LeafyDry. Not yet received."})
    if s.get("hero"):
        notes += [
            {"date": dt.datetime(2026, 10, 22, 15, 30), "author": "Jordan Reyes",
             "note": "Field inspection completed. See Teams channel for findings and scope breakdown. Photos uploaded."},
            {"date": dt.datetime(2026, 10, 28, 9, 10), "author": "Maya Chen",
             "note": "Insured called for status (third call this week). Family displaced from kitchen with two children under five. Escalated to Team Lead for review."},
        ]
    claims.append({
        "_id": None,
        "claim_number": None,
        **({"_hero": True} if s.get("hero") else {}),
        "policy_number": pol["policy_number"],
        "insured_name": s["insured"],
        "property_address": addr,
        "line_of_business": "Homeowners",
        "peril": "Water - Plumbing",
        "cat_event": None,
        "date_of_loss": s["loss"],
        "date_reported": reported,
        "date_closed": closed,
        "status": s["status"],
        "assigned_adjuster": s["adjuster"],
        "claimed_amount": s["claimed"],
        "reserve_amount": reserve,
        "paid_amount": paid,
        "deductible_applied": s["deductible"],
        "contractor": {"name": BAD_ACTOR, "estimate_amount": s["claimed"]},
        "pricing_guide_estimate": s["guide"],
        "assignment_of_benefits": True,
        "denial_reason": None,
        "loss_description": s["desc"],
        "adjuster_notes": notes,
    })


# --------------------------------------------------------------------------
# Side story: two sewer backups on the same Irving street, same night
# --------------------------------------------------------------------------
# Same storm, same damage. One policy carries the water backup endorsement and
# one does not. Shows Copilot reading the policy record in Atlas and the
# exclusion in the policy form on OneDrive.

SEWER = [
    dict(insured="Grace Thompson", street="3318 Shady Elm Ct", endorsements=["HO-ID"],
         claimed=14_900, desc="During the storm on the night of the 15th the city sewer backed up through our downstairs shower and toilet. About two inches of dirty water covered the bathroom and the hallway carpet."),
    dict(insured="Kevin and Lauren Park", street="3326 Shady Elm Ct", endorsements=["HO-WB-10", "HO-OL"],
         claimed=13_600, desc="Heavy rain overnight and sewage came up through the guest bathroom tub and toilet. The water spread into the guest bedroom and soaked the carpet and the bottom of the drywall."),
]
for s in SEWER:
    addr = {"street": s["street"], "city": "Irving", "county": "Dallas", "state": "TX", "zip": "75038"}
    pol = make_policy(s["insured"], addr, endorsements=s["endorsements"], deductible=1_000,
                      wind_hail_pct=0.01)
    policies.append(pol)
    loss = dt.datetime(2026, 10, 15, 2, 30)
    reported = dt.datetime(2026, 10, 16, 8, 15)
    claims.append({
        "_id": None,
        "claim_number": None,
        "policy_number": pol["policy_number"],
        "insured_name": s["insured"],
        "property_address": addr,
        "line_of_business": "Homeowners",
        "peril": "Water - Sewer Backup",
        "cat_event": {"code": CAT_CODE, "name": CAT_NAME},
        "date_of_loss": loss,
        "date_reported": reported,
        "date_closed": None,
        "status": "Open",
        "assigned_adjuster": "Priya Nair",
        "claimed_amount": s["claimed"],
        "reserve_amount": r500(s["claimed"] * 0.8),
        "paid_amount": 0,
        "deductible_applied": 1_000,
        "contractor": {"name": "Metroplex Mitigation Services", "estimate_amount": s["claimed"]},
        "pricing_guide_estimate": r50(s["claimed"] / 1.04),
        "assignment_of_benefits": False,
        "denial_reason": None,
        "loss_description": s["desc"],
        "adjuster_notes": [
            {"date": reported + dt.timedelta(hours=3), "author": "Priya Nair",
             "note": "First contact with insured. Mitigation already underway by Metroplex Mitigation Services."},
        ],
    })


# --------------------------------------------------------------------------
# Write
# --------------------------------------------------------------------------

def main() -> None:
    OUT.mkdir(exist_ok=True)
    assign_claim_numbers(claims)
    assert len({c["_id"] for c in claims}) == len(claims)
    assert len({p["_id"] for p in policies}) == len(policies)
    opts = json_util.JSONOptions(json_mode=json_util.JSONMode.RELAXED, tz_aware=False)
    (OUT / "claims.json").write_text(json_util.dumps(claims, indent=2, json_options=opts))
    (OUT / "policies.json").write_text(json_util.dumps(policies, indent=2, json_options=opts))
    print(f"wrote {len(claims)} claims and {len(policies)} policies to {OUT}")


if __name__ == "__main__":
    main()
