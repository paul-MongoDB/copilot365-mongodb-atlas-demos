"""Build the Word documents for the Leafy Tech demo, and the Teams post sheet.

    python demos/leafy-tech/scripts/build_documents.py
        ->  onedrive/*.docx            (upload these to OneDrive)
        ->  teams/TEAMS_MESSAGES.md    (post these in Teams)
        ->  fallback/Willow Bend Refresh channel export.docx   (upload this too: see README)

All wording is original and fictional. Leafy Tech and Willow Bend Health are not real businesses.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
FOOTER = "Leafy Tech. Fictional document created for a product demonstration."
TEAM, CHANNEL = "Leafy Tech (DEMO)", "Willow Bend Refresh"

# (subject, sender, role, date, paragraphs)
POSTS = [
    ("Willow Bend quote ready for sign-off", "Nina Patel", "Account Manager", "Mon Nov 2",
     ["Paul, the Willow Bend Health laptop refresh is in the system as quote Q-2026-4471: 500 clinical laptops "
      "with docks, warranty and imaging. They pushed hard on price, so I went to 14% off on every line. They want "
      "it by Friday, and it is over $500,000, so it needs your sign-off."]),
    ("What Willow Bend's nurses told me", "Nina Patel", "Account Manager", "Mon Nov 2",
     ["I asked the nursing lead what they need, and I wrote it down word for word: \"Our nurses push a cart from "
      "room to room all shift. It gets wiped down with harsh cleaning chemicals between every patient, it cannot "
      "die halfway through a 12-hour shift, and it gets knocked off the cart a few times a year.\""]),
    ("Willow Bend carts", "Omar Haddad", "Presales Engineer", "Tue Nov 3",
     ["I walked the Willow Bend floors today. All of their new carts use the G2 mount, so a G1 dock will not fit "
      "them. Whatever we quote has to be the G2 dock."]),
    ("Deal registration", "Grace Okafor", "Vendor Manager", "Tue Nov 3",
     ["I do not see a Fabrikam deal registration for Willow Bend. It has to be approved before the quote goes to "
      "the customer, or we lose the rebate. Approval takes one business day, so someone needs to file it now."]),
    ("MedBook truck", "Terry Boone", "Warehouse Lead", "Wed Nov 4",
     ["Heads up: a truck with 180 MedBook 14 Clinical laptops is due at the Chicago warehouse on Thursday. I will "
      "book them in as soon as it arrives."]),
]


def new_doc(title: str, subtitle: str, created=datetime(2026, 1, 12, 9, 0), modified=datetime(2026, 10, 5, 9, 0)) -> Document:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)
    r = doc.add_paragraph().add_run("LEAFY TECH")
    r.bold = True
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x00, 0x68, 0x4A)
    doc.add_heading(title, level=0)
    doc.add_paragraph(subtitle).runs[0].italic = True
    cp = doc.core_properties  # python-docx defaults to 2013 and 'python-docx'; Copilot shows these
    cp.author = cp.last_modified_by = "Leafy Tech Sales Operations"
    cp.title = title
    cp.created, cp.modified = created, modified
    footer = doc.sections[0].footer.paragraphs[0]
    footer.text = FOOTER
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.runs[0].font.size = Pt(8)
    return doc


def numbered(doc: Document, *items: str) -> None:
    # Literal numbers, so "rule 2" means the same thing in Word and in Copilot's text extract.
    for i, t in enumerate(items, 1):
        p = doc.add_paragraph(f"{i}.\t{t}")
        p.paragraph_format.left_indent = Inches(0.35)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(0.35))


def policy() -> None:
    doc = new_doc("Quote and Discount Policy",
                  "Applies to every customer quote. Owner: Sales Operations. Last updated October 2026.")
    doc.add_heading("1. Pricing rules", level=1)
    numbered(doc,
             "An Account Manager may discount hardware and warranties by up to 10% off list price. A deeper "
             "discount needs Sales Director approval. A customer contract price overrides this rule.",
             "Services, such as imaging, asset tagging and installation, are always sold at list price. "
             "They are never discounted.",
             "Every quote must keep a gross margin of at least 15%. There are no exceptions. Gross margin is "
             "(price minus cost) divided by price, using catalog cost and before any vendor rebate.")
    doc.add_heading("2. Product rules", level=1)
    numbered(doc,
             "Never quote a product with an end_of_life status in the catalog. Quote its replacement.",
             "Before a quote goes out, the quantity available must cover the quantity quoted. Available "
             "means on hand minus reserved, across all warehouses.")
    doc.add_heading("3. Approval", level=1)
    doc.add_paragraph("Any quote over $500,000 needs Sales Director sign-off before it goes to the customer. "
                      "The Sales Director also checks that any vendor deal registration is in place.")
    doc.save(ROOT / "onedrive" / "Quote and Discount Policy.docx")


def rebate() -> None:
    doc = new_doc("Fabrikam Partner Rebate Program 2026",
                  "Summary of the rebate terms for Leafy Tech, prepared by the Vendor Management team.")
    doc.add_heading("How the rebate works", level=1)
    numbered(doc,
             "Fabrikam pays a rebate of 4% of Leafy Tech's cost on Fabrikam notebooks sold in a registered deal.",
             "A deal qualifies at 250 notebooks or more. Warranties and other products earn no rebate.",
             "The registration must be approved before the quote goes to the customer. A deal registered "
             "after the quote is sent earns nothing.",
             "Approval takes one business day. An approved deal has a registration ID, which goes on the quote.")
    doc.save(ROOT / "onedrive" / "Fabrikam Partner Rebate Program 2026.docx")


def contract() -> None:
    doc = new_doc("Master Purchase Agreement: Willow Bend Health",
                  "Between Leafy Tech and Willow Bend Health. Term: January 1, 2026 to December 31, 2028.")
    doc.add_heading("3. Pricing", level=1)
    doc.add_paragraph("Hardware and warranties are sold at 10% off Leafy Tech's list price, fixed for the term. "
                      "Any other discount requires a signed amendment to this agreement. Services are sold at "
                      "list price.")
    doc.add_heading("4. Warranty", level=1)
    doc.add_paragraph("Every clinical device must ship with a four-year onsite warranty.")
    doc.add_heading("5. Delivery", level=1)
    doc.add_paragraph("Leafy Tech delivers within 30 days of the purchase order, in one shipment per site.")
    doc.save(ROOT / "onedrive" / "Willow Bend Health Master Purchase Agreement.docx")


def channel_export() -> None:
    doc = new_doc(f"{CHANNEL} channel export",
                  f"Team: {TEAM}. Channel: {CHANNEL}. Posts in the order they were made.",
                  created=datetime(2026, 11, 4, 17, 0), modified=datetime(2026, 11, 4, 17, 0))
    for subject, sender, role, date, paras in POSTS:
        doc.add_heading(subject, level=2)
        doc.add_paragraph(f"Posted by {sender} ({role}), {date}").runs[0].italic = True
        for t in paras:
            doc.add_paragraph(t)
    doc.save(ROOT / "fallback" / f"{CHANNEL} channel export.docx")


def teams_sheet() -> None:
    lines = [
        "# Teams posts for the Leafy Tech demo", "",
        f"Create a team called **{TEAM}** with a standard channel called **{CHANNEL}**.",
        "For each post below, start a new post, paste the subject into the subject box, and paste the",
        "message into the message box. Change nothing.", "", "---", ""]
    for i, (subject, sender, role, _date, paras) in enumerate(POSTS, 1):
        lines += [f"## Post {i}", "", "**Subject:**", "", "```", subject, "```", "", "**Message:**", "", "```",
                  f"Posting for {sender}, {role}:", "", *paras, "```", "", "---", ""]
    (ROOT / "teams" / "TEAMS_MESSAGES.md").write_text("\n".join(lines))


def main() -> None:
    for d in ("onedrive", "teams", "fallback"):
        (ROOT / d).mkdir(exist_ok=True)
    policy()
    rebate()
    contract()
    channel_export()
    teams_sheet()
    for p in sorted((ROOT / "onedrive").glob("*.docx")):
        print(p.name)


if __name__ == "__main__":
    main()
