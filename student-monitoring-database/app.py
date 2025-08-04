import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------- CONFIG / AUTH ----------
st.set_page_config(page_title="Enrollment Dashboard", layout="wide")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

service_account_info = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(creds)

SPREADSHEET_NAME = "Student Monitoring Database"  # replace with your actual spreadsheet name
spreadsheet = client.open(SPREADSHEET_NAME)

# ---------- HELPERS ----------
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    df = pd.DataFrame(spreadsheet.worksheet(sheet_name).get_all_records())
    df.columns = df.columns.str.strip().str.lower()
    return df

def push_df_to_sheet(df: pd.DataFrame, sheet_name: str):
    ws = spreadsheet.worksheet(sheet_name)
    ws.clear()
    data = [df.columns.tolist()] + df.fillna("").astype(str).values.tolist()
    ws.update(data)

def normalize_enrolled(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "yes", "1", "checked")
    if pd.isna(val):
        return False
    return False

def generate_student_id(existing_df: pd.DataFrame, enrollment_year: int, program_code: str = "R") -> str:
    prefix = f"{enrollment_year}{program_code}"
    existing_ids = existing_df["student_id"].astype(str).fillna("")
    tails = []
    for sid in existing_ids:
        if sid.startswith(prefix):
            tail = sid[len(prefix):]
            if tail.isdigit():
                tails.append(int(tail))
    if tails:
        next_num = max(tails) + 1
    else:
        next_num = 10001
    return f"{prefix}{next_num}"

def section_enrollment_count(section_code: str, df_students: pd.DataFrame) -> int:
    return df_students[df_students["section_code"] == section_code]["student_id"].nunique()

def student_has_section(student_id, section_code, df_students):
    return not df_students[
        (df_students["student_id"].astype(str) == str(student_id))
        & (df_students["section_code"] == section_code)
    ].empty

# ---------- LOAD DATA ----------
students_df = load_sheet_df("Students")
section_df = load_sheet_df("Section")
subjects_df = load_sheet_df("Subjects")
applications_df = load_sheet_df("Students Registration")

# Normalize status/checkbox
applications_df["enrolled_flag"] = applications_df.get("status", "").apply(normalize_enrolled)

# ---------- UI TABS ----------
tab1, tab2, tab3 = st.tabs(
    ["📝 Student Applications", "🎓 Enrolled Students", "📚 Section List"]
)

