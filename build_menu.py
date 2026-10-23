"""Regenerate the menu section of index.html from sisters-menu.md.
Usage: python3 build_menu.py sisters-menu.md path/to/index.html
"""
import re, html, sys

MD, SRC = sys.argv[1], sys.argv[2]

TAB = {
    "Coffee": ("coffee", "☕"), "Iced Coffee": ("coffee", "🧊"),
    "Tea & Hot Drinks": ("coffee", "🫖"), "Cold Drinks": ("coffee", "🥤"),
    "Bites & Sandwiches": ("eats", "🍽"), "Desserts": ("eats", "🍰"),
    "Wine & Cocktails": ("drinks", "🍷"), "Spirits": ("drinks", "🥃"),
    "Beer": ("beer", "🍺"), "Packed Products": ("extras", "🛍"),
}
TABS = [("coffee", "Coffee &amp; Drinks"), ("eats", "Eats"),
        ("drinks", "Wine &amp; Cocktails"), ("beer", "Beer"), ("extras", "Extras")]
SIZE = re.compile(r"^(.*?)\s+(\d+(?:\.\d+)?\s*(?:ml|cl|gr|g))\.?$", re.I)
ITEM = re.compile(r"^- \*\*(.+?)\*\*(?: · .+?)? \.\.\.\. \*\*(.+?)\*\*$")

# ── parse md ──
sections, sec, blk = [], None, None
for line in open(MD, encoding="utf-8"):
    line = line.rstrip("\n")
    if line.startswith("## "):
        name = line[3:].split(" · ")[0].strip()
        if name not in TAB: sec = None; continue
        sec = dict(name=name, tab=TAB[name][0], icon=TAB[name][1], blocks=[])
        blk = dict(sub=None, note=None, items=[]); sec["blocks"].append(blk); sections.append(sec)
    elif not sec:
        continue
    elif line.startswith("### "):
        sub = line[4:].split(" · ")[0].strip()
        blk = dict(sub=None if sub == "Extras" else sub, skip=sub == "Extras", note=None, items=[])
        sec["blocks"].append(blk)
    elif line.startswith("_") and not blk["items"]:
        blk["note"] = line.strip("_")
    elif (m := ITEM.match(line)):
        name, price, note = m.group(1), m.group(2).replace("/", " / "), None
        if (s := SIZE.match(name)):
            name, note = s.group(1), re.sub(r"\s+", "", s.group(2)).replace("gr", "g")
        blk["items"].append(dict(name=name, note=note, price=price, desc=None))
    elif line.startswith("  - _") and blk["items"]:
        blk["items"][-1]["desc"] = line.strip()[2:].strip("_").split(" / ")[0].strip()

# ── helpers ──
esc = lambda s: html.escape(s, quote=False)
src = open(SRC, encoding="utf-8").read()

def grab(marker):
    i = src.find(marker); depth, j = 0, i
    tok = re.compile(r"<div\b|</div>")
    while True:
        m = tok.search(src, j); depth += -1 if m.group(0) == "</div>" else 1; j = m.end()
        if depth == 0: return src[i:j]

red_bull = next(it["price"] for s in sections for b in s["blocks"] for it in b["items"] if it["name"] == "Red Bull")
ADDONS = grab('<div class="addons-banner">')
REDBULL = re.sub(r'(<p class="redbull-all-price">All flavours · )\d+(</p>)', rf"\g<1>{red_bull}\g<2>",
                 grab('<div class="menu-category redbull-showcase">'))

def row(it):
    n = esc(it["name"]) + (f' <span class="item-note">({esc(it["note"])})</span>' if it["note"] else "")
    out = (f'      <div class="menu-item"><span class="item-name">{n}</span>'
           f'<span class="item-dots"></span><span class="item-price">{esc(it["price"])}</span></div>')
    return out + (f'\n      <p class="item-desc">{esc(it["desc"])}</p>' if it["desc"] else "")

# ── emit ──
P = ['<div class="tabs">']
P += [f'    <button class="tab-btn{" active" if t == "coffee" else ""}" data-tab="{t}">{l}</button>' for t, l in TABS]
P.append("  </div>\n")
for t, _ in TABS:
    P += [f"  <!-- {t.upper()} -->", f'  <div class="menu-panel{" active" if t == "coffee" else ""}" id="{t}">']
    for s in (s for s in sections if s["tab"] == t):
        P += ['    <div class="menu-category">', f'      <h3><span class="icon">{s["icon"]}</span> {esc(s["name"])}</h3>']
        for b in s["blocks"]:
            if b.get("skip"): continue
            if b["sub"]: P.append(f'      <h4>{esc(b["sub"])}</h4>')
            if b["note"]: P.append(f'      <p class="item-desc">{esc(b["note"])}</p>')
            P += [row(it) for it in b["items"]]
        if s["name"] == "Coffee": P.append("    " + ADDONS)
        P.append("    </div>")
    if t == "extras": P.append("    " + REDBULL)
    P.append("  </div>\n")

start = src.find('<div class="tabs">')
end = src.find("</section>", src.find('id="extras"'))
new = src[:start] + "\n".join(P).rstrip() + "\n" + src[end:]

CSS = """.item-desc {
    font-size: 0.82rem;
    color: var(--text-light);
    font-weight: 300;
    font-style: italic;
    margin: 0 0 0.55rem;
    padding-bottom: 0.5rem;
    max-width: 46ch;
    border-bottom: 1px dotted var(--sand-light);
  }
  .menu-item:has(+ .item-desc) { border-bottom: none; padding-bottom: 0.15rem; }

  .menu-category > h4 {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--terracotta);
    margin: 1.75rem 0 0.6rem;
  }

  .item-price {"""
if ".item-desc {" not in new:
    new = new.replace(".item-price {", CSS, 1)

open(SRC, "w", encoding="utf-8").write(new)
print("sections", len(sections), "items", sum(len(b["items"]) for s in sections for b in s["blocks"]))
