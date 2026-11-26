# Model Comparison — Week 4

Three approaches evaluated on all 220 labelled leads, identical protocol:
stratified 5-fold CV (random_state=42) for both trained models; the LLM is
zero-shot (trains on nothing), so predicting the full set covers the same data.

| Model | Trained? | temperature acc | temp macro P | temp macro R | service_fit acc | Cost / 220 leads |
|---|---|---|---|---|---|---|
| TF-IDF + LR (week 3 baseline) | yes | 0.877 | 0.840 | 0.863 | 1.000 | free, seconds |
| MiniLM embeddings + LR | yes | 0.873 | 0.836 | 0.859 | 1.000 | free, seconds |
| LLM zero-shot (gpt-oss-20b, Groq) | no | **0.964** | 0.946 | 0.972 | **1.000** | free tier, 220 API calls |

## Winner: LLM zero-shot (0.964 temperature accuracy)

## Interpretation

- **The two trained text classifiers are statistically identical** (0.877 vs
  0.873) and fail identically: all errors are hot↔warm (TF-IDF 20+7, embeddings
  21+7). The discriminating signal for hot vs warm is budget and timeline, which
  both models only see as one weak text hint. Semantic text quality is not the
  bottleneck.
- **The LLM wins for a structural reason, not a modelling one**: the prompt
  gives it the budget/timeline values and the guide's decision rules, so it can
  apply the actual logic ("high budget but 10 weeks → warm"). Its remaining
  errors: 8 cold leads predicted hot/warm.
- service_fit is 1.000 everywhere because labels come from a keyword lookup —
  a trivial task for all three (see week 3 caveat).

## Decision

Week 4 conclusion: build on the LLM zero-shot for accuracy; keep the TF-IDF
pipeline as the cost/latency fallback for bulk scoring. The obvious week-5
lever for a trained model: feed budget_band and timeline_weeks as explicit
structured features instead of text hints.

## Caveats

- Synthetic template data; real-world scores would drop for all three.
- LLM scores depend on prompt wording, temperature=0 determinism, and provider
  quota; the two sklearn models are free and instant at inference.