# ---------- TAB 1: Student Applications ----------
with tab1:
    st.header("Student Application List")
    st.markdown(
        "Pending applications appear below. Select subject and section (capacity shown), then click Enroll. "
        "Max per section is **6**. Age and preferred starting bracket are included."
    )

    # Sanity check column presence
    missing_cols = []
    for col in ["student_age", "preferred_starting_bracket"]:
        if col not in applications_df.columns:
            missing_cols.append(col)
    if missing_cols:
        st.warning(f"The following expected column(s) are missing from Students Registration: {', '.join(missing_cols)}")

    # Filter pending and non-empty
    pending_apps = applications_df[
        (~applications_df["enrolled_flag"])
        & applications_df["first_name"].astype(str).str.strip().astype(bool)
        & applications_df["last_name"].astype(str).str.strip().astype(bool)
    ].reset_index()

    if pending_apps.empty:
        st.info("No pending applications to process.")
    else:
        for _, app in pending_apps.iterrows():
            orig_idx = app["index"]
            first_name = app.get("first_name", "")
            last_name = app.get("last_name", "")
            student_type = app.get("student_type", "")
            student_nickname = app.get("student_nickname", "")
            student_contact = app.get("student_contact", "")
            student_birthday = app.get("student_birthday", "")
            student_age = app.get("student_age", "(no age)")
            preferred_bracket = app.get("preferred_starting_bracket", "(no bracket)")
            emergency_contact_person = app.get("emergency_contact_person", "")
            emergency_contact_number = app.get("emergency_contact_number", "")
            emergency_contact_relationship = app.get("emergency_contact_relationship", "")

            with st.expander(f"{student_type} — {first_name} {last_name} {student_age} {preferred_bracket}", expanded=False):
                cols = st.columns([1.2, 1.2, 1.5, 1.2, 1.8, 1.8, 2, 1.5])
                with cols[0]:
                    st.markdown("**Type**")
                    st.write(student_type)
                with cols[1]:
                    st.markdown("**First Name**")
                    st.write(first_name)
                with cols[2]:
                    st.markdown("**Last Name**")
                    st.write(last_name)
                with cols[3]:
                    st.markdown("**Age**")
                    st.write(student_age)
                with cols[4]:
                    st.markdown("**Preferred Starting Bracket**")
                    st.write(preferred_bracket)
                with cols[5]:
                    st.markdown("**Subject**")
                    subject_choice = st.selectbox(
                        "Select subject",
                        options=[""] + subjects_df["subject_title"].dropna().unique().tolist(),
                        key=f"subject_select_{orig_idx}"
                    )
                with cols[6]:
                    st.markdown("**Section (capacity)**")
                    subject_id = ""
                    if subject_choice:
                        matched = subjects_df[subjects_df["subject_title"] == subject_choice]
                        if not matched.empty:
                            subject_id = matched["subject_id"].iloc[0]
                    section_options = []
                    if subject_id:
                        section_options = section_df[
                            section_df["subject_id"] == subject_id
                        ]["section_code"].dropna().unique().tolist()
                    section_choice = st.selectbox(
                        "Select section",
                        options=[""] + section_options if section_options else [""],
                        key=f"section_select_{orig_idx}"
                    )
                with cols[7]:
                    st.markdown("**Enroll**")
                    enroll_clicked = st.button("Enroll", key=f"enroll_btn_{orig_idx}")

                # Show capacity
                if section_choice:
                    count = section_enrollment_count(section_choice, students_df)
                    st.markdown(f"**Section {section_choice}: {count}/6 enrolled**")
                    if count >= 6:
                        st.error(f"Section {section_choice} is full. Cannot enroll more.")

                if enroll_clicked:
                    if not subject_choice or not section_choice:
                        st.warning("Both subject and section must be selected.")
                        continue
                    current_count = section_enrollment_count(section_choice, students_df)
                    if current_count >= 6:
                        st.error(f"Cannot enroll: section {section_choice} already has 6 students.")
                        continue

                    # Generate student ID
                    now = datetime.now()
                    year = now.year
                    new_student_id = generate_student_id(students_df, year, program_code="R")

                    # Build student record
                    student_row = {
                        "student_id": new_student_id,
                        "first_name": first_name,
                        "last_name": last_name,
                        "student_nickname": student_nickname,
                        "student_contact": student_contact,
                        "student_birthday": student_birthday,
                        "student_age": student_age,
                        "emergency_contact_person": emergency_contact_person,
                        "emergency_contact_number": emergency_contact_number,
                        "emergency_contact_relationship": emergency_contact_relationship,
                        "preferred_starting_bracket": preferred_bracket,
                        "section_code": section_choice,
                        "subject_id": subject_id,
                        "subject_title": subject_choice,
                        "date_enrolled": now.strftime("%Y-%m-%d"),
                    }

                    # Append to Students
                    students_df.loc[len(students_df)] = student_row

                    # Update application
                    applications_df.at[orig_idx, "student_id"] = new_student_id
                    applications_df.at[orig_idx, "subject_title"] = subject_choice
                    applications_df.at[orig_idx, "subject_id"] = subject_id
                    applications_df.at[orig_idx, "section_code"] = section_choice
                    applications_df.at[orig_idx, "date_enrolled"] = now.strftime("%Y-%m-%d")
                    applications_df.at[orig_idx, "status"] = True
                    applications_df.at[orig_idx, "enrolled_flag"] = True

                    # Persist
                    push_df_to_sheet(applications_df, "Students Registration")
                    push_df_to_sheet(students_df, "Students")

                    st.success(f"Enrolled {first_name} {last_name} as {new_student_id} into section '{section_choice}'.")


