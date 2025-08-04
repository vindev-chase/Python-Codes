import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from datetime import datetime

st.title("Student Subject & Section Viewer")

# 🔐 Authenticate to Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
#scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#creds_dict = dict(st.secrets["student-monitoring-database"])  # secrets section name
#creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#client = gspread.authorize(creds)
service_account_info = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(creds)


# 📊 Load Google Sheets by name or key
spreadsheet = client.open("Student Monitoring Database")

# 🧾 Read the worksheets into DataFrames
students_df = pd.DataFrame(spreadsheet.worksheet("Students").get_all_records())
section_df = pd.DataFrame(spreadsheet.worksheet("Section").get_all_records())
subjects_df = pd.DataFrame(spreadsheet.worksheet("Subjects").get_all_records())
applications_df = pd.DataFrame(spreadsheet.worksheet("Students Registration").get_all_records())

# 🧼 Clean all column headers to avoid KeyError
for df in (students_df, section_df, subjects_df, applications_df):
    df.columns = df.columns.str.strip().str.lower()
#students_df.columns = students_df.columns.str.strip().str.lower()
#section_df.columns = section_df.columns.str.strip().str.lower()
#subjects_df.columns = subjects_df.columns.str.strip().str.lower()

#Helper to write back to a sheet
def push_df_to_sheet(df:pd.DataFrame, sheet_name: str):
    ws = spreadsheet.worksheet(sheet_name)
    ws.clear()
    ws.update([df.columns.tolist()] + df.fillna("").astype(str).values.tolist())

# Tabbed interface
tab1, tab2, tab3 = st.tabs(["Student Applications", "Enrolled Students", "Section List"])

# 👥 Merge Section with Students on student_id
#merged_df = section_df.merge(students_df, on="student_id", how="left")

# 🧾 Merge: Section ⬅️➡️ Students ⬅️➡️ Subjects
#merged_df = section_df.merge(students_df, on="student_id", how="left")
#final_df = merged_df.merge(subjects_df, on="subject_id", how="left")

# ✅ Filter: Only students with non-empty section_code
#assigned_df = final_df[final_df["section_id"].notna() & (final_df["section_id"] != "")]

# 📋 Select only the desired columns
#final_output = assigned_df[["student_id", "first_name", "last_name", "subject_title", "section_code"]]

# 🖥 Display
#st.subheader("Students with Assigned Sections")
#st.dataframe(final_output)

with tab1:
    st.header("Student Application List")

    # Only show applications not yet enrolled
    pending_apps = applications_df[applications_df.get("status", "").str.lower() != "enrolled"].copy()
    if pending_apps.empty:
        st.info("No pending applications.")
    else:
        st.subheader("Pending Applications")

        for idx, app in pending_apps.reset_index().iterrows():
            # Use the original index in applications_df to update later
            orig_idx = app["index"] if "index" in app else idx

            st.markdown("---")
            cols = st.columns([1, 2, 2, 2, 2])  # adjust widths as needed

            with cols[0]:
                st.markdown(f"**{app.get('student_type','')}**")
            with cols[1]:
                st.markdown(f"{app.get('first_name','')}")
            with cols[2]:
                st.markdown(f"{app.get('last_name','')}")
            with cols[3]:
                # Subject dropdown: show titles
                subject_choice = st.selectbox(
                    "Subject",
                    options=[""] + subjects_df["subject_title"].dropna().unique().tolist(),
                    key=f"subject_select_{orig_idx}"
                )
            with cols[4]:
                # Determine subject_id from title
                subject_id = ""
                if subject_choice:
                    matched = subjects_df[subjects_df["subject_title"] == subject_choice]
                    if not matched.empty:
                        subject_id = matched["subject_id"].iloc[0]

                # Section dropdown filtered by subject_id
                section_options = []
                if subject_id:
                    section_options = section_df[section_df["subject_id"] == subject_id]["section_code"].dropna().unique().tolist()
                section_choice = st.selectbox(
                    "Section",
                    options=[""] + section_options if section_options else [""],
                    key=f"section_select_{orig_idx}"
                )

            # Enroll button (must be outside the column group to avoid layout issues)
            enroll_key = f"enroll_btn_{orig_idx}"
            if st.button("Enroll", key=enroll_key):
                # Validation
                if not subject_choice or not section_choice:
                    st.warning("You must select both a subject and a section before enrolling.")
                else:
                    # Update the corresponding row in applications_df
                    # Find the row by matching a unique identifier (assumes 'student_id' exists)
                    mask = applications_df["student_id"].astype(str) == str(app.get("student_id"))
                    # If multiple matches, further narrow down by first+last name if needed
                    # Here we pick the first unmatched pending one
                    target_indices = applications_df[mask & (applications_df.get("status", "").str.lower() != "enrolled")]
                    if target_indices.empty:
                        st.error("Could not find the application row to update.")
                    else:
                        target_idx = target_indices.index[0]
                        applications_df.at[target_idx, "subject_id"] = subject_id
                        applications_df.at[target_idx, "subject_title"] = subject_choice
                        applications_df.at[target_idx, "section_code"] = section_choice
                        applications_df.at[target_idx, "status"] = "enrolled"
                        applications_df.at[target_idx, "date_enrolled"] = datetime.now().strftime("%Y-%m-%d")

                        # Push updated applications back to the sheet
                        push_df_to_sheet(applications_df, "Students Registration")

                        st.success(f"Enrolled {app.get('first_name','')} {app.get('last_name','')} in {subject_choice} / {section_choice}")



