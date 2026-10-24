"""
stage_art.py
============
Original SVG illustrations of the soybean growth stages (Fehr & Caviness, 1977) and the stage
descriptions shown in the web app. Everything is drawn in code, so there are no image files to
download, no licences to worry about, and it works offline.

    from stage_art import stage_svg, STAGES, GROUP_KEY
    svg_text = stage_svg("r2")
"""
import math

W, H = 300, 340
GROUND = 292

# ----------------------------------------------------------------------------------------------
# Stage descriptions (paraphrased from Fehr & Caviness, 1977, Iowa State University Special Report 80)
# ----------------------------------------------------------------------------------------------
STAGES = [
    {"key": "ve", "code": "VE", "name": "Emergence", "group": "Vegetative",
     "definition": "The seedling pushes through the soil and the two seed leaves (cotyledons) appear above the surface.",
     "look_for": ["Two fat, green seed leaves above the soil", "No true leaves yet"]},
    {"key": "vc", "code": "VC", "name": "Cotyledon stage", "group": "Vegetative",
     "definition": "The first true leaves, which are single leaves (unifoliolate), have unrolled so their edges no longer touch.",
     "look_for": ["Two single, heart-shaped leaves above the seed leaves", "Seed leaves still attached below"]},
    {"key": "v1", "code": "V1", "name": "First node", "group": "Vegetative",
     "definition": "The unifoliolate leaves are fully developed and the first three-part (trifoliolate) leaf is forming above them.",
     "look_for": ["First leaf made of three leaflets appears", "Seed leaves are shrivelling or gone"]},
    {"key": "vn", "code": "V2 to Vn", "name": "Second node to nth node", "group": "Vegetative",
     "definition": "One new node with a fully developed trifoliolate leaf is added at a time (V2, V3, V4 and so on) until flowering begins.",
     "look_for": ["Count the nodes with fully open three-leaflet leaves", "No open flowers yet"]},
    {"key": "r1", "code": "R1", "name": "Beginning bloom", "group": "Flowering",
     "definition": "One open flower appears at any node on the main stem.",
     "look_for": ["First small purple or white flower open", "Plant is still adding nodes"]},
    {"key": "r2", "code": "R2", "name": "Full bloom", "group": "Flowering",
     "definition": "An open flower is present at one of the two uppermost nodes on the main stem that has a fully developed leaf.",
     "look_for": ["Flowers open near the top of the plant", "Many flowers along the main stem"]},
    {"key": "r3", "code": "R3", "name": "Beginning pod", "group": "Pod",
     "definition": "A pod about 5 mm long is present at one of the four uppermost nodes on the main stem with a fully developed leaf.",
     "look_for": ["Tiny pods (about 5 mm) near the top", "Flowers may still be opening above them"]},
    {"key": "r4", "code": "R4", "name": "Full pod", "group": "Pod",
     "definition": "A pod about 2 cm long is present at one of the four uppermost nodes on the main stem with a fully developed leaf.",
     "look_for": ["Flat green pods about 2 cm long at the top", "Leaves are still fully green"]},
    {"key": "r5", "code": "R5", "name": "Beginning seed", "group": "Seed",
     "definition": "A seed about 3 mm long can be felt inside a pod at one of the four uppermost nodes with a fully developed leaf.",
     "look_for": ["Pods start to bulge where seeds form", "Small seeds felt when squeezing a top pod"]},
    {"key": "r6", "code": "R6", "name": "Full seed", "group": "Seed",
     "definition": "A pod at one of the four uppermost nodes holds a green seed that fills the pod cavity.",
     "look_for": ["Plump green pods with seeds filling them", "Lower leaves begin to yellow"]},
    {"key": "r7", "code": "R7", "name": "Beginning maturity", "group": "Maturity",
     "definition": "One normal pod on the main stem has reached its mature pod colour (brown or tan).",
     "look_for": ["At least one brown or tan pod", "Leaves yellowing and starting to drop"]},
    {"key": "r8", "code": "R8", "name": "Full maturity", "group": "Maturity",
     "definition": "About 95% of the pods have reached their mature colour. A few dry days are needed before harvest.",
     "look_for": ["Almost all pods brown or tan", "Most leaves have fallen"]},
]
STAGE_BY_KEY = {s["key"]: s for s in STAGES}
GROUP_KEY = {"Vegetative": "vn", "Flowering": "r2", "Pod": "r4", "Seed": "r6", "Maturity": "r8"}
GROUP_INFO = {
    "Vegetative": {"stages": "VE to Vn", "blurb": "The plant is building roots, leaves and nodes. No flowers yet.",
                   "look_for": ["Count fully open three-leaflet leaves", "No open flowers on the main stem"]},
    "Flowering": {"stages": "R1 to R2", "blurb": "Flowers open and the plant starts to set the yield it will carry.",
                  "look_for": ["Open flowers on the main stem", "Flowers reach the top nodes by full bloom"]},
    "Pod": {"stages": "R3 to R4", "blurb": "Pods form and grow to full length at the top of the plant.",
            "look_for": ["Pods from 5 mm up to about 2 cm long", "Leaves still fully green"]},
    "Seed": {"stages": "R5 to R6", "blurb": "Seeds swell inside the pods until they fill the pod cavity.",
             "look_for": ["Pods bulging with seeds", "Lower leaves starting to yellow"]},
    "Maturity": {"stages": "R7 to R8", "blurb": "Pods turn brown and leaves drop as the crop dries down for harvest.",
                 "look_for": ["Brown or tan pods", "Leaves yellow or fallen"]},
}

