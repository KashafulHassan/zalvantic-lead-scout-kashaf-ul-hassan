"""LLM zero-shot classifier: applies the labelling guide via prompt."""
import json, os, re, time
from pathlib import Path
from statistics import mean
from urllib import request, error

import pandas as pd
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_score,
                             recall_score)
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[2]
URL = "https://api.groq.com/openai/v1/chat/completions"
PRED_PATH = ROOT / "data" / "llm_predictions.csv"

MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
CHAT_MODELS = {
    "qwen/qwen3.8-27b", "openai/gpt-oss-20b",
    "openai/gpt-oss-120b", "allam-2-7b",
}
LABELS = {
    "temperature": ["hot", "warm", "cold"],
    "service_fit": ["ai_automation", "web_backend", "both", "neither"],
}

PROMPT = """You label sales leads. Reply with ONE JSON object only, no markdown, no code fences, no explanation:
{{"temperature": "hot|warm|cold", "service_fit": "ai_automation|web_backend|both|neither"}}

Rules: hot = clear need + budget medium/high + timeline <= 8 weeks. warm = clear need but low/unknown budget or timeline 9-16. cold = vague need, or no budget and no timeline, or timeline > 16. service_fit: chatbot/invoice automation/dashboard = ai_automation; backend redesign/cloud migration = web_backend; both kinds = both; vague = neither.

Lead: {lead}"""


