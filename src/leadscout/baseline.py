"""Week 3 baseline: TF-IDF + logistic regression, stratified CV."""
import csv
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_score,
                             recall_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[2]
RANDOM_STATE = 42


def load_data():
    leads = pd.read_csv(ROOT / "data" / "synthetic_leads.csv")
    labels = pd.read_csv(ROOT / "data" / "labels.csv")
    df = leads.merge(labels, on="lead_id")
    # text features: the message plus structured hints
    df["text"] = df["need"].fillna("") + " budget=" + df["budget_band"].fillna("unknown")
    return df


def evaluate(df, target):
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    y = df[target]
    pred = cross_val_predict(pipe, df["text"], y, cv=skf)

    print(f"\n=== target: {target} ===")
    print(f"accuracy : {accuracy_score(y, pred):.3f}")
    print(f"precision: {precision_score(y, pred, average='macro', zero_division=0):.3f}")
    print(f"recall   : {recall_score(y, pred, average='macro', zero_division=0):.3f}")
    classes = sorted(y.unique())
    print("confusion matrix (rows = true, cols = predicted):")
    print(pd.DataFrame(confusion_matrix(y, pred), index=classes, columns=classes))


def main():
    df = load_data()
    print(f"{len(df)} labelled leads")
    evaluate(df, "temperature")
    evaluate(df, "service_fit")


if __name__ == "__main__":
    main()