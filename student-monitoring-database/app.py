import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------- AUTH & SETUP ----------
st.set_page_config(page_title="Enrollment Dashboard", layout="wide")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Load credentials from Streamlit secrets
service_account_info = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(creds)

# Replace with your spreadsheet name or use open_by_key(...)
SPREADSHEET_NAME = "Student Monitoring Database"
spreadsheet = client.open(SPREADSHEET_NAME)

# ---------- LOAD / CLEAN DATA ----------
def load_sheet_df(name):
    df = pd.DataFrame(spreadsheet.worksheet(name).get_all_records())
    df.columns = df.columns.str.strip().str.lower()
    return df

students_df = load_sheet_df("Students")
section_df = load_sheet_df("Section")
subjects_df = load_sheet_df("Subjects")
applications_df = load_sheet_df("Students Registration")  # contains status checkbox in column q

# Normalize status (checkbox) into boolean enrolled_flag
def normalize_enrolled(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "yes", "1", "checked")
    if pd.isna(val):
        return False
    return False

applications_df["enrolled_flag"] = applications_df.get("status", "").apply(normalize_enrolled)

# ---------- HELPERS ----------
def push_df_to_sheet(df: pd.DataFrame, sheet_name: str):
    """Overwrite the sheet with the DataFrame (headers + rows)."""
    ws = spreadsheet.worksheet(sheet_name)
    # Clear before updating to avoid residuals
    ws.clear()
    # Convert all to strings to avoid type issues
    data = [df.columns.tolist()] + df.fillna("").astype(str).values.tolist()
    ws.update(data)

def student_already_enrolled_in_section(student_id, section_code):
    """Check in section_df if student is already enrolled in that section_code."""
    mask = (
        section_df["student_id"].astype(str) == str(student_id)
    ) & (section_df["section_code"] == section_code)
    return not section_df[mask].empty

# ---------- UI ----------
tab1, tab2, tab3 = st.tabs(
    ["📝 Student Applications", "🎓 Enrolled Students", "📚 Section List"]
)

# ---------- TAB 1: Student Applications ----------
with tab1:
    st.header("Student Application List")
    st.markdown("Only applications with no checked status are shown. Select subject + section and press Enroll.")

    # Filter out blank/placeholder rows: require student_id and first_name non-empty
    pending_apps = applications_df[
        (~applications_df["enrolled_flag"])
        & applications_df["student_id"].astype(str).str.strip().astype(bool)
        & applications_df["first_name"].astype(str).str.strip().astype(bool)
    ].reset_index()

    if pending_apps.empty:
        st.info("No pending applications to enroll.")
    else:
        for _, app in pending_apps.iterrows():
            orig_idx = app["index"]  # original row index in applications_df
            student_id = app.get("student_id", "")
            first_name = app.get("first_name", "")
            last_name = app.get("last_name", "")
            student_type = app.get("student_type", "")

            # Layout per application
            with st.expander(f"{student_type} — {first_name} {last_name} (ID: {student_id})", expanded=False):
                cols = st.columns([1.5, 1.5, 2, 2, 2, 1.5])
                with cols[0]:
                    st.markdown("**Student Type**")
                    st.write(student_type)
                with cols[1]:
                    st.markdown("**First Name**")
                    st.write(first_name)
                with cols[2]:
                    st.markdown("**Last Name**")
                    st.write(last_name)
                with cols[3]:
                    st.markdown("**Subject**")
                    subject_choice = st.selectbox(
                        "Select subject",
                        options=[""] + subjects_df["subject_title"].dropna().unique().tolist(),
                        key=f"subject_select_{orig_idx}"
                    )
                with cols[4]:
                    st.markdown("**Section**")
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
                with cols[5]:
                    st.markdown("**Enroll**")
                    enroll_clicked = st.button("Enroll", key=f"enroll_btn_{orig_idx}")

                if enroll_clicked:
                    # Validation
                    if not subject_choice or not section_choice:
                        st.warning("Please select both subject and section before enrolling.")
                    else:
                        # Prevent duplicate enrollment in Section sheet if desired
                        if student_already_enrolled_in_section(student_id, section_choice):
                            st.error(f"Student {student_id} already enrolled in section '{section_choice}'. Skipping.")
                        else:
                            # Update registration record
                            applications_df.at[orig_idx, "subject_title"] = subject_choice
                            applications_df.at[orig_idx, "subject_id"] = subject_id
                            applications_df.at[orig_idx, "section_code"] = section_choice
                            applications_df.at[orig_idx, "date_enrolled"] = datetime.now().strftime("%Y-%m-%d")
                            applications_df.at[orig_idx, "status"] = True  # mark checkbox as checked
                            applications_df.at[orig_idx, "enrolled_flag"] = True

                            # Optionally: append to Students sheet if missing
                            if str(student_id) not in students_df["student_id"].astype(str).tolist():
                                new_student = {
                                    "student_id": student_id,
                                    "first_name": first_name,
                                    "last_name": last_name,
                                    "date_enrolled": datetime.now().strftime("%Y-%m-%d"),
                                }
                                students_df.loc[len(students_df)] = new_student

                            # Optionally: append to Section sheet to reflect enrollment
                            if not student_already_enrolled_in_section(student_id, section_choice):
                                new_section_row = {
                                    "student_id": student_id,
                                    "section_id": section_choice,  # adapt if you have a separate section_id
                                    "section_code": section_choice,
                                    "subject_id": subject_id,
                                }
                                section_df.loc[len(section_df)] = new_section_row

                            # Persist changes back to Google Sheets
                            push_df_to_sheet(applications_df, "Students Registration")
                            push_df_to_sheet(students_df, "Students")
                            push_df_to_sheet(section_df, "Section")

                            st.success(f"Enrolled {first_name} {last_name} in '{subject_choice}' / '{section_choice}'.")