def parse_label_json(text):
    """Tolerate ```json fences / trailing prose, then validate both fields."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(),
                  flags=re.IGNORECASE).strip()
    decoder = json.JSONDecoder()
    obj = None
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(text[i:])
                break
            except json.JSONDecodeError:
                continue
    if not isinstance(obj, dict):
        raise ValueError(f"no JSON object in reply: {text[:120]!r}")

    out = {
        "temperature": str(obj.get("temperature", "")).strip().lower(),
        "service_fit": str(obj.get("service_fit", "")).strip().lower(),
    }
    if out["temperature"] not in LABELS["temperature"]:
        raise ValueError(f"bad temperature label: {out['temperature']!r}")
    if out["service_fit"] not in LABELS["service_fit"]:
        raise ValueError(f"bad service_fit label: {out['service_fit']!r}")
    return out


def ask(lead):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(lead=lead)}],
    }
    if not MODEL.startswith("openai/gpt-oss"):
        payload["temperature"] = 0

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json",
        "User-Agent": "leadscout-llm/1.0",
        "Accept": "application/json",
    }

    for attempt in range(4):
        req = request.Request(URL, data=body, headers=headers)
        try:
            raw = request.urlopen(req, timeout=60).read().decode("utf-8")
            break
        except error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                wait = 2 ** attempt
                print(f"transient HTTP {e.code}, retry in {wait}s")
                time.sleep(wait)
                continue
            print(f"Groq HTTP {e.code}: {detail[:500]}")
            raise
        except error.URLError:
            if attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise

    msg = json.loads(raw)["choices"][0]["message"]
    content = (msg.get("content") or msg.get("reasoning")
               or msg.get("reasoning_content") or "")
    if not str(content).strip():
        raise ValueError("empty model content")
    return parse_label_json(str(content))


def load_saved(n_rows):
    """Reuse a complete predictions file so metrics can be reprinted with no API calls."""
    if os.getenv("FORCE") == "1" or not PRED_PATH.exists():
        return None
    saved = pd.read_csv(PRED_PATH)
    needed = {"temperature", "service_fit", "pred_temperature", "pred_service_fit"}
    if not needed.issubset(saved.columns) or len(saved) != n_rows:
        return None
    if (saved["pred_temperature"] == "?").any() or (saved["pred_service_fit"] == "?").any():
        return None
    return saved


def main():
    df = pd.read_csv(ROOT / "data" / "synthetic_leads.csv").merge(
        pd.read_csv(ROOT / "data" / "labels.csv"), on="lead_id")

    limit = os.getenv("LIMIT")
    if limit:
        df = df.head(int(limit)).copy()
        print(f"LIMIT={len(df)} test run")

    saved = None if limit else load_saved(len(df))
    if saved is not None:
        df = saved
        print(f"reusing {PRED_PATH} ({len(df)} rows). set FORCE=1 to call Groq again")
    else:
        if not os.environ.get("GROQ_API_KEY"):
            raise SystemExit("GROQ_API_KEY not set here -> set GROQ_API_KEY=gsk_...")
        if MODEL not in CHAT_MODELS:
            print(f"WARNING: {MODEL!r} is not a chat model from check_groq.py")

        out, consecutive_failures = [], 0
        for _, row in df.iterrows():
            lead = (f"need: {row['need']} | budget: {row['budget_band']} | "
                    f"timeline_weeks: {row['timeline_weeks']}")
            try:
                out.append(ask(lead))
                consecutive_failures = 0
                time.sleep(0.7)
            except Exception as e:
                print("failed:", row["lead_id"], repr(e))
                out.append({"temperature": "?", "service_fit": "?"})
                consecutive_failures += 1

            if len(out) % 20 == 0:
                print(f"{len(out)}/{len(df)} done")
            if consecutive_failures >= 3:
                print("3 failures in a row, aborting before wasting more calls")
                break

        out.extend({"temperature": "?", "service_fit": "?"}
                   for _ in range(len(df) - len(out)))

        n_good = sum(o["temperature"] != "?" for o in out)
        print(f"got {n_good}/{len(df)} valid predictions")
        if n_good == 0:
            raise SystemExit("No valid predictions - not saving. Check model/endpoint.")

        df = df.assign(pred_temperature=[o["temperature"] for o in out],
                       pred_service_fit=[o["service_fit"] for o in out])
        df.to_csv(PRED_PATH, index=False)

    for target, pred_col in [("temperature", "pred_temperature"),
                             ("service_fit", "pred_service_fit")]:
        all_labels = LABELS[target]
        valid = df[df[pred_col].isin(all_labels)]
        if valid.empty:
            print(f"\n=== {target}: no valid predictions ===")
            continue
        y, pred = valid[target], valid[pred_col]
        # Macro P/R over classes that actually appear. Do NOT pass labels=
        # here: an absent class (service_fit "both") would be scored 0 and
        # drag a perfect result down to 0.75.
        print(f"\n=== LLM zero-shot, target: {target} ({len(valid)}/{len(df)} valid) ===")
        print(f"accuracy : {accuracy_score(y, pred):.3f}")
        print(f"precision: {precision_score(y, pred, average='macro', zero_division=0):.3f}")
        print(f"recall   : {recall_score(y, pred, average='macro', zero_division=0):.3f}")
        missing = [l for l in all_labels if l not in set(y)]
        if missing:
            print(f"note: {missing} has 0 true examples, excluded from macro P/R")
        print(pd.DataFrame(confusion_matrix(y, pred, labels=all_labels),
                           index=all_labels, columns=all_labels))

    if limit:
        print("\n(LIMIT set - skipped fold table; run the full 220 for it)")
        return

    N_SPLITS, SEED = 5, 42
    rows = []
    for target, pred_col in [("temperature", "pred_temperature"),
                             ("service_fit", "pred_service_fit")]:
        all_labels = LABELS[target]
        skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
        accs, precs, recs = [], [], []
        for _, test_idx in skf.split(df, df[target]):
            fold = df.iloc[test_idx]
            fold = fold[fold[pred_col].isin(all_labels)]
            if fold.empty:
                continue
            y, p = fold[target], fold[pred_col]
            accs.append(accuracy_score(y, p))
            precs.append(precision_score(y, p, average="macro", zero_division=0))
            recs.append(recall_score(y, p, average="macro", zero_division=0))
        rows.append({
            "model": f"llm-zero-shot/{MODEL}",
            "target": target,
            "accuracy": round(mean(accs), 3) if accs else float("nan"),
            "precision_macro": round(mean(precs), 3) if precs else float("nan"),
            "recall_macro": round(mean(recs), 3) if recs else float("nan"),
            "n_valid": int(df[pred_col].isin(all_labels).sum()),
            "folds": N_SPLITS,
        })

    print("\n=== fold-aligned LLM rows for the comparison table ===")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()