with tab2:
    st.header("Enrolled Students")

    # Recompute merges to reflect updated data
    merged_df = section_df.merge(students_df, on="student_id", how="left")
    final_df = merged_df.merge(subjects_df, on="subject_id", how="left")

    # Only those with an assigned section
    assigned_df = final_df[
        final_df["section_code"].notna() & (final_df["section_code"] != "")
    ]

    display_df = assigned_df[["student_id", "first_name", "last_name", "subject_title", "section_code"]]
    st.dataframe(display_df)

    # Optionally allow exporting
    st.download_button("Download Enrolled Students CSV", display_df.to_csv(index=False).encode("utf-8"),
                       file_name="enrolled_students.csv", mime="text/csv")


with tab3:
    st.header("Section List Overview")

    # Count enrolled students per section_code
    enrolled = section_df.merge(students_df, on="student_id", how="left")
    section_summary = (
        enrolled.groupby("section_code", dropna=False)
        .agg(
            enrolled_count=("student_id", "nunique"),
        )
        .reset_index()
    )

    # Add schedule info: assuming section_code maps to one schedule row
    # Pick the first matching to pull schedule/start/end/batch
    def get_section_meta(code, field):
        row = section_df[section_df["section_code"] == code]
        return row[field].iloc[0] if not row.empty else ""

    section_summary["day_sched"] = section_summary["section_code"].apply(lambda c: get_section_meta(c, "section_day_sched"))
    section_summary["start_time"] = section_summary["section_code"].apply(lambda c: get_section_meta(c, "section_start_time"))
    section_summary["end_time"] = section_summary["section_code"].apply(lambda c: get_section_meta(c, "section_end_time"))
    section_summary["batch_id"] = section_summary["section_code"].apply(lambda c: get_section_meta(c, "batch_id"))

    st.subheader("All Sections")
    st.dataframe(section_summary)

    # Drill-down: select a section to view its details and students
    selected_section = st.selectbox("View Section Details", options=section_summary["section_code"].dropna().unique())
    if selected_section:
        st.markdown(f"### Details for Section **{selected_section}**")
        meta = section_summary[section_summary["section_code"] == selected_section].iloc[0]
        st.write({
            "Section Code": meta["section_code"],
            "Batch": meta["batch_id"],
            "Schedule": f"{meta['day_sched']} {meta['start_time']}–{meta['end_time']}",
            "Enrolled Count": int(meta["enrolled_count"]),
        })

        # List students in that section
        students_in_section = assigned_df[assigned_df["section_code"] == selected_section]
        if not students_in_section.empty:
            st.subheader("Enrolled Students in This Section")
            st.dataframe(students_in_section[["student_id", "first_name", "last_name", "subject_title"]])
        else:
            st.info("No students currently enrolled in this section.")
