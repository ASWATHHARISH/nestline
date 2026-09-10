"""Nestline reviewer preview for PC00, P10 and PP01.

Run with: streamlit run streamlit_app.py
"""

from pathlib import Path

import streamlit as st

from app.schemas.ingestion import Stage1ReviewLedger
from app.services.foundation import read_catalogues
from app.services.review_preview import build_review_preview, comparison_gate
from scripts.validate_content import load_bundle

ROOT = Path(__file__).resolve().parent
PROFILE_LABELS = {
    "PC00": "PC00 · Possible pregnancy",
    "P10": "P10 · Pregnancy week 10",
    "PP01": "PP01 · First week after birth",
}
SCENARIOS = {
    "PC00": {
        "missing": ("Possible pregnancy · no result inferred", frozenset(), frozenset()),
    },
    "P10": {
        "missing": ("Pregnancy confirmed · movement facts missing",
                    frozenset({"pregnancy_confirmed"}), frozenset()),
        "cleared": ("Care professional cleared activity · no restriction/warning",
                    frozenset({"pregnancy_confirmed", "exercise_clearance"}),
                    frozenset({"movement_restriction", "current_warning_symptom"})),
        "restricted": ("Movement restriction recorded",
                       frozenset({"pregnancy_confirmed", "movement_restriction"}),
                       frozenset({"current_warning_symptom"})),
    },
    "PP01": {
        "missing": ("Feeding and delivery details missing", frozenset(), frozenset()),
        "uncomplicated": ("Breastfeeding · straightforward birth · feels ready",
                          frozenset({"breastfeeding", "uncomplicated_delivery",
                                     "feels_ready_for_gentle_activity"}),
                          frozenset({"complicated_delivery_or_caesarean",
                                     "movement_restriction", "current_warning_symptom"})),
        "caesarean": ("Breastfeeding · caesarean recorded",
                     frozenset({"breastfeeding", "complicated_delivery_or_caesarean"}),
                     frozenset({"uncomplicated_delivery", "current_warning_symptom"})),
    },
}
SLOT_LABELS = {
    "what_may_change": "What may change",
    "nutrition_focus": "Diet",
    "movement_focus": "Movement",
    "wellbeing_focus": "Mental wellbeing",
    "symptom_education": "Symptoms and safety",
    "preparation": "Preparation",
    "consider": "Do",
    "avoid": "Don't",
    "ask_a_professional": "Ask a professional",
}


@st.cache_resource
def load_review_data():
    bundle = load_bundle(ROOT / "data")
    ledger = Stage1ReviewLedger.model_validate_json(
        (ROOT / "data/reviews/ingestion_decisions.json").read_text(encoding="utf-8"))
    return bundle, ledger, read_catalogues(ROOT / "data")


def render_card(card: dict) -> None:
    status = {
        "shown": "Eligible for this fictional scenario",
        "needs_information": "Needs confirmed information",
        "not_applicable": "Not applicable to this fictional scenario",
    }[card["state"]]
    with st.container(border=True):
        st.markdown(f"**{status}**")
        st.write(card["text"])
        if card["state"] != "shown":
            st.caption(card["state_reason"])
        for source in card["sources"]:
            st.link_button(f"Source · {source['source_id']}", source["url"])
        with st.expander("Review and condition details"):
            st.write("Accepted roles: " + ", ".join(card["accepted_roles"]))
            st.write("Pending roles: " + ", ".join(card["pending_roles"]))
            st.write("Required confirmed facts: "
                     + (", ".join(card["required_conditions"]) or "none"))
            st.write("Required confirmed absences: "
                     + (", ".join(card["excluded_conditions"]) or "none"))
            st.write("Evidence: " + ", ".join(card["evidence_ids"]))


