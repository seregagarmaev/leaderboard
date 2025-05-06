import streamlit as st
import pandas as pd
import os
from datetime import datetime
from evaluate import evaluate_prediction, EvaluationError
import traceback

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    spreadsheet_id = st.secrets["gsheet"]["spreadsheet_id"]
    return client.open_by_key(spreadsheet_id).sheet1

def load_leaderboard():
    sheet = get_worksheet()
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def append_submission(team_name, score):
    sheet = get_worksheet()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([team_name, score, timestamp])

def load_teams_from_secrets():
    secrets = st.secrets["teams"]
    return {team: secrets[team] for team in secrets}

teams_dict = load_teams_from_secrets()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.team_name = None

def login(team_id, password):
    if team_id in teams_dict and teams_dict[team_id] == password:
        st.session_state.logged_in = True
        st.session_state.team_name = team_id
    else:
        st.error("Invalid team ID or password.")

if not st.session_state.logged_in:
    st.title("Team Login")
    team_id = st.text_input("Team ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        login(team_id, password)
    st.stop()

try:
    lb_df = load_leaderboard()
except Exception as e:
    st.error("Failed to load leaderboard.")
    st.text(traceback.format_exc())
    lb_df = pd.DataFrame(columns=["Team Name", "Score", "Submission Date"])

st.title("Graded Exercise 3")
st.markdown("""
This is the leaderboard for Graded Exercise 3.  
You are allowed to submit only twice per day.  
The evaluation metric is F1 score.
""")

today = datetime.now().strftime("%Y-%m-%d")
team_name = st.session_state.team_name
submissions_today = lb_df[
    (lb_df["Team Name"] == team_name) &
    (lb_df["Submission Date"].str.startswith(today))
]
remaining_submissions = 2 - len(submissions_today)

st.markdown(f"**Logged in as:** `{team_name}`")

uploaded_file = st.file_uploader("Upload CSV prediction", type="csv")

if uploaded_file and remaining_submissions > 0:
    # Save uploaded file (optional - not persistent)
    safe_time = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{team_name}_{safe_time}.csv"
    filepath = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)

    with open(filepath, "wb") as f:
        f.write(uploaded_file.read())

    try:
        score = evaluate_prediction(filepath)
        st.success(f"Score: {score:.4f}")

        if st.button("Submit to leaderboard"):
            append_submission(team_name, score)
            st.success("Submission recorded!")

    except EvaluationError as e:
        st.error(f"Submission error: {e}")

elif uploaded_file and remaining_submissions <= 0:
    st.error("You have reached the submission limit for today (2 submissions).")

# === Display leaderboard ===
st.subheader("Leaderboard")

if not lb_df.empty:
    all_submissions_sorted = lb_df.sort_values("Score", ascending=False).reset_index(drop=True)
    all_submissions_sorted.insert(0, "Place", range(1, len(all_submissions_sorted) + 1))
    st.dataframe(all_submissions_sorted.style.hide(axis="index"), use_container_width=True)
else:
    st.info("No submissions yet.")