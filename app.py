import streamlit as st
import pandas as pd
import os
from evaluate import evaluate_prediction, EvaluationError

st.title("🧠 Deep Learning Project Submission")

uploaded_file = st.file_uploader("Upload your predictions (CSV file)", type="csv")

if uploaded_file:
    # Save uploaded file
    os.makedirs("uploads", exist_ok=True)
    filepath = os.path.join("uploads", uploaded_file.name)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.read())

    # Evaluate and handle errors
    try:
        score = evaluate_prediction(filepath)
        st.success(f"✅ Your score: {score:.4f}")

        # Input name for leaderboard
        name = st.text_input("Enter your name for the leaderboard:")
        if st.button("Submit score to leaderboard") and name:
            leaderboard_file = "leaderboard.csv"
            if os.path.exists(leaderboard_file):
                lb_df = pd.read_csv(leaderboard_file)
            else:
                lb_df = pd.DataFrame(columns=["name", "score"])

            new_entry = pd.DataFrame({"name": [name], "score": [score]})
            lb_df = pd.concat([lb_df, new_entry], ignore_index=True)
            lb_df.to_csv(leaderboard_file, index=False)
            st.success("🏅 Submitted to leaderboard!")

    except EvaluationError as e:
        st.error(f"❌ Submission error: {e}")

# Show leaderboard
leaderboard_file = "leaderboard.csv"
if os.path.exists(leaderboard_file):
    st.subheader("🏆 Leaderboard")
    leaderboard = pd.read_csv(leaderboard_file).sort_values(by="score", ascending=False).reset_index(drop=True)
    st.dataframe(leaderboard)