import streamlit as st
import pandas as pd
import os
from datetime import datetime
from evaluate import evaluate_prediction, EvaluationError

def load_teams_from_secrets():
    secrets = st.secrets["teams"]
    return {team: secrets[team] for team in secrets}

teams_dict = load_teams_from_secrets()

# Streamlit session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.team_id = None

def login(team_id, password):
    if team_id in teams_dict and teams_dict[team_id] == password:
        st.session_state.logged_in = True
        st.session_state.team_id = team_id
    else:
        st.error("Invalid team ID or password.")

# Login form
if not st.session_state.logged_in:
    st.title("Team Login")
    team_id = st.text_input("Team ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        login(team_id, password)
    st.stop()

# Load or initialize leaderboard
leaderboard_file = "leaderboard.csv"
if os.path.exists(leaderboard_file):
    lb_df = pd.read_csv(leaderboard_file)
    required_cols = {"team_id", "score", "timestamp"}
    if not required_cols.issubset(lb_df.columns):
        lb_df = pd.DataFrame(columns=["team_id", "score", "timestamp"])
else:
    lb_df = pd.DataFrame(columns=["team_id", "score", "timestamp"])

# Get submission count for today
st.title("Submit Your Predictions")
today = datetime.now().strftime("%Y-%m-%d")
team_id = st.session_state.team_id
submissions_today = lb_df[
    (lb_df["team_id"] == team_id) &
    (lb_df["timestamp"].str.startswith(today))
]
remaining_submissions = 2 - len(submissions_today)

st.markdown(f"**Logged in as:** `{team_id}`")
st.markdown(f"**Remaining submissions today:** {remaining_submissions}")

# Upload and submit
uploaded_file = st.file_uploader("Upload CSV prediction", type="csv")

if uploaded_file and remaining_submissions > 0:
    # Safe filename
    safe_time = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{team_id}_{safe_time}.csv"
    filepath = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)

    with open(filepath, "wb") as f:
        f.write(uploaded_file.read())

    try:
        score = evaluate_prediction(filepath)
        st.success(f"Score: {score:.4f}")

        if st.button("Submit to leaderboard"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = pd.DataFrame({
                "team_id": [team_id],
                "score": [score],
                "timestamp": [timestamp]
            })
            lb_df = pd.concat([lb_df, new_entry], ignore_index=True)
            lb_df.to_csv(leaderboard_file, index=False)
            st.success("🎉 Submission recorded!")

    except EvaluationError as e:
        st.error(f"Submission error: {e}")

elif uploaded_file and remaining_submissions <= 0:
    st.error("You have reached the submission limit for today (2 submissions).")

# Leaderboard
st.subheader("Leaderboard")
if not lb_df.empty:
    lb_df = lb_df.sort_values(by="score", ascending=False).reset_index(drop=True)
    st.dataframe(lb_df)
else:
    st.info("No submissions yet.")