import pandas as pd
from sklearn.metrics import f1_score

class EvaluationError(Exception):
    """Custom exception for evaluation errors."""
    pass

def evaluate_prediction(pred_path, ground_truth_path='ground_truth.csv'):
    try:
        # Check file type
        if not pred_path.endswith(".csv"):
            raise EvaluationError("Uploaded file is not a CSV.")

        # Load predictions and ground truth
        preds = pd.read_csv(pred_path)
        truth = pd.read_csv(ground_truth_path)

        # Check if either is empty
        if preds.empty:
            raise EvaluationError("Prediction file is empty.")
        if truth.empty:
            raise EvaluationError("Ground truth file is empty.")

        # Check shape
        if preds.shape != truth.shape:
            raise EvaluationError(f"Shape mismatch: predictions {preds.shape}, ground truth {truth.shape}.")

        # Check columns
        if list(preds.columns) != list(truth.columns):
            raise EvaluationError("Prediction file must have the same column names as the ground truth.")

        # Check binary classification
        unique_classes = set(preds.iloc[:, 0].unique())
        if len(unique_classes) != 2 or not unique_classes.issubset({0, 1}):
            raise EvaluationError(f"Prediction must contain exactly two classes: 0 and 1. Got: {unique_classes}")

        # Compute F1 score
        score = f1_score(truth, preds)
        return score

    except pd.errors.ParserError:
        raise EvaluationError("Failed to read CSV. Please check the file format.")
    except Exception as e:
        raise EvaluationError(str(e))