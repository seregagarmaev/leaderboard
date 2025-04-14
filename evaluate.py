import pandas as pd
from sklearn.metrics import f1_score
from cryptography.fernet import Fernet
from io import BytesIO
import streamlit as st


class EvaluationError(Exception):
    """Custom exception for evaluation errors."""
    pass


def load_ground_truth_encrypted():
    try:
        with open("ground_truth.encrypted", "rb") as f:
            encrypted = f.read()
        key = st.secrets["encryption"]["key"]
        cipher = Fernet(key.encode())
        decrypted = cipher.decrypt(encrypted)
        df = pd.read_csv(BytesIO(decrypted))
        return df
    except Exception as e:
        raise EvaluationError(f"Failed to load ground truth: {e}")


def evaluate_prediction(pred_path):
    try:
        if not pred_path.endswith(".csv"):
            raise EvaluationError("Uploaded file is not a CSV.")

        preds = pd.read_csv(pred_path)
        truth = load_ground_truth_encrypted()

        if preds.empty:
            raise EvaluationError("Prediction file is empty.")
        if truth.empty:
            raise EvaluationError("Ground truth file is empty.")
        if preds.shape != truth.shape:
            raise EvaluationError(f"Shape mismatch: predictions {preds.shape}, ground truth {truth.shape}.")
        if list(preds.columns) != list(truth.columns):
            raise EvaluationError("Prediction file must have the same column names as the ground truth.")

        unique_classes = set(preds.iloc[:, 0].unique())
        if len(unique_classes) != 2 or not unique_classes.issubset({0, 1}):
            raise EvaluationError(f"Prediction must contain exactly two classes: 0 and 1. Got: {unique_classes}")

        score = f1_score(truth, preds)
        return score

    except pd.errors.ParserError:
        raise EvaluationError("Failed to read CSV. Please check the file format.")
    except Exception as e:
        raise EvaluationError(str(e))