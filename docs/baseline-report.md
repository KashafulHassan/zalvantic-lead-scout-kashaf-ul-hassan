# Baseline Report — Week 3

Model: TF-IDF (word unigrams + bigrams) → logistic regression, wrapped in a
scikit-learn pipeline, evaluated with stratified 5-fold cross-validation
(shuffle, random_state=42). Features: lead text (`need`) plus a structured
`budget=` hint appended to the text. `class_weight="balanced"` compensates for
the class imbalance (cold 95 / hot 86 / warm 39).

Run with: `python src\leadscout\baseline.py`

## Results

### Target: temperature

| Metric | Score (macro where applicable) |
|---|---|
| Accuracy | 0.877 |
| Precision (macro) | 0.840 |
| Recall (macro) | 0.863 |

Confusion matrix (rows = true, cols = predicted):

|      | cold | hot | warm |
|------|-----|-----|------|
| cold | 95  | 0   | 0    |
| hot  | 0   | 66  | 20   |
| warm | 0   | 7   | 32   |

### Target: service_fit

| Metric | Score |
|---|---|
| Accuracy | 1.000 |
| Precision (macro) | 1.000 |
| Recall (macro) | 1.000 |

Confusion matrix: perfect diagonal, no misclassifications in any class.

## Interpretation

**service_fit is perfectly predictable (1.000) — and that is not a win.**
The labels are assigned by a deterministic keyword lookup (chatbot/invoice/
dashboard → ai_automation; backend/migration → web_backend), so the TF-IDF
model just re-learns the keyword table. A perfect score here means the task
is trivial for this feature set, not that the model is impressive. It does
confirm the labelling guide is internally consistent.

**temperature is the interesting one (0.877).** The errors are structured,
not random:

- cold is never confused (95/95 correct): vague leads are trivially separable.
- The only real confusion is hot ↔ warm (20 hot leads predicted warm, 7 warm
  predicted hot). This is expected: those two classes differ *only* in budget
  and timeline, which enter the model as a single weak `budget=` token, while
  the need text is identical across styles.

**What the baseline tells week 4:** the model to beat is 0.877 accuracy on
temperature. The obvious improvement lever is not a fancier text model but
better use of the structured fields (budget_band, timeline_weeks) as explicit
features rather than a text hint — the errors already point at them.

## Honest caveats

- Metrics come from cross-validation on 220 synthetic leads generated from 6
  templates; real-world leads would be messier and scores would drop.
- The labels themselves are rule-derived, so the model is partly learning the
  labelling script, not independent ground truth.