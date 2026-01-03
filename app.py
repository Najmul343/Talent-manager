import streamlit as st
from PIL import Image
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(
    page_title="Talent Intelligence Dashboard",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "people" not in st.session_state:
    st.session_state.people = []

# ---------------- HELPERS ----------------
def normalize(skill: str) -> str:
    return skill.strip().lower()

def load_image(src):
    try:
        if not src:
            return None
        if isinstance(src, str) and src.startswith("http"):
            r = requests.get(src, timeout=5)
            return Image.open(BytesIO(r.content)).convert("RGB")
        if hasattr(src, "read"):
            return Image.open(src).convert("RGB")
        return Image.open(src).convert("RGB")
    except:
        return None

# ---------------- SIDEBAR ----------------
st.sidebar.title("Talent Intake")

st.sidebar.subheader("Manual Entry")
name = st.sidebar.text_input("Name *")
place = st.sidebar.text_input("Place")
skills = st.sidebar.text_input("Skills (comma separated)")
image_file = st.sidebar.file_uploader(
    "Upload Image",
    type=["png", "jpg", "jpeg"]
)

if st.sidebar.button("Add Person"):
    if name.strip():
        st.session_state.people.append({
            "name": name.strip(),
            "place": place.strip(),
            "skills": [normalize(s) for s in skills.split(",") if s.strip()],
            "image": load_image(image_file)
        })

st.sidebar.markdown("---")
st.sidebar.subheader("Bulk Upload (CSV / Excel)")
bulk_file = st.sidebar.file_uploader(
    "Upload CSV or Excel",
    type=["csv", "xlsx"]
)

if bulk_file:
    df = pd.read_csv(bulk_file) if bulk_file.name.endswith(".csv") else pd.read_excel(bulk_file)
    df.columns = [c.lower() for c in df.columns]

    if "name" not in df.columns:
        st.sidebar.error("CSV/Excel must contain a 'name' column")
    else:
        if st.sidebar.button("Import File"):
            for _, row in df.iterrows():
                name = str(row.get("name", "")).strip()
                if not name:
                    continue
                place = str(row.get("place", "")).strip()
                skills_raw = row.get("skills") or row.get("skill") or ""
                skills_list = [normalize(s) for s in str(skills_raw).split(",") if s.strip()]
                image = load_image(row.get("image", ""))

                st.session_state.people.append({
                    "name": name,
                    "place": place,
                    "skills": skills_list,
                    "image": image
                })
            st.sidebar.success("Bulk upload completed")

# ---------------- MAIN ----------------
st.title("Talent Intelligence Dashboard")

view_mode = st.radio(
    "View Mode",
    ["Talent Wall", "Multi-Skill Tree Intelligence"],
    horizontal=True
)

st.subheader("Filters")

filter_place = st.text_input("Filter by place (optional)")

# 🔽 THIS IS THE DROPDOWN WITH CHECKBOXES
all_skills = sorted({
    skill
    for p in st.session_state.people
    for skill in p["skills"]
})

selected_skills = st.multiselect(
    "Filter by skill(s)",
    options=all_skills,
    help="Select one or more skills"
)

match_all_skills = st.toggle(
    "Require ALL selected skills (AND logic)",
    value=False
)

# ---------------- FILTER LOGIC ----------------
def visible(p):
    if selected_skills:
        if match_all_skills:
            if not all(skill in p["skills"] for skill in selected_skills):
                return False
        else:
            if not any(skill in p["skills"] for skill in selected_skills):
                return False

    if filter_place.strip():
        if not p["place"]:
            return False
        if filter_place.lower() not in p["place"].lower():
            return False

    return True

filtered_people = [p for p in st.session_state.people if visible(p)]

# =================================================
# 🧱 TALENT WALL
# =================================================
if view_mode == "Talent Wall":
    cols = st.columns(4)
    for idx, p in enumerate(filtered_people):
        with cols[idx % 4]:
            if p["image"]:
                st.image(p["image"], width=250)
            else:
                st.markdown("### 👤")
            st.markdown(f"**{p['name']}**")
            st.caption(p["place"] or "—")
            st.caption(", ".join(p["skills"]) or "No skills")

# =================================================
# 🌳 MULTI-SKILL TREE INTELLIGENCE
# =================================================
else:
    show_images = st.toggle("Show images under tree", value=False)
    show_related_skills = st.toggle(
        "Show other skills associated with selected people",
        value=False
    )

    if not filtered_people:
        st.info("No matching people.")
    else:
        dot = "digraph TalentMap {\nrankdir=TB;\nnode [shape=box style=rounded];\n"

        if selected_skills and not show_related_skills:
            skill_roots = selected_skills
        else:
            skill_roots = sorted({
                skill
                for p in filtered_people
                for skill in p["skills"]
            })

        for skill in skill_roots:
            dot += f'"{skill}" [shape=ellipse style=filled fillcolor=lightblue];\n'

        for p in filtered_people:
            for skill in p["skills"]:
                if skill in skill_roots:
                    dot += f'"{skill}" -> "{p["name"]}";\n'
            dot += f'"{p["name"]}" -> "{p["place"] or "Unknown"}";\n'

        dot += "}"
        st.graphviz_chart(dot)

        if show_images:
            st.markdown("### Visual Talent Map")
            cols = st.columns(5)
            for idx, p in enumerate(filtered_people):
                with cols[idx % 5]:
                    if p["image"]:
                        st.image(p["image"], width=150)
                    else:
                        st.markdown("### 👤")
                    st.caption(p["name"])