# ---------- TAB 2: Enrolled Students ----------
with tab2:
    st.header("Enrolled Students")

    enrolled_students = students_df[
        students_df["section_code"].astype(str).str.strip() != ""
    ].copy()

    # Ensure subject_title is filled if missing
    if "subject_title" in enrolled_students.columns:
        missing_mask = enrolled_students["subject_title"].isna() | (enrolled_students["subject_title"] == "")
        if missing_mask.any():
            title_map = subjects_df.set_index("subject_id")["subject_title"].to_dict()
            enrolled_students.loc[missing_mask, "subject_title"] = enrolled_students.loc[missing_mask, "subject_id"].map(title_map)
    else:
        enrolled_students["subject_title"] = enrolled_students["subject_id"].map(
            subjects_df.set_index("subject_id")["subject_title"]
        )

    display_df = enrolled_students[[
        "student_id", "first_name", "last_name", "subject_title", "section_code"
    ]].drop_duplicates().reset_index(drop=True)

    st.subheader("Current Enrollments")
    st.dataframe(display_df)

    st.download_button(
        "Download Enrolled Students CSV",
        display_df.to_csv(index=False).encode("utf-8"),
        file_name="enrolled_students.csv",
        mime="text/csv"
    )

# ---------- TAB 3: Section List ----------
with tab3:
    st.header("Section List Overview")

    section_summary = (
        students_df[students_df["section_code"].astype(str).str.strip() != ""]
        .groupby("section_code", dropna=False)
        .agg(enrolled_count=("student_id", "nunique"))
        .reset_index()
    )

    def get_section_meta(code, field):
        row = section_df[section_df["section_code"] == code]
        return row[field].iloc[0] if not row.empty and field in row.columns else ""

    section_summary["section_day_sched"] = section_summary["section_code"].apply(lambda c: get_section_meta(c, "section_day_sched"))
    section_summary["section_start_time"] = section_summary["section_code"].apply(lambda c: get_section_meta(c, "section_start_time"))
    section_summary["section_end_time"] = section_summary["section_code"].apply(lambda c: get_section_meta(c, "section_end_time"))
    section_summary["batch_id"] = section_summary["section_code"].apply(lambda c: get_section_meta(c, "batch_id"))

    st.subheader("Sections and Enrollment Counts")
    st.dataframe(section_summary)

    st.markdown("### Drill-down: Section Details")
    selected_section = st.selectbox(
        "Select section to inspect",
        options=section_summary["section_code"].dropna().unique()
    )

    if selected_section:
        meta = section_summary[section_summary["section_code"] == selected_section].iloc[0]
        st.markdown(f"**Section {selected_section}**")
        st.write({
            "Batch": meta.get("batch_id", ""),
            "Schedule": f"{meta.get('section_day_sched','')} {meta.get('section_start_time','')} - {meta.get('section_end_time','')}",
            "Enrolled Students": int(meta.get("enrolled_count", 0))
        })

        students_in_section = students_df[students_df["section_code"] == selected_section].copy()
        if not students_in_section.empty:
            if "subject_title" not in students_in_section.columns or students_in_section["subject_title"].isna().any():
                title_map = subjects_df.set_index("subject_id")["subject_title"].to_dict()
                students_in_section["subject_title"] = students_in_section["subject_id"].map(title_map)

            st.subheader("Students in this Section")
            st.dataframe(
                students_in_section[["student_id", "first_name", "last_name", "subject_title"]]
                .drop_duplicates()
                .reset_index(drop=True)
            )
        else:
            st.info("No students enrolled in this section yet.")