# ----------------------------------------------------------------------------------------------
# Drawing parameters per stage
# ----------------------------------------------------------------------------------------------
GREEN, GREEN_DK = "#3f9142", "#2b6a31"
CFG = {
    "ve": dict(zoom=2.5, h=46, nodes=0, cot="fat", unifol=False, leaf="#43a047"),
    "vc": dict(zoom=2.05, h=78, nodes=0, cot="fat", unifol=True, leaf="#43a047"),
    "v1": dict(zoom=1.55, h=118, nodes=1, cot="shrunk", unifol=True, leaf="#43a047"),
    "vn": dict(zoom=1.2, h=178, nodes=4, cot="dry", unifol=True, leaf="#3f9a45"),
    "r1": dict(h=212, nodes=6, cot="none", unifol=True, leaf="#3c9443", flowers=2),
    "r2": dict(h=232, nodes=7, cot="none", unifol=True, leaf="#3a8f41", flowers=9),
    "r3": dict(h=240, nodes=7, cot="none", unifol=True, leaf="#3a8f41", flowers=3,
               pods=dict(n=5, length=8, w=3.5, color="#a9d86b")),
    "r4": dict(h=246, nodes=7, cot="none", unifol=True, leaf="#3a8f41", flowers=1,
               pods=dict(n=8, length=25, w=6.5, color="#a0d462")),
    "r5": dict(h=250, nodes=7, cot="none", unifol=True, leaf="#4a9a3f",
               pods=dict(n=9, length=27, w=9.5, color="#9fd36a", seeds=True)),
    "r6": dict(h=252, nodes=7, cot="none", unifol=True, leaf="#8fb23a", lower_yellow=True,
               pods=dict(n=10, length=29, w=12, color="#8fcc5c", seeds=True)),
    "r7": dict(h=252, nodes=7, cot="none", unifol=True, leaf="#d2b93a", keep=0.45, stem="#9b8a3a",
               pods=dict(n=10, length=28, w=11, color="#8fcc5c", seeds=True, tan_frac=0.35)),
    "r8": dict(h=250, nodes=7, cot="none", unifol=False, leaf="#b98a3c", keep=0.12, stem="#7a5a30", dry=True,
               pods=dict(n=10, length=27, w=10, color="#b0802f", seeds=False, tan_frac=1.0)),
}
SKY = {"ve": "#e6f4ec", "vc": "#e6f4ec", "v1": "#e6f4ec", "vn": "#e4f3ee", "r1": "#e8f3fa", "r2": "#e8f3fa",
       "r3": "#eaf5ee", "r4": "#eaf5ee", "r5": "#eef5e3", "r6": "#f1f3de", "r7": "#f7efd6", "r8": "#f8ecd0"}