# ---------- TAB 2: Enrolled Students ----------
with tab2:
    st.header("Enrolled Students")

    # Recompute merged view
    merged_students = section_df.merge(students_df, on="student_id", how="left")
    final_df = merged_students.merge(subjects_df, on="subject_id", how="left")

    # Only those with a section assigned
    assigned_df = final_df[
        final_df["section_code"].notna() & (final_df["section_code"].astype(str).str.strip() != "")
    ]

    display_df = assigned_df[[
        "student_id", "first_name", "last_name", "subject_title", "section_code"
    ]].drop_duplicates()

    st.subheader("Current Enrollments")
    st.dataframe(display_df.reset_index(drop=True))

    st.download_button(
        "Download Enrolled Students CSV",
        display_df.to_csv(index=False).encode("utf-8"),
        file_name="enrolled_students.csv",
        mime="text/csv"
    )

# ---------- TAB 3: Section List ----------
with tab3:
    st.header("Section List Overview")

    # Build summary: count students per section_code from assigned_df
    section_summary = (
        assigned_df.groupby("section_code", dropna=False)
        .agg(
            enrolled_count=("student_id", "nunique"),
        )
        .reset_index()
    )

    # Pull additional metadata from section_df (first occurrence per section_code)
    def get_meta(section_code, field):
        row = section_df[section_df["section_code"] == section_code]
        return row[field].iloc[0] if not row.empty and field in row.columns else ""

    section_summary["section_day_sched"] = section_summary["section_code"].apply(lambda c: get_meta(c, "section_day_sched"))
    section_summary["section_start_time"] = section_summary["section_code"].apply(lambda c: get_meta(c, "section_start_time"))
    section_summary["section_end_time"] = section_summary["section_code"].apply(lambda c: get_meta(c, "section_end_time"))
    section_summary["batch_id"] = section_summary["section_code"].apply(lambda c: get_meta(c, "batch_id"))

    st.subheader("Sections and Enrollment Counts")
    st.dataframe(section_summary)

    st.markdown("### Drill-down: Section Details")
    selected_section = st.selectbox("Select section to view details", options=section_summary["section_code"].dropna().unique())

    if selected_section:
        meta = section_summary[section_summary["section_code"] == selected_section].iloc[0]
        st.markdown(f"**Section {selected_section}**")
        st.write({
            "Batch": meta.get("batch_id", ""),
            "Schedule": f"{meta.get('section_day_sched','')} {meta.get('section_start_time','')} - {meta.get('section_end_time','')}",
            "Enrolled Students": int(meta.get("enrolled_count", 0))
        })

        # List students in that section
        in_section = assigned_df[assigned_df["section_code"] == selected_section]
        if not in_section.empty:
            st.subheader("Students in this Section")
            st.dataframe(in_section[[
                "student_id", "first_name", "last_name", "subject_title"
            ]].drop_duplicates().reset_index(drop=True))
        else:
            st.info("No students currently enrolled in this section.")
