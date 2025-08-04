import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("Student Subject & Section Viewer")

# 🔐 Authenticate to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("student-monitoring-database-334212d8ac2b.json", scope)
client = gspread.authorize(creds)

# 📊 Load Google Sheets by name or key
spreadsheet = client.open("Student Monitoring Database")

# 🧾 Read the worksheets into DataFrames
students_df = pd.DataFrame(spreadsheet.worksheet("Students").get_all_records())
section_df = pd.DataFrame(spreadsheet.worksheet("Section").get_all_records())
subjects_df = pd.DataFrame(spreadsheet.worksheet("Subjects").get_all_records())

# 🧼 Clean all column headers to avoid KeyError
students_df.columns = students_df.columns.str.strip().str.lower()
section_df.columns = section_df.columns.str.strip().str.lower()
subjects_df.columns = subjects_df.columns.str.strip().str.lower()

# 👥 Merge Section with Students on student_id
merged_df = section_df.merge(students_df, on="student_id", how="left")

# 🧾 Merge: Section ⬅️➡️ Students ⬅️➡️ Subjects
merged_df = section_df.merge(students_df, on="student_id", how="left")
final_df = merged_df.merge(subjects_df, on="subject_id", how="left")

# ✅ Filter: Only students with non-empty section_code
assigned_df = final_df[final_df["section_id"].notna() & (final_df["section_id"] != "")]

# 📋 Select only the desired columns
final_output = assigned_df[["student_id", "first_name", "last_name", "subject_title", "section_code"]]

# 🖥 Display
st.subheader("Students with Assigned Sections")
st.dataframe(final_output)

