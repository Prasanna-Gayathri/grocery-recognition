import base64
import html
import requests
import streamlit as st

st.set_page_config(page_title="SafeScan | Grocery Allergen and Nutrition Checker",
                   page_icon="🛒", layout="wide")

ALLERGENS = ["Milk", "Gluten", "Peanut", "Tree nut", "Soy", "Egg", "Fish", "Shellfish", "Sesame"]
GRADE_COL = {"A": ("#2E8B3E", "#fff"), "B": ("#8BBF3A", "#10200A"), "C": ("#F2C21A", "#2B2200"),
             "D": ("#EE8B24", "#2B1400"), "E": ("#D9382B", "#fff")}
BAR_NAMES = {"energy_pts": ("Energy", 10, 0), "sugar_pts": ("Sugars", 10, 0), "satfat_pts": ("Saturated fat", 10, 0),
             "sodium_pts": ("Sodium", 10, 0), "fibre_pts": ("Fibre (helps)", 5, 1), "fruit_pts": ("Fruit, veg, nuts (helps)", 5, 1)}
NUT_NAMES = {"energy_kcal_100g": ("Energy", "kcal"), "sugars_g_100g": ("Sugars", "g"),
             "saturated_fat_g_100g": ("Saturated fat", "g"), "sodium_mg_100g": ("Sodium", "mg"),
             "fibre_g_100g": ("Fibre", "g"), "protein_g_100g": ("Protein", "g"), "fruit_veg_nuts_pct": ("Fruit, veg, nuts", "%")}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Nunito:wght@400;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input { font-family: 'Nunito', sans-serif; }
