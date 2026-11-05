"""Generate synthetic leads in varied styles, with noise and ambiguity."""
import csv, random, uuid
from pathlib import Path
from faker import Faker
from leadscout.schema import Lead, BudgetBand

fake = Faker()
random.seed(42)  # reproducible: same data every run

NEEDS = [
    "automate invoice processing with AI",
    "redesign our e-commerce backend for scale",
    "build a customer support chatbot",
    "migrate our data pipeline to the cloud",
    "dashboard for sales analytics",
]

def style_professional():
    """Clear need + budget + timeline. The easy case."""
    return {
        "need": f"We need a vendor to {random.choice(NEEDS)}. Please send a proposal.",
        "budget_band": random.choice([BudgetBand.medium, BudgetBand.high]),
        "timeline_weeks": random.randint(4, 12),
    }

def style_vague():
    """Unclear need, no budget, no timeline. Hard to act on."""
    return {
        "need": random.choice([
            "not sure, maybe something with AI?",
            "we want more digital. reach out.",
            "improve things generally.",
        ]),
        "budget_band": BudgetBand.unknown,
        "timeline_weeks": None,
    }

def style_budget_conscious():
    """Clear need, but explicitly cheap and slow."""
    return {
        "need": f"Looking for the cheapest option to {random.choice(NEEDS)}.",
        "budget_band": BudgetBand.low,
        "timeline_weeks": random.randint(20, 50),
    }

def style_urgent():
    """Clear need, short timeline, willing to pay."""
    return {
        "need": f"URGENT: need to {random.choice(NEEDS)} within weeks. Budget approved.",
        "budget_band": BudgetBand.high,
        "timeline_weeks": random.randint(1, 8),
    }

def style_noisy():
    """Typos, no punctuation, lowercase. Realistic messy input."""
    base = f"we wnt to {random.choice(NEEDS)} asap, send detials"
    noisy = base.replace("a", "4").replace("e", "3", 3)  # light leet corruption
    return {"need": noisy, "budget_band": BudgetBand.unknown, "timeline_weeks": None}

def style_ambiguous():
    """Deliberately borderline: need is clear but budget/timeline conflict."""
    return {
        "need": f"We'd like to {random.choice(NEEDS)}, but budget isn't decided yet and the board meets next month.",
        "budget_band": random.choice([BudgetBand.low, BudgetBand.unknown]),
        "timeline_weeks": random.randint(6, 14),
    }

STYLES = [style_professional, style_vague, style_budget_conscious,
          style_urgent, style_noisy, style_ambiguous]  # 6 styles > 5 required


def make_lead(i):
    style = random.choices(STYLES, weights=[30, 20, 15, 15, 10, 10])[0]
    fields = style()
    return Lead(
        lead_id=f"lead-{i:04d}",
        name=fake.name(),
        company=fake.company(),
        country=fake.country(),
        **fields,
    )


def main(n=220, out="data/synthetic_leads.csv"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    leads = [make_lead(i) for i in range(1, n + 1)]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(leads[0].model_dump().keys()))
        w.writeheader()
        for l in leads:
            w.writerow(l.model_dump())
    print(f"Wrote {len(leads)} leads to {out}")


if __name__ == "__main__":
    main()