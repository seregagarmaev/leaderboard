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
    st.session_state.team_name = None

def login(team_id, password):
    if team_id in teams_dict and teams_dict[team_id] == password:
        st.session_state.logged_in = True
        st.session_state.team_name = team_id
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

# File to store full submission history
leaderboard_file = "leaderboard.csv"

# Load or initialize leaderboard
if os.path.exists(leaderboard_file):
    lb_df = pd.read_csv(leaderboard_file)
    required_cols = {"Team Name", "Score", "Submission Date"}
    if not required_cols.issubset(lb_df.columns):
        lb_df = pd.DataFrame(columns=["Team Name", "Score", "Submission Date"])
else:
    lb_df = pd.DataFrame(columns=["Team Name", "Score", "Submission Date"])

# Page title and instructions
st.title("Graded Exercise 3")
st.markdown(
    """
    This is the leaderboard for Graded Exercise 3.  
    You are allowed to submit only twice per day.  
    The evaluation metric is F1 score.
    """
)

# Submission section
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
    # Safe filename
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
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = pd.DataFrame({
                "Team Name": [team_name],
                "Score": [score],
                "Submission Date": [timestamp]
            })
            lb_df = pd.concat([lb_df, new_entry], ignore_index=True)
            lb_df.to_csv(leaderboard_file, index=False)
            st.success("Submission recorded!")

    except EvaluationError as e:
        st.error(f"Submission error: {e}")

elif uploaded_file and remaining_submissions <= 0:
    st.error("You have reached the submission limit for today (2 submissions).")

# Display full leaderboard (all submissions)
st.subheader("Leaderboard")

if not lb_df.empty:
    # Add Place column: sort all submissions from highest to lowest score
    all_submissions_sorted = (
        lb_df.sort_values("Score", ascending=False)
        .reset_index(drop=True)
    )
    all_submissions_sorted.insert(0, "Place", range(1, len(all_submissions_sorted) + 1))
    st.dataframe(all_submissions_sorted.style.hide(axis="index"), use_container_width=True)
else:
    st.info("No submissions yet.")