h1, h2, h3, .poppins { font-family: 'Poppins', sans-serif !important; letter-spacing: -0.02em; }
.block-container { padding-top: 1rem; max-width: 1150px; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.topbar { display:flex; align-items:center; justify-content:space-between; padding: 6px 4px 18px; }
.brand { font-family:'Poppins',sans-serif; font-weight:700; font-size:24px; color:#1B5E20; }
.brand span { color:#F28C28; }
.hero { background: linear-gradient(120deg,#1B5E20 0%,#2E7D32 55%,#7DB65A 100%); border-radius: 26px;
        padding: 54px 48px; color:#fff; position:relative; overflow:hidden; }
.hero:after { content:"🥦  🥛  🍞  🧀  🍎"; position:absolute; right:30px; bottom:14px; font-size:34px; opacity:.28; letter-spacing:8px; }
.hero h1 { color:#fff; font-size: 46px; line-height:1.08; margin:0 0 14px; max-width: 640px; }
.hero p { font-size:18px; line-height:1.6; max-width: 560px; margin:0 0 20px; color:#EAF6E3; }
.pill { display:inline-block; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.35); color:#fff;
        border-radius:999px; padding:7px 15px; font-size:14px; font-weight:600; margin:0 8px 8px 0; }
.card { background:#fff; border:1px solid #DDE8D3; border-radius:20px; padding:24px; height:100%; }
.card h4 { margin:10px 0 6px; font-family:'Poppins',sans-serif; font-size:18px; color:#1B2A1B; }
.card p { margin:0; color:#4F6450; line-height:1.55; font-size:15px; }
.num { width:38px; height:38px; border-radius:11px; background:#E3F1DA; color:#1B5E20; display:flex; align-items:center;
       justify-content:center; font-weight:700; font-family:'Poppins',sans-serif; }
.section-title { font-family:'Poppins',sans-serif; font-weight:700; font-size:30px; color:#1B2A1B; margin: 38px 0 6px; }
.section-sub { color:#4F6450; font-size:16px; margin-bottom:16px; }
.badge { display:inline-block; border-radius:999px; padding:8px 15px; font-size:14px; font-weight:700; margin:0 8px 8px 0; }
.badge.f { background:#B93815; color:#fff; } .badge.n { background:#fff; border:1px solid #C9D8BF; color:#1B2A1B; font-weight:600; }
.verdict { border-radius:22px; padding:28px; border:1px solid; margin-bottom:18px; }
.verdict .lbl { font-size:13px; font-weight:700; letter-spacing:.07em; }
.verdict .big { font-family:'Poppins',sans-serif; font-size:40px; font-weight:700; line-height:1.05; margin:8px 0 8px; }
.verdict p { font-size:16.5px; line-height:1.55; margin:0 0 14px; }
.v-CONFLICT { background:#FBEAE4; border-color:#F0C4B5; color:#8F2A0F; }
.v-SAFE { background:#E4F3E7; border-color:#B9DDC0; color:#17612A; }
.v-UNCERTAIN { background:#FFF4DB; border-color:#EBD79A; color:#7A5200; }
.row { background:#fff; color:#1B2A1B; border-radius:12px; padding:13px 16px; display:flex; justify-content:space-between;
       gap:8px; flex-wrap:wrap; margin-top:8px; font-size:15px; }
.scale { display:flex; gap:6px; align-items:flex-end; margin:6px 0 4px; }
.g { flex:1; height:44px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:700; opacity:.4; }
.g.on { flex:1.5; height:66px; font-size:30px; opacity:1; border-radius:12px; box-shadow:0 10px 22px -10px rgba(0,0,0,.45); }
.bar { margin-top:12px; font-size:14.5px; } .bar .h { display:flex; justify-content:space-between; }
.bar .t { height:8px; background:#E4EDDD; border-radius:99px; margin-top:5px; } .bar .t i { display:block; height:8px; border-radius:99px; background:#C2410C; }
.bar.good .t i { background:#2E7D32; }
.note { background:#EAF3E3; border-radius:12px; padding:12px 14px; font-size:14px; color:#3F5A3F; margin-top:14px; line-height:1.5; }
.tbl div { display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #E4EDDD; font-size:15px; }
.dark { background:#1B3D1F; color:#fff; border-radius:20px; padding:24px; }
.dark .it { margin-top:12px; font-size:14.5px; line-height:1.5; }
.dark b { color:#BFE8A8; }
.disclaimer { color:#5B6E5B; font-size:13px; margin-top:26px; line-height:1.6; border-top:1px solid #DDE8D3; padding-top:14px; }
div.stButton > button { border-radius:12px; font-weight:700; padding:.6rem 1.2rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def esc(x):
    return html.escape(str(x if x is not None else ""))


def pretty(s):
    return str(s or "").replace("_", " ").lower().capitalize()


# ---------------------------------------------------------------- sample report (works without a server)
SAMPLE = {
    "category": "BISCUITS", "confidence": 0.91, "confidence_set": ["BISCUITS", "CHOCOLATE_CANDY"], "product_name": None,
    "verdict": "CONFLICT", "grounding_hit": True, "highlight_count": 2, "highlighted_image_b64": None,
    "per_allergen": [{"allergen": "milk", "status": "found"}, {"allergen": "gluten", "status": "found"},
                     {"allergen": "peanut", "status": "not_found"}],
    "ontology_matches": [{"term": "milk solids", "category": "MILK", "allergen": "milk"},
                         {"term": "wheat flour", "category": "GLUTEN_WHEAT", "allergen": "gluten"}],
    "details": "This product lists milk solids and wheat flour. Both conflict with your milk and gluten allergies. "
               "No peanut ingredients were visible in the text that was read. Text recognition can miss words, "
               "so confirm on the physical label before you eat it.",
    "nutrients": {"energy_kcal_100g": 450, "sugars_g_100g": 20, "saturated_fat_g_100g": 5, "sodium_mg_100g": 300,
                  "fibre_g_100g": 2, "protein_g_100g": 6, "fruit_veg_nuts_pct": 0},
    "nutriscore": {"grade": "D", "final_score": 14, "negative_points": 16, "positive_points": 2, "data_complete": True,
                   "missing_fields": [], "breakdown": {"energy_pts": 5, "sugar_pts": 4, "satfat_pts": 4,
                                                       "sodium_pts": 3, "fibre_pts": 2, "fruit_pts": 0}},
}


# ---------------------------------------------------------------- API call
def call_api(url, key, front, back, allergies):
    files = {"front": (front.name, front.getvalue(), front.type or "image/jpeg"),
             "back": (back.name, back.getvalue(), back.type or "image/jpeg")}
    try:
        r = requests.post(url.rstrip("/") + "/analyze", files=files,
                          data={"allergies": ",".join(a.lower() for a in allergies)},
                          headers={"x-api-key": key}, timeout=300)
    except requests.exceptions.RequestException:
        return None, "Could not reach the SafeScan server. Check the API URL and that the Colab cell is still running."
    if r.status_code == 401:
        return None, "The access key is wrong. Copy the key printed in Colab again."
    if r.status_code != 200:
        try:
            detail = r.json().get("detail", "")
        except Exception:
            detail = ""
        return None, f"The server returned an error ({r.status_code}). {detail} If the AI quota is used up, try again later."
    return r.json(), None


# ---------------------------------------------------------------- result page
def render_result(d, sample=False):
    v = d.get("verdict", "UNCERTAIN")
    title = {"CONFLICT": "Conflict found", "SAFE": "Looks safe", "UNCERTAIN": "Uncertain"}.get(v, "Uncertain")
    pa = d.get("per_allergen") or []
    found = sum(1 for a in pa if a.get("status") == "found")
    sub = {"CONFLICT": f"{found} of your {len(pa)} allergens appear in the ingredients. Do not eat this product if these allergies apply to you.",
           "SAFE": "No conflicts with your allergies were found in the text that was read. Text recognition can miss words, so still check the label.",
           "UNCERTAIN": "The check could not give a firm answer. Please read the physical label."}.get(v)

    top = st.columns([3, 1])
    with top[0]:
        st.markdown('<div class="brand">🛒 Safe<span>Scan</span></div>', unsafe_allow_html=True)
    with top[1]:
        if st.button("New scan", use_container_width=True):
            st.session_state.pop("result", None)
            st.session_state.pop("sample", None)
            st.rerun()
    if sample:
        st.markdown('<span class="badge n">Sample report</span>', unsafe_allow_html=True)

    cat = pretty(d.get("category"))
    others = [pretty(c) for c in (d.get("confidence_set") or []) if pretty(c) != cat]
    conf = d.get("confidence")
    meta = f'<span class="badge f" style="background:#1B5E20">{esc(cat)}</span>'
    if others:
        meta += "Also possible: " + "".join(f'<span class="badge n">{esc(o)}</span>' for o in others)
    if conf is not None:
        meta += f' <span style="color:#4F6450">Confidence {round(conf*100)}%</span>'
    st.markdown(f'<h2 style="margin:4px 0 6px">{esc(d.get("product_name") or "Your product report")}</h2>{meta}',
                unsafe_allow_html=True)
    st.write("")

    left, right = st.columns([1.6, 1])
    with left:
        badges = "".join(f'<span class="badge {"f" if a.get("status")=="found" else "n"}">{esc(pretty(a.get("allergen")))}: '
                         f'{"found" if a.get("status")=="found" else "not found"}</span>' for a in pa)
        rows = "".join(f'<div class="row"><span><b>{esc(m.get("term"))}</b> on the label</span>'
                       f'<span style="color:#B93815;font-weight:700">counts as {esc(pretty(m.get("category")))}</span></div>'
                       for m in d.get("ontology_matches") or [])
        st.markdown(f'<div class="verdict v-{v}"><div class="lbl">ALLERGEN VERDICT</div><div class="big">{title}</div>'
                    f'<p>{esc(sub)}</p>{badges}{rows}</div>', unsafe_allow_html=True)

        st.markdown("### Back label, flagged")
        if d.get("highlighted_image_b64"):
            st.image(base64.b64decode(d["highlighted_image_b64"]), use_container_width=True,
                     caption=f'{d.get("highlight_count", 0)} flagged word(s) boxed in red')
        else:
            st.info("No label image in this report. A live scan shows your back-of-pack photo with the flagged words boxed in red.")

        st.markdown("### In plain words")
        st.write(d.get("details", ""))

    with right:
        ns = d.get("nutriscore") or {}
        g = ns.get("grade", "N/A")
        head = '<div class="card"><b style="color:#2E7D32;letter-spacing:.06em;font-size:13px">NUTRITION GRADE</b>'
        if g == "N/A":
            st.markdown(head + '<h3>Not available</h3><div class="note">The nutrition table could not be read, so no grade was calculated.</div></div>',
                        unsafe_allow_html=True)
        else:
            scale = "".join(f'<div class="g {"on" if x == g else ""}" style="background:{GRADE_COL[x][0]};color:{GRADE_COL[x][1]}">{x}</div>'
                            for x in "ABCDE")
            bd = ns.get("breakdown") or {}
            bars = "".join(f'<div class="bar {"good" if good else ""}"><div class="h"><span>{n}</span><span style="color:#4F6450">{bd[k]} of {mx}</span></div>'
                           f'<div class="t"><i style="width:{bd[k]/mx*100}%"></i></div></div>'
                           for k, (n, mx, good) in BAR_NAMES.items() if bd.get(k) is not None)
            miss = ""
            if ns.get("missing_fields") and not ns.get("data_complete"):
                miss = (f'<div class="note">Incomplete data: {esc(", ".join(ns["missing_fields"]))} were not found on the label '
                        f'and are counted as 0, so this grade is only a rough guide.</div>')
            st.markdown(head + f'<div class="scale" style="margin-top:14px">{scale}</div><h3 style="margin:12px 0 2px">Grade {g}</h3>'
                        f'<div style="color:#4F6450;font-size:14.5px">Score {ns.get("final_score")} = {ns.get("negative_points")} negative points minus {ns.get("positive_points")} positive points</div>'
                        f'{bars}{miss}</div>', unsafe_allow_html=True)

        nut = d.get("nutrients") or {}
        nrows = "".join(f'<div><span>{n}</span><b>{esc(nut[k])} {u}</b></div>' for k, (n, u) in NUT_NAMES.items() if nut.get(k) is not None)
        if nrows:
            st.write("")
            st.markdown(f'<div class="card"><h4 style="margin-top:0">Per 100 g</h4><div class="tbl">{nrows}</div></div>', unsafe_allow_html=True)

        n_ont = len(d.get("ontology_matches") or [])
        st.write("")
        st.markdown(f'<div class="dark"><h4 style="margin:0;color:#fff;font-family:Poppins">How this was decided</h4>'
                    f'<div class="it">✔ <b>Allergen rules</b> {"matched " + str(n_ont) + " word(s) on your list." if n_ont else "found no matching words."}</div>'
                    f'<div class="it">✔ <b>AI text reading</b> checked the same label text.</div>'
                    f'<div class="it">✔ <b>Open Food Facts</b> {"record found for this product." if d.get("grounding_hit") else "had no matching record, so the label text was used alone."}</div></div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="disclaimer">Decision support, not medical advice. Text recognition can miss or misread words, '
                'so always check the physical label. The nutrition grade follows the published Nutri-Score method for general foods.</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------- landing page
def render_landing():
    st.markdown('<div class="topbar"><div class="brand">🛒 Safe<span>Scan</span></div>'
                '<div style="color:#4F6450;font-weight:600">Allergen-aware grocery scanning</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero"><span class="pill">Allergens</span><span class="pill">Nutri-Score</span>'
                '<span class="pill">Highlighted label</span><h1>Know what is in your food before you buy it.</h1>'
                '<p>Take two photos of any grocery pack, the front and the back. SafeScan recognises the product, '
                'checks the ingredients against your allergies and grades its nutrition.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Scan a product</div><div class="section-sub">Add both photos, choose your allergies, and press Analyse.</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        front = st.file_uploader("Front of pack (identifies the product)", type=["jpg", "jpeg", "png"], key="front")
        if front:
            st.image(front, use_container_width=True)
    with c2:
        back = st.file_uploader("Back of pack (ingredients and nutrition)", type=["jpg", "jpeg", "png"], key="back")
        if back:
            st.image(back, use_container_width=True)
    allergies = st.multiselect("Your allergies", ALLERGENS, default=["Milk", "Gluten", "Peanut"])

    b1, b2, _ = st.columns([1, 1, 2])
    with b1:
        go = st.button("Analyse product", type="primary", use_container_width=True, disabled=not (front and back))
    with b2:
        if st.button("View sample report", use_container_width=True):
            st.session_state["result"] = SAMPLE
            st.session_state["sample"] = True
            st.rerun()
    if not (front and back):
        st.caption("Upload both photos to enable Analyse.")

    if go:
        url, key = st.session_state.get("api_url", ""), st.session_state.get("api_key", "")
        if not url or not key:
            st.error("Connect to the SafeScan server first, using the sidebar on the left.")
        else:
            with st.spinner("Analysing your product. This can take up to a minute..."):
                result, err = call_api(url, key, front, back, allergies)
            if err:
                st.error(err)
            else:
                st.session_state["result"] = result
                st.session_state["sample"] = False
                st.rerun()

    st.markdown('<div class="section-title">How it works</div>', unsafe_allow_html=True)
    h1, h2_, h3_ = st.columns(3)
    for col, (n, t, p) in zip((h1, h2_, h3_), [
        ("1", "Scan front and back", "One photo of the front and one of the ingredient and nutrition panel."),
        ("2", "Recognise and read", "The front photo and its text identify the product. OCR reads the back label word by word."),
        ("3", "Get your verdict", "A safe, conflict or uncertain verdict for your allergies, plus an A to E nutrition grade.")]):
        col.markdown(f'<div class="card"><div class="num">{n}</div><h4>{t}</h4><p>{p}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="disclaimer">SafeScan: an LLM-driven multimodal approach to fine-grained product recognition with allergen detection. '
                'Decision support, not medical advice. Always check the physical label.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- sidebar: connection to the Colab brain
with st.sidebar:
    st.markdown("### Server connection")
    st.caption("Run the last cell of Notebook 6 in Colab. Paste the API URL and access key it prints.")
    st.session_state["api_url"] = st.text_input("API URL", value=st.session_state.get("api_url", ""),
                                                placeholder="https://xxxx.trycloudflare.com")
    st.session_state["api_key"] = st.text_input("Access key", value=st.session_state.get("api_key", ""), type="password")
    if st.button("Test connection"):
        try:
            r = requests.get(st.session_state["api_url"].rstrip("/") + "/health", timeout=15)
            st.success("Connected.") if r.ok else st.error(f"Server answered {r.status_code}.")
        except Exception:
            st.error("Could not reach the server.")

if st.session_state.get("result"):
    render_result(st.session_state["result"], st.session_state.get("sample", False))
else:
    render_landing()
