"""Embedding-based classifier: MiniLM embeddings + LR, same stratified folds."""
from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_score,
                             recall_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict

ROOT = Path(__file__).resolve().parents[2]
RANDOM_STATE = 42


def main():
    df = pd.read_csv(ROOT / "data" / "synthetic_leads.csv").merge(
        pd.read_csv(ROOT / "data" / "labels.csv"), on="lead_id")
    df["text"] = df["need"].fillna("") + " budget=" + df["budget_band"].fillna("unknown")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    X = model.encode(df["text"].tolist(), show_progress_bar=True)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    for target in ["temperature", "service_fit"]:
        y = df[target]
        pred = cross_val_predict(LogisticRegression(max_iter=1000,
                                                   class_weight="balanced"),
                                 X, y, cv=skf)
        print(f"\n=== embeddings, target: {target} ===")
        print(f"accuracy : {accuracy_score(y, pred):.3f}")
        print(f"precision: {precision_score(y, pred, average='macro', zero_division=0):.3f}")
        print(f"recall   : {recall_score(y, pred, average='macro', zero_division=0):.3f}")
        classes = sorted(y.unique())
        print(pd.DataFrame(confusion_matrix(y, pred), index=classes, columns=classes))


if __name__ == "__main__":
    main()