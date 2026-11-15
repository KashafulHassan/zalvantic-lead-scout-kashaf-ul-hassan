# Labelling Guide — Lead Scout

This guide defines how every lead in `data/synthetic_leads.csv` is labelled with
two labels: `temperature` and `service_fit`. Follow the rules in order. If a lead
does not clearly fit any rule, label it with your best judgement and list it in
the "Ambiguous cases" section at the bottom.

## Labels

- **temperature**: `hot` | `warm` | `cold`
- **service_fit**: `ai_automation` | `web_backend` | `both` | `neither`

## Temperature rules (apply in order, first match wins)

| # | Condition | Label |
|---|---|---|
| 1 | Clear need + stated budget (medium or high) + timeline ≤ 8 weeks | **hot** |
| 2 | Clear need, but budget is low, unknown, or undecided; or timeline is 9–16 weeks | **warm** |
| 3 | Vague or unclear need, or no budget and no timeline, or timeline > 16 weeks | **cold** |

**"Clear need"** means the text says what they want built (e.g. "automate invoice
processing"), not just "improve things" or "not sure, maybe something with AI?".

**"Stated budget"** means `medium` or `high`. A `low` budget shows price
sensitivity, not commitment, so it can never make a lead hot.

**"Undecided budget"** ("budget isn't decided yet, board meets next month") is
treated like `unknown`: the need is real but not yet funded → at most **warm**.

## Service fit rules

| If the need mentions... | Label |
|---|---|
| AI/automation work (chatbot, invoice processing automation, analytics dashboard) **and** web/backend work (backend redesign, e-commerce platform, cloud migration) | **both** |
| Only AI/automation work | **ai_automation** |
| Only web/backend/infrastructure work | **web_backend** |
| Nothing actionable, or too vague to tell | **neither** |

Mapping of the needs that appear in this dataset:

| Need text | service_fit |
|---|---|
| "automate invoice processing with AI" | ai_automation |
| "build a customer support chatbot" | ai_automation |
| "dashboard for sales analytics" | ai_automation |
| "redesign our e-commerce backend for scale" | web_backend |
| "migrate our data pipeline to the cloud" | web_backend (infrastructure work, not modelling) |
| "we want more digital. reach out." / "improve things generally." / "not sure, maybe something with AI?" | neither (mentions of "AI" here are not an actionable need) |

## Worked examples (real rows from synthetic_leads.csv)

**lead-0006** — "We need a vendor to dashboard for sales analytics. Please send a proposal." — budget high, 7 weeks → **hot / ai_automation**. Clear need, stated high budget, timeline ≤ 8.

**lead-0002** — "We need a vendor to redesign our e-commerce backend for scale." — budget medium, 5 weeks → **hot / web_backend**. Meets all three hot conditions.

**lead-0005** — same need, budget medium, 12 weeks → **warm / web_backend**. Clear need, but timeline is 9–16.

**lead-0027** — "We need a vendor to automate invoice processing with AI." — budget high, 10 weeks → **warm / ai_automation**. Stated budget but timeline > 8.

**lead-0001** — "Looking for the cheapest option to automate invoice processing with AI." — budget low, 43 weeks → **cold / ai_automation**. Low budget and timeline > 16.

**lead-0007** — "we want more digital. reach out." — budget unknown, no timeline → **cold / neither**. No clear need, nothing actionable.

**lead-0008** — "w3 wnt to 4utom4t3 invoic3 processing with AI 4s4p, send deti4ls" — budget unknown, no timeline → **cold / ai_automation**. Decode the noisy spelling first ("we want to automate invoice processing with AI asap"); the need is clear but there is no budget or timeline.

**lead-0038** — "We'd like to dashboard for sales analytics, but budget isn't decided yet and the board meets next month." — budget unknown, 14 weeks → **warm / ai_automation**. Clear need, but an undecided budget can never be hot.

## Ambiguous cases

These leads sit between two rules. Judgement calls made, with reasons:

- **lead-0044** (chatbot, low budget, 8 weeks): timeline qualifies for hot but budget is low → **warm**.
- **lead-0115** (backend redesign, low budget, 8 weeks): same conflict → **warm**.
- **lead-0192** (backend redesign, low budget, 8 weeks): same conflict → **warm**.
- **lead-0125** (dashboard, unknown budget, 6 weeks): timeline qualifies for hot but budget undecided → **warm**.
- **lead-0135** (dashboard, unknown budget, 7 weeks): same conflict → **warm**.
- **lead-0008, lead-0013, lead-0019, lead-0026... (all noisy-style leads)**: need is clear after decoding, but budget and timeline are missing entirely → **cold** by rule 3. If "asap" were counted as a timeline, these would be warm; we count only explicit week numbers.
- **lead-0010, lead-0033, lead-0045... (all "not sure, maybe something with AI?")**: "AI" is mentioned, but there is no actionable need → **neither**, not `ai_automation`.

Full ambiguous list (ambiguous style + noisy style): lead-0007, lead-0008, lead-0010, lead-0012, lead-0013, lead-0019, lead-0021, lead-0024, lead-0026, lead-0033, lead-0037, lead-0038, lead-0039, lead-0043, lead-0044, lead-0045, lead-0053, lead-0062, lead-0070, lead-0074, lead-0075, lead-0076, lead-0078, lead-0090, lead-0100, lead-0109, lead-0115, lead-0125, lead-0135, lead-0140, lead-0160, lead-0175, lead-0182, lead-0192.

## Annotator agreement (round 2)

30 leads relabelled blind 3 days after round 1 (Cohen's kappa, sklearn):

- temperature: **0.821** (strong)
- service_fit: **0.948** (near-perfect)

Interpretation: the guide is reproducible. Temperature agreement is slightly
lower because hot/warm/cold depends on combining three fields (need, budget,
timeline), while service_fit is a direct keyword lookup. No systematic
disagreements were found; the first scoring attempt (kappa 0.165) was invalid
because matched keywords were written instead of final labels, and was redone.