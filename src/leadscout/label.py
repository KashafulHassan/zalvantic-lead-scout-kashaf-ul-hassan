"""Apply the labelling guide (docs/labelling-guide.md) to every lead."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

AI_WORDS = ["ai", "automat", "chatbot", "invoice", "analytics", "dashboard"]
WEB_WORDS = ["backend", "e-commerce", "web", "migrate", "cloud", "scale"]


def clean(text):  # undo the leet-speak noise from week 1
    return text.replace("4", "a").replace("3", "e").lower()


VAGUE = ["not sure", "maybe", "generally", "more digital"]

def label_lead(lead):
    need = clean(lead["need"])
    timeline = lead["timeline_weeks"]
    budget = lead["budget_band"]

    clear_need = not any(w in need for w in VAGUE)

    # temperature: rules 1-3 in order
    if clear_need and budget in ("medium", "high") and timeline and timeline <= 8:
        temp = "hot"
    elif clear_need and timeline and timeline <= 16:
        temp = "warm"          # clear need, funded-or-not, but slower / cheaper
    else:
        temp = "cold"          # vague need, no timeline, or timeline > 16

    # service fit: only actionable needs get a fit
    if not clear_need:
        fit = "neither"
    else:
        is_ai = any(w in need for w in AI_WORDS)
        is_web = any(w in need for w in WEB_WORDS)
        fit = "both" if is_ai and is_web else "ai_automation" if is_ai else "web_backend"

    return temp, fit

def main():
    leads = list(csv.DictReader(open(ROOT / "data" / "synthetic_leads.csv")))
    with open(ROOT / "data" / "labels.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lead_id", "temperature", "service_fit"])
        for lead in leads:
            lead["timeline_weeks"] = int(lead["timeline_weeks"]) if lead["timeline_weeks"] else None
            temp, fit = label_lead(lead)
            w.writerow([lead["lead_id"], temp, fit])
    print(f"Labelled {len(leads)} leads")


if __name__ == "__main__":
    main()