def _stem_x(y):
    return 150 + 4.5 * math.sin((GROUND - y) / 40.0)


def _f(v):
    return f"{v:.1f}"


def _trifoliate(x, y, side, scale, color):
    """Three-leaflet leaf on a petiole leaning outward from the stem at (x, y)."""
    ang = 56 * side
    L = 20 * scale + 6
    ex = x + side * L * math.sin(math.radians(56))
    ey = y - L * math.cos(math.radians(56))
    dark = "#25602c"
    s = scale
    leaflet = lambda rot, rx, ry, cy: (
        f'<g transform="rotate({rot})"><ellipse cx="0" cy="{_f(-cy * s)}" rx="{_f(rx * s)}" ry="{_f(ry * s)}" fill="{color}" stroke="{dark}" stroke-opacity=".35" stroke-width=".8"/>'
        f'<path d="M0 0 L0 {_f(-2 * cy * s * .9)}" stroke="{dark}" stroke-opacity=".35" stroke-width=".8"/></g>')
    return (f'<path d="M{_f(x)} {_f(y)} L{_f(ex)} {_f(ey)}" stroke="#4d8a3a" stroke-width="2" fill="none" stroke-linecap="round"/>'
            f'<g transform="translate({_f(ex)} {_f(ey)}) rotate({ang})">'
            + leaflet(0, 10.5, 17, 17) + leaflet(-62, 8.5, 14, 13) + leaflet(62, 8.5, 14, 13) + '</g>')


def _simple_leaf(x, y, side, color, scale=1.0):
    ang = 72 * side
    ex = x + side * 18 * scale
    ey = y - 6 * scale
    return (f'<path d="M{_f(x)} {_f(y)} L{_f(ex)} {_f(ey)}" stroke="#4d8a3a" stroke-width="2" stroke-linecap="round"/>'
            f'<g transform="translate({_f(ex)} {_f(ey)}) rotate({ang})">'
            f'<ellipse cx="0" cy="{_f(-13 * scale)}" rx="{_f(11.5 * scale)}" ry="{_f(15 * scale)}" fill="{color}" stroke="#25602c" stroke-opacity=".35" stroke-width=".8"/>'
            f'<path d="M0 0 L0 {_f(-26 * scale)}" stroke="#25602c" stroke-opacity=".35" stroke-width=".8"/></g>')


def _cotyledons(x, y, kind):
    if kind == "none":
        return ""
    if kind == "fat":
        rx, ry, col = 17, 9.5, "#b6d65b"
    elif kind == "shrunk":
        rx, ry, col = 11, 6, "#c9c05a"
    else:  # dry
        rx, ry, col = 7, 4, "#a89860"
    out = ""
    for side in (-1, 1):
        out += (f'<g transform="translate({_f(x)} {_f(y)}) rotate({side * 28})">'
                f'<ellipse cx="{side * rx * .75:.1f}" cy="0" rx="{rx}" ry="{ry}" fill="{col}" stroke="#6f8d2b" stroke-opacity=".6" stroke-width="1"/></g>')
    return out


def _flower(x, y):
    return (f'<g transform="translate({_f(x)} {_f(y)})">'
            '<circle cx="-3.2" cy="-1" r="4" fill="#9b4fc0"/><circle cx="3.2" cy="-1" r="4" fill="#9b4fc0"/>'
            '<circle cx="0" cy="3" r="3.6" fill="#b574d3"/><circle cx="0" cy="-0.5" r="1.7" fill="#fff"/></g>')


def _pod(x, y, side, length, w, color, seeds, tan):
    ang = side * 28
    col = "#c49a4c" if tan else color
    edge = "#8a6420" if tan else "#2a6a2f"
    out = (f'<g transform="translate({_f(x)} {_f(y)}) rotate({-ang})">'
           f'<rect x="{_f(-w / 2)}" y="0" width="{_f(w)}" height="{_f(length)}" rx="{_f(w / 2)}" fill="{col}" stroke="{edge}" stroke-opacity=".9" stroke-width="1.2"/>')
    if seeds:
        n = 3
        for i in range(n):
            cy = length * (i + 1) / (n + 1)
            out += f'<ellipse cx="0" cy="{_f(cy)}" rx="{_f(w * .28)}" ry="{_f(w * .32)}" fill="{edge}" fill-opacity=".28"/>'
    return out + "</g>"