def render_slots(preview: dict, slots: tuple[str, ...]) -> None:
    displayed = False
    for slot in slots:
        cards = preview["cards_by_slot"][slot]
        if not cards:
            continue
        displayed = True
        st.subheader(SLOT_LABELS[slot])
        for card in cards:
            render_card(card)
    if not displayed:
        st.info("No proposed card for this section. The system does not invent one to fill the gap.")


st.set_page_config(page_title="Nestline · reviewer preview", page_icon="🌿", layout="wide")
st.markdown("""
<style>
    .stApp { background: #fbfaf7; }
    [data-testid="stMetric"] { background: white; border: 1px solid #e8e3dc;
        padding: 1rem; border-radius: 18px; }
    [data-testid="stMetricValue"] { font-size: 1.55rem; }
    [data-testid="stSidebar"] { background: #f1f7f3; }
    .review-banner { background: #fff1cc; border: 1px solid #e6b94f; color: #5e4300;
        padding: .85rem 1rem; border-radius: 14px; margin-bottom: 1rem; font-weight: 650; }
    .brand { color: #176b55; font-size: 1rem; font-weight: 800; letter-spacing: .08em; }
</style>
""", unsafe_allow_html=True)

bundle, ledger, catalogues = load_review_data()
requested_profile = st.query_params.get("profile", "PC00")
if requested_profile not in PROFILE_LABELS:
    requested_profile = "PC00"
profile_ids = list(PROFILE_LABELS)
profile_id = st.sidebar.selectbox(
    "Review profile", profile_ids, index=profile_ids.index(requested_profile),
    format_func=PROFILE_LABELS.get)
scenario_keys = list(SCENARIOS[profile_id])
requested_scenario = st.query_params.get("scenario", "missing")
if requested_scenario not in scenario_keys:
    requested_scenario = scenario_keys[0]
scenario_key = st.sidebar.selectbox(
    "Fictional condition state", scenario_keys,
    index=scenario_keys.index(requested_scenario),
    format_func=lambda key: SCENARIOS[profile_id][key][0])
scenario_label, confirmed, absent = SCENARIOS[profile_id][scenario_key]
preview = build_review_preview(bundle, ledger, profile_id, confirmed=confirmed, absent=absent)
gate = comparison_gate(catalogues)

st.markdown('<div class="brand">NESTLINE · KAJAL REVIEW</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="review-banner">Draft reviewer preview · hidden from public users, embeddings and live RAG · '
    'clinical, India-localisation and licence decisions are still pending</div>',
    unsafe_allow_html=True)
st.title(preview["title"])
st.caption(f"Profile {profile_id} · Fictional scenario: {scenario_label}")

columns = st.columns(4)
for column, (label, value, help_text) in zip(columns, preview["metrics"], strict=True):
    column.metric(label, value, help=help_text)
if profile_id == "P10":
    st.caption("*A general source estimate for review; it is not a measurement from a user's scan.")

if gate["safe"]:
    st.info(f"🔒 All {gate['total']} baby-size comparisons remain hidden. Verified measurements and "
            "object dimensions have not been recorded.")
else:
    st.error("Baby-size comparison gate needs engineering review before this preview can continue.")

overview, diet, movement, wellbeing, actions = st.tabs(
    ["This week", "Diet", "Movement", "Mental wellbeing", "Do, don't & ask"])
with overview:
    render_slots(preview, ("what_may_change", "symptom_education", "preparation"))
with diet:
    render_slots(preview, ("nutrition_focus",))
with movement:
    render_slots(preview, ("movement_focus",))
with wellbeing:
    render_slots(preview, ("wellbeing_focus",))
with actions:
    render_slots(preview, ("consider", "avoid", "ask_a_professional"))

with st.sidebar:
    st.divider()
    st.caption("Review state")
    st.write("✅ Product — Kajal")
    st.write("✅ Content — Kajal")
    st.write("◻ Clinical — pending")
    st.write("◻ India localisation — pending")
    st.write("◻ Licence — pending")
    st.caption("This app reads draft records for review only. It does not publish content.")
