from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).parent
ICON = HERE / "graduation-hat.png"

st.set_page_config(page_title="Fuzzy Course Assistant", page_icon=str(ICON), layout="wide")

# ---------- Style: bigger text, wider sidebar, status pills ----------
st.markdown(
    """
    <style>
      html { font-size: 18px; }
      .block-container {padding-top: 2.2rem; max-width: 1300px;}
      section[data-testid="stSidebar"] {width: 360px !important;}
      .subtitle {color: #6b6b6b; margin-top: -0.6rem; font-size: 1.05rem;}
      div[data-testid="stMetric"] {background: #F5F5F4; border-radius: 12px; padding: 12px 16px;}
      .tag {display:inline-block; background:#FFF4D6; color:#7A5800; border-radius:999px;
            padding:2px 10px; margin:2px 4px 2px 0; font-size:0.85rem;}
      .row {display:flex; justify-content:space-between; align-items:center; margin: 0.6rem 0 0.15rem 0;}
      .row b {font-weight:600;}
      .pill {border-radius:999px; padding:1px 10px; font-size:0.75rem; font-weight:600;}
      .done {background:#E3F4E6; color:#1F6B33;}
      .todo {background:#FFF1CC; color:#7A5800;}
      .open {background:#EDEDED; color:#555;}
      .small {color:#6b6b6b; font-size:0.82rem; margin-bottom:0.2rem;}
      .missing {color:#9A3412; font-size:0.9rem;}
      .marks {display:flex; justify-content:space-between; color:#9a9a9a; font-size:0.72rem;
              margin:-0.9rem 0.4rem 0.9rem 0.4rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Data ----------
TRACKS = {
    "T0": "General",
    "T1": "Distributed Software Systems",
    "T2": "Security",
    "T3": "Visual Computing",
    "T4": "Theory and Logic",
    "T5": "Information Systems and Decision Support",
    "T6": "Data Science",
}
CITIES = ["Bern", "Fribourg", "Neuchâtel"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
ASSESSMENTS = ["Written exam", "Oral exam", "Mixed", "Continuous evaluation"]
UNITS_NEEDED, ECTS_PER_UNIT, MIN_TRACKS, SPEC_UNITS = 12, 5, 3, 5

# Preferences are degrees on a continuous 0-10 scale. The words are only guide marks;
# the fuzzy engine turns the number into membership degrees of Low / Medium / High.
MARKS = ["Not at all", "Low", "Medium", "High", "Very much"]
HIGH = 7.0  # from here a track counts as a favourite


def word_for(v):
    return MARKS[min(int(v / 2.0001), 4)]


def degree_slider(label, key, default=5.0, disabled=False):
    v = st.slider(label, 0.0, 10.0, default, 0.1, key=key, disabled=disabled, format="%.1f")
    st.markdown(
        '<div class="marks">' + "".join(f"<span>{m}</span>" for m in MARKS) + "</div>",
        unsafe_allow_html=True,
    )
    return v


@st.cache_data
def load_courses():
    df = pd.read_csv(HERE / "courses.csv", dtype=str).fillna("")
    df["track_list"] = df["tracks"].str.split(";")
    df["lecturer_list"] = df["lecturers"].str.split(";")
    df["label"] = df["code"] + " – " + df["name"]
    return df


courses = load_courses()
all_profs = sorted({p for ps in courses["lecturer_list"] for p in ps if p})
catalog = courses.drop_duplicates("label").set_index("label")

# ---------- Header ----------
logo, title = st.columns([1, 12], vertical_alignment="center")
logo.image(str(ICON), width=80)
with title:
    st.title("Fuzzy Course Selection Assistant")
    st.markdown(
        '<p class="subtitle">Swiss Joint Master in Computer Science · Bern · Fribourg · Neuchâtel</p>',
        unsafe_allow_html=True,
    )

# ---------- Form ----------
left, right = st.columns([3, 2], gap="large")

with left:
    tab_prog, tab_sem, tab_tracks, tab_place, tab_eval = st.tabs(
        ["1 · Your progress", "2 · This semester", "3 · Tracks", "4 · Place & days", "5 · Assessment"]
    )

    with tab_prog:
        st.caption("Tell us where you are in the master. Your checklist on the left updates automatically.")
        name = st.text_input("Your name (optional)", placeholder="e.g. Alex")
        study_sem = st.selectbox(
            "Which master semester are you in? *",
            ["1st semester", "2nd semester", "3rd semester", "4th semester or later"],
            index=None,
            placeholder="Choose your semester",
        )
        completed = st.multiselect(
            "Teaching units you have already completed",
            list(catalog.index),
            placeholder="Search by course name or code",
            help="These courses will not be recommended again.",
        )
        other_units = st.number_input(
            "Other completed units not in the list", 0, 12, 0,
            help="For example units from earlier years that are no longer offered.",
        )
        thesis = st.selectbox("Master's thesis", ["Not started", "In progress", "Done"])

    with tab_sem:
        semester = st.radio(
            "Which semester are you planning? *",
            ["A2026", "S2027"],
            format_func=lambda s: "Autumn 2026" if s == "A2026" else "Spring 2027",
            horizontal=True,
            index=None,
        )
        c1, c2 = st.columns(2)
        n_lectures = c1.number_input("How many lectures? *", 0, 8, 3)
        n_seminars = c2.number_input("How many seminars? *", 0, 4, 1)

    with tab_tracks:
        st.caption("How interested are you in each track? Move the slider anywhere: it's a degree, "
                   "not a fixed answer. Put at least one track at High or above. *")
        tracks = {}
        for code, label in TRACKS.items():
            v = degree_slider(f"**{code}** – {label}", key=f"tr_{code}")
            tracks[code] = {"value": v, "term": word_for(v)}

    def place_row(label, key, cant_text):
        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        excluded = c2.checkbox(cant_text, key=f"x_{key}")
        with c1:
            v = degree_slider(label, key=key, disabled=excluded)
        return {"value": None if excluded else v, "term": cant_text if excluded else word_for(v),
                "excluded": excluded}

    with tab_place:
        st.caption("How much do you like each city and day? **Can't go** / **Can't attend** removes "
                   "courses completely. The sliders only change the ranking.")
        st.markdown("##### Cities")
        cities = {c: place_row(c, f"city_{c}", "Can't go") for c in CITIES}
        st.markdown("##### Days")
        days = {d: place_row(d, f"day_{d}", "Can't attend") for d in DAYS}

    with tab_eval:
        st.caption("How much do you like each assessment method?")
        assessment = {}
        for a in ASSESSMENTS:
            v = degree_slider(a, key=f"as_{a}")
            assessment[a] = {"value": v, "term": word_for(v)}
        profs = st.multiselect("Preferred professors (optional)", all_profs, placeholder="Choose professors")

# ---------- Degree progress (computed from tab 1) ----------
done_rows = catalog.loc[completed] if completed else catalog.iloc[0:0]
units_done = len(done_rows) + other_units
units_planned = n_lectures + n_seminars
track_counts = {t: 0 for t in TRACKS}
for tl in done_rows["track_list"]:
    for t in tl:
        track_counts[t] += 1
tracks_covered = [t for t, n in track_counts.items() if n > 0]
# Specialisation is not asked: we show the track the student is closest to.
spec_code = max(track_counts, key=track_counts.get) if tracks_covered else None


def pill(ok, text_ok="Done", text_no="To do"):
    cls, txt = ("done", text_ok) if ok else ("todo", text_no)
    return f'<span class="pill {cls}">{txt}</span>'


def row(label, value, ok):
    st.markdown(f'<div class="row"><b>{label}</b>{pill(ok)}</div><div class="small">{value}</div>',
                unsafe_allow_html=True)


with st.sidebar:
    st.subheader("Your degree checklist")
    st.markdown(f'<div class="small">{study_sem or "Fill in tab 1 to see your progress"}</div>',
                unsafe_allow_html=True)

    row("Teaching units", f"{units_done} of {UNITS_NEEDED} completed", units_done >= UNITS_NEEDED)
    st.progress(min(units_done / UNITS_NEEDED, 1.0))

    row("ECTS from units", f"{units_done * ECTS_PER_UNIT} of {UNITS_NEEDED * ECTS_PER_UNIT} ECTS",
        units_done >= UNITS_NEEDED)
    st.progress(min(units_done / UNITS_NEEDED, 1.0))

    covered_txt = ", ".join(tracks_covered) if tracks_covered else "none yet"
    row("At least 3 tracks", f"{len(tracks_covered)} of {MIN_TRACKS}: {covered_txt}",
        len(tracks_covered) >= MIN_TRACKS)

    if spec_code:
        n_spec = track_counts[spec_code]
        row("Specialisation (optional)",
            f"Closest track: {spec_code} {TRACKS[spec_code]}, {n_spec} of {SPEC_UNITS} units",
            n_spec >= SPEC_UNITS)
        st.progress(min(n_spec / SPEC_UNITS, 1.0))

    thesis_ok = thesis == "Done"
    st.markdown(
        f'<div class="row"><b>Master\'s thesis (30 ECTS)</b>'
        f'{pill(thesis_ok, "Done", "In progress" if thesis == "In progress" else "To do")}</div>',
        unsafe_allow_html=True,
    )

    # What is still left to do
    todo = []
    left_units = max(UNITS_NEEDED - units_done, 0)
    if left_units:
        todo.append(f"Complete {left_units} more teaching units ({left_units * ECTS_PER_UNIT} ECTS).")
    if len(tracks_covered) < MIN_TRACKS:
        todo.append(f"Take units from {MIN_TRACKS - len(tracks_covered)} more track(s).")
    if spec_code and track_counts[spec_code] < SPEC_UNITS:
        todo.append(f"Optional: to specialise in {spec_code}, take {SPEC_UNITS - track_counts[spec_code]} "
                    f"more units there and write your thesis in this track.")
    if not thesis_ok:
        todo.append("Write your master's thesis.")
    if units_planned and left_units:
        after = min(units_done + units_planned, UNITS_NEEDED)
        todo.append(f"With this semester's plan you would reach {after} of {UNITS_NEEDED} units.")

    st.divider()
    st.subheader("Still to do")
    if todo:
        st.markdown("\n".join(f"- {t}" for t in todo))
    else:
        st.success("All requirements are covered.")

    st.divider()
    with st.expander("Key rules to keep in mind"):
        st.markdown(
            "- 12 teaching units of 5 ECTS = 60 ECTS, plus a 30 ECTS thesis.\n"
            "- Units must come from **at least 3 different tracks**.\n"
            "- To specialise: **at least 5 units** in one track **and** a thesis in that track.\n"
            "- Normal duration: **3 semesters** full-time.\n"
            "- If you fail the **continuous evaluation** of a unit, you must repeat the whole unit "
            "and cannot take its exam.\n"
            "- Courses are taught in English, sometimes in French or German."
        )
    st.caption("A course listed in several tracks is counted for each of them here. "
               "Check the final allocation with your study advisor.")

# ---------- Hard constraints (crisp filter) ----------
excluded_cities = [c for c, v in cities.items() if v["excluded"]]
done_codes = set(done_rows["code"])
pool = courses[courses["semester"] == semester] if semester else courses.iloc[0:0]
removed = pd.concat([
    pool[pool["site"].isin(excluded_cities)].assign(reason="City you can't go to"),
    pool[pool["code"].isin(done_codes)].assign(reason="Already completed"),
]).drop_duplicates("code")
pool = pool[~pool["code"].isin(removed["code"])]

# ---------- Required fields ----------
missing = []
if not study_sem:
    missing.append("your current master semester (tab 1)")
if not semester:
    missing.append("the semester you are planning (tab 2)")
if units_planned == 0:
    missing.append("at least one lecture or seminar (tab 2)")
if not any(v["value"] >= HIGH for v in tracks.values()):
    missing.append("at least one track at High or above (tab 3)")
if len(excluded_cities) == len(CITIES):
    missing.append("at least one city you can go to (tab 4)")

user_input = {
    "name": name, "study_semester": study_sem, "completed": completed, "other_units": other_units,
    "specialisation": spec_code, "thesis": thesis, "semester": semester,
    "n_lectures": n_lectures, "n_seminars": n_seminars, "tracks": tracks,
    "cities": cities, "days": days, "assessment": assessment, "profs": profs,
}

# ---------- Live summary ----------
with right:
    st.subheader("Your course pool")
    if semester:
        offered = len(courses[courses["semester"] == semester])
        st.metric("Courses you can take", len(pool),
                  delta=f"-{len(removed)} removed" if len(removed) else None, delta_color="inverse")
        st.caption(f"{offered} courses offered in this semester")
    else:
        st.metric("Courses you can take", "–")
        st.caption("Choose the semester you are planning in tab 2.")

    top_tracks = [f"{k} {TRACKS[k]} ({v['value']:.1f})" for k, v in tracks.items() if v["value"] >= HIGH]
    if top_tracks:
        st.markdown("**Your favourite tracks**")
        st.markdown("".join(f'<span class="tag">{t}</span>' for t in top_tracks), unsafe_allow_html=True)
    if excluded_cities:
        st.markdown("**Excluded cities:** " + ", ".join(excluded_cities))
    excluded_days = [d for d, v in days.items() if v["excluded"]]
    if excluded_days:
        st.markdown("**Days you can't attend:** " + ", ".join(excluded_days))

    st.write("")
    if missing:
        st.markdown('<div class="missing"><b>Before we can recommend, please fill in:</b></div>',
                    unsafe_allow_html=True)
        st.markdown("\n".join(f"- {m}" for m in missing))
    clicked = st.button("Recommend courses", type="primary", width="stretch",
                        disabled=bool(missing))
    if clicked:
        st.session_state["show_results"] = True

# ---------- Results ----------
if st.session_state.get("show_results") and not missing:
    st.divider()
    who = f", {name}" if name else ""
    st.subheader(f"Courses you can take{who}")
    st.info("The fuzzy ranking is coming next. For now, these are the courses that pass your hard constraints.")

    table = pool[["code", "name", "type", "site", "tracks", "lecturers"]].copy()
    table["tracks"] = table["tracks"].str.replace(";", ", ")
    table["lecturers"] = table["lecturers"].str.replace(";", ", ")
    st.dataframe(table.rename(columns=str.capitalize), hide_index=True, width="stretch")

    if len(removed):
        with st.expander(f"Removed by your constraints ({len(removed)})"):
            st.dataframe(removed[["code", "name", "site", "reason"]].rename(columns=str.capitalize),
                         hide_index=True, width="stretch")

    with st.expander("Data sent to the fuzzy engine"):
        st.json(user_input)