def stage_svg(key):
    c = CFG[key]
    st = STAGE_BY_KEY[key]
    h = c["h"]
    ytop = GROUND - h
    stem_col = c.get("stem", "#4f9a3b")
    parts = []

    # background
    parts.append(f'<rect width="{W}" height="{H}" rx="18" fill="{SKY[key]}"/>')
    parts.append(f'<circle cx="246" cy="58" r="24" fill="#ffd966" fill-opacity=".55"/>')
    parts.append(f'<path d="M0 {GROUND - 6} Q150 {GROUND - 30} 300 {GROUND - 6} L300 {H} L0 {H} Z" fill="#8a5d3b"/>')
    parts.append(f'<path d="M0 {GROUND + 14} Q150 {GROUND - 8} 300 {GROUND + 14} L300 {H} L0 {H} Z" fill="#74492c" fill-opacity=".55"/>')
    for (sx, sy) in ((40, 312), (88, 322), (130, 306), (200, 318), (244, 308), (270, 326), (60, 330), (170, 330)):
        parts.append(f'<ellipse cx="{sx}" cy="{sy}" rx="4" ry="2" fill="#5d3a22" fill-opacity=".6"/>')

    z = c.get('zoom', 1.0)
    parts.append(f'<g transform="translate(150 {GROUND}) scale({z}) translate(-150 {-GROUND})">')
    # stem (drawn first so leaves and pods overlap it)
    pts = [(_stem_x(y), y) for y in range(GROUND - 4, int(ytop) - 1, -4)]
    d = "M" + " L".join(f"{_f(px)} {_f(py)}" for px, py in pts)
    parts.append(f'<path d="{d}" stroke="{stem_col}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')

    cot_y = ytop + 4 if key == "ve" else GROUND - 56
    parts.append(_cotyledons(_stem_x(cot_y), cot_y, c["cot"]))
    if key == "ve":
        parts.append(f'<ellipse cx="{_f(_stem_x(ytop))}" cy="{_f(ytop - 5)}" rx="4" ry="6" fill="#7cc06a"/>')

    unifol_y = None
    if c["unifol"]:
        unifol_y = max(ytop + 8, cot_y - 28)
        col = c["leaf"] if key != "vc" else "#4aa34f"
        sc = 0.8 if key == "vc" else 1.0
        parts.append(_simple_leaf(_stem_x(unifol_y), unifol_y, -1, col, sc))
        parts.append(_simple_leaf(_stem_x(unifol_y), unifol_y, 1, col, sc))

    # trifoliate nodes
    n = c["nodes"]
    node_pts = []
    if n:
        y_low = (unifol_y - 30) if unifol_y else GROUND - 90
        y_low = max(y_low, ytop + 12)
        y_high = ytop + 10
        for i in range(n):
            y = y_low if n == 1 else y_low + (y_high - y_low) * i / (n - 1)
            node_pts.append((i, y))
    keep = c.get("keep", 1.0)
    first_kept = int(round(n * (1 - keep)))
    leaf_parts, flower_pts, pod_pts = [], [], []
    for i, y in node_pts:
        side = -1 if i % 2 == 0 else 1
        scale = 1.0 - 0.38 * (i / max(n - 1, 1))
        x = _stem_x(y)
        color = c["leaf"]
        if c.get("lower_yellow") and i < n // 2:
            color = "#d3c13d"
        if i >= first_kept:
            leaf_parts.append(_trifoliate(x, y, side, scale, color))
        flower_pts.append((x, y, side))
        pod_pts.append((x, y, side))
    parts.extend(reversed(leaf_parts))

    # pods hang from the upper nodes
    pods = c.get("pods")
    if pods:
        upper = pod_pts[-5:] if len(pod_pts) >= 5 else pod_pts
        total = pods["n"]
        tan_n = int(round(total * pods.get("tan_frac", 0)))
        k = 0
        slot = 0
        while k < total:
            x, y, side = upper[slot % len(upper)]
            tier = slot // len(upper)
            sd = side if tier % 2 == 0 else -side
            tan = k < tan_n if c.get("dry") else (k % 3 == 0 and k // 3 < tan_n)
            parts.append(_pod(x + sd * (8 + 4 * tier), y + 4 + 5 * tier, sd, pods["length"], pods["w"],
                              pods["color"], pods.get("seeds", False), tan))
            k += 1
            slot += 1

    # flowers on the top nodes
    nf = c.get("flowers", 0)
    if nf:
        upper = flower_pts[-4:] if len(flower_pts) >= 4 else flower_pts
        for j in range(nf):
            x, y, side = upper[(len(upper) - 1 - j) % len(upper)]
            ring = j // len(upper)
            fx = x + (-side if ring % 2 else side) * (8 + 7 * (ring // 1))
            fy = y - 3 + 7 * ring
            parts.append(_flower(fx, fy))

    # fallen leaves on the ground at full maturity
    if c.get("dry"):
        for (lx, ly, r) in ((95, 300, -20), (205, 306, 25), (120, 316, 10)):
            parts.append(f'<ellipse cx="{lx}" cy="{ly}" rx="9" ry="4.5" fill="#b98a3c" transform="rotate({r} {lx} {ly})"/>')

    parts.append('</g>')

    # badge
    code = st["code"]
    bw = 38 + 11 * max(len(code) - 2, 0)
    parts.append(f'<rect x="12" y="12" width="{bw}" height="30" rx="9" fill="#2e7d32"/>')
    parts.append(f'<text x="{12 + bw / 2:.0f}" y="33" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="{16 if len(code) <= 3 else 14}" font-weight="700" fill="#ffffff">{code}</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Illustration of a soybean plant at stage {code}, {st["name"]}">' + "".join(parts) + "</svg>")


def node_guide_svg():
    """Diagram for the form: a plant with its main-stem nodes numbered."""
    parts = [f'<rect width="{W}" height="{H}" rx="18" fill="#eef6ee"/>',
             f'<path d="M0 {GROUND - 6} Q150 {GROUND - 30} 300 {GROUND - 6} L300 {H} L0 {H} Z" fill="#8a5d3b"/>']
    top = 62
    pts = [(_stem_x(y), y) for y in range(GROUND - 4, top - 1, -4)]
    parts.append('<path d="M' + " L".join(f"{_f(px)} {_f(py)}" for px, py in pts) + '" stroke="#4f9a3b" stroke-width="5" fill="none" stroke-linecap="round"/>')
    ys = [238, 192, 146, 100, 70]
    for i, y in enumerate(ys):
        side = -1 if i % 2 == 0 else 1
        parts.append(_trifoliate(_stem_x(y), y, side, 1.0 - 0.1 * i, "#3f9a45"))
    for i, y in enumerate(ys):
        x = _stem_x(y)
        parts.append(f'<circle cx="{_f(x)}" cy="{y}" r="10" fill="#fff" stroke="#2e7d32" stroke-width="2"/>')
        parts.append(f'<text x="{_f(x)}" y="{y + 5}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="700" fill="#2e7d32">{i + 1}</text>')
    parts.append('<text x="150" y="30" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" fill="#2b5d31">Each numbered dot is one node</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
            'aria-label="Diagram of a soybean main stem with five nodes numbered one to five">' + "".join(parts) + "</svg>")


if __name__ == "__main__":
    import cairosvg
    from PIL import Image
    imgs = []
    for s in STAGES:
        cairosvg.svg2png(bytestring=stage_svg(s["key"]).encode(), write_to=f"/tmp/{s['key']}.png", output_width=300)
        imgs.append(Image.open(f"/tmp/{s['key']}.png"))
    sheet = Image.new("RGB", (300 * 4, 340 * 3), "white")
    for i, im in enumerate(imgs):
        sheet.paste(im, ((i % 4) * 300, (i // 4) * 340))
    sheet.save("/tmp/contact.png")
    print("contact sheet written")
