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

    # Show raw applications
    st.subheader("Pending Applications")
    # Optionally filter out already enrolled if you track status
    # You might have a column like 'enrolled' or 'status'
    applications_df["selected"] = False  # placeholder for checkbox tracking

    # Display and handle enrollment per row
    enrollments = []

    for idx, app in applications_df.iterrows():
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            enroll_checkbox = st.checkbox(f"Enroll {app.get('first_name','')} {app.get('last_name','')}", key=f"enroll_{idx}")
        with col2:
            subject_choice = st.selectbox(
                "Subject",
                options=subjects_df["subject_title"].fillna("").unique(),
                key=f"subject_{idx}"
            )
        with col3:
            # derive subject_id from title
            selected_subject_row = subjects_df[subjects_df["subject_title"] == subject_choice]
            subject_id = selected_subject_row["subject_id"].iloc[0] if not selected_subject_row.empty else ""
            # Filter available sections for that subject
            valid_sections = section_df[section_df["subject_id"] == subject_id]["section_code"].unique().tolist()
            if not valid_sections:
                valid_sections = ["(no section for this subject)"]
            section_choice = st.selectbox("Section", options=valid_sections, key=f"section_{idx}")

        if enroll_checkbox:
            # Collect data for processing
            enrollments.append({
                "application_index": idx,
                "student_id": app.get("student_id"),
                "first_name": app.get("first_name"),
                "last_name": app.get("last_name"),
                "subject_title": subject_choice,
                "subject_id": subject_id,
                "section_code": section_choice,
                # you can map or lookup section_id if needed
                "date_enrolled": datetime.now().strftime("%Y-%m-%d")
            })

    if enrollments:
        if st.button("Confirm Enrollment(s)"):
            for e in enrollments:
                # 1. Append to Students sheet if not already there
                if e["student_id"] not in students_df["student_id"].astype(str).tolist():
                    new_student_row = {
                        "student_id": e["student_id"],
                        "first_name": e["first_name"],
                        "last_name": e["last_name"],
                        # fill other required student fields minimally
                        "date_enrolled": e["date_enrolled"]
                    }
                    students_df = pd.concat([students_df, pd.DataFrame([new_student_row])], ignore_index=True)

                # 2. Append to Section sheet: need section_id (if you have mapping)
                # If your subjects_df has section_id (ambiguous in schema), otherwise use section_code as is
                new_section_entry = {
                    "student_id": e["student_id"],
                    "section_id": e.get("section_code"),  # or look up true section_id
                    "section_code": e.get("section_code"),
                    "subject_id": e.get("subject_id"),
                    # you can fill other fields like schedule, batch_id if derivable
                }
                section_df = pd.concat([section_df, pd.DataFrame([new_section_entry])], ignore_index=True)

                # Optionally mark application as enrolled: add a status column if not present
                applications_df.loc[e["application_index"], "status"] = "enrolled"

            # Push updates back
            push_df_to_sheet(students_df, "Students")
            push_df_to_sheet(section_df, "Section")
            push_df_to_sheet(applications_df, "Students Registration")

            st.success(f"Enrolled {len(enrollments)} student(s). Reload to refresh data.")


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
