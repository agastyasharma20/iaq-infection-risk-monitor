# V2 Upgrade Report: From Working Prototype to Deployable System

## 1. Why V2, and what changed conceptually

V1 answered one question well: *"what is the infection risk in this classroom right
now?"* — using the Wells-Riley formula and a Fuzzy Decision Tree vs Neural Network
comparison, exactly continuing your original research thread.

V2 turns that single answer into a **complete decision-support system** by adding four
new capabilities on top of the same core model, plus the engineering scaffolding
needed to actually ship and maintain it:

1. **Forecasting** — don't just report current risk, predict where it's heading
2. **Explainability** — don't just say "High risk", say *why*
3. **Root-cause diagnosis** — turn the explanation into an actionable label
4. **Alerting** — close the loop by automatically flagging dangerous rooms

And the production layer around them:

5. A REST API (so the model isn't locked inside one dashboard)
6. Centralized configuration (no more hunting through files to change a threshold)
7. Proper logging (a real audit trail, not scattered print statements)
8. Automated tests (proof the system works, checked automatically)
9. Containerization (Docker — runs identically anywhere)
10. CI/CD (GitHub Actions — every push is automatically verified)

## 2. Detailed breakdown of each new module

### 2.1 Forecasting (`src/forecast_model.py`)
**What it does:** Predicts the risk score ~1 hour ahead (4 steps × 15 minutes) for a
room, using its last 4 readings of CO₂, temperature, humidity, and occupancy as lag
features, fed into a Gradient Boosting Regressor.

**Why this matters:** Your V1 system is reactive — it tells you a room is already
risky. V2's forecast lets a teacher or facilities officer act *before* the room
becomes risky (e.g., "risk is trending toward High in the next hour — open windows
now"), which is a materially different and more useful capability.

**How it was validated:** Trained and tested with a held-out split; Mean Absolute
Error (MAE) on the risk score (0–1 scale) is logged and saved alongside the model, so
you always know how reliable the forecast currently is.

### 2.2 Explainability (`src/explainability.py`)
**What it does:** Uses SHAP (SHapley Additive exPlanations), a standard, published,
model-agnostic explainability technique, to compute exactly how much each input
feature (CO₂, temperature, humidity, occupancy) pushed the prediction toward its
predicted risk category.

**Why this matters:** "High risk" alone isn't actionable. Knowing *occupancy* is the
dominant driver (vs. a stale, poorly-ventilated baseline) tells you whether the fix is
"let some students step out" or "open a window" — genuinely different actions.

### 2.3 Root-cause diagnosis (`src/explainability.py::diagnose_root_cause`)
**What it does:** A simple, transparent rule layered on top of the SHAP output,
translating numeric contributions into one of: *Overcrowding*, *Poor Ventilation
Baseline*, *Combined*, or *Normal*.

**Why this is defensible in a report/viva:** It's not a black box — the rule is
plain, auditable, and directly traceable to the SHAP values that produced it. This
is the "Explainable AI" and "Bayesian-style diagnosis" ideas from your original
brainstorm, implemented in the simplest form that's still genuinely useful.

### 2.4 Alerting (`src/alerts.py`)
**What it does:** Whenever a room's predicted risk is "High" (or your configured
trigger category — from `config.yaml`), logs a timestamped alert to
`data/alerts_log.csv` and simulates a notification (a log line for now — swap in a
real email/SMS call later without touching any other code). A cooldown prevents the
same room from re-alerting every 15 minutes while it stays High.

### 2.5 REST API (`api/main.py`)
**What it does:** Exposes `/predict` (full explainable prediction + alert check) and
`/health` over HTTP using FastAPI, with automatic interactive documentation at
`/docs`.

**Why this matters for you specifically:** Right now, the model logic lives inside
the Streamlit dashboard. An API decouples them — the same model could serve a mobile
app, a college-wide dashboard, or another team's tool, without duplicating code. This
is also the standard shape a real deployment takes (dashboard and API as separate,
independently scalable services — see `docker-compose.yml`).

### 2.6 Config (`config.yaml`, `config_loader.py`)
**What it does:** Every threshold, path, and hyperparameter that used to be hardcoded
across multiple files now lives in one YAML file. Change `risk_thresholds.medium_max`
once, and every module (training, dashboard, API) picks it up automatically.

### 2.7 Logging (`logging_setup.py`)
**What it does:** Structured, timestamped logs to both console and a rotating file
(`logs/project.log`, capped at 1MB × 3 backups so it never grows unbounded). Every
training run, prediction, and alert is now traceable after the fact.

### 2.8 Tests (`tests/`)
**What it does:** 10 automated tests covering the risk formula's edge cases (empty
room = zero risk, monotonic increase with CO₂/occupancy, category boundaries) and the
trained model's basic sanity (valid output categories, low-input → Low risk,
explainability output shape). Run anytime with `pytest tests/ -v`.

### 2.9 Docker (`Dockerfile`, `dashboard.Dockerfile`, `docker-compose.yml`)
**What it does:** Packages the API and dashboard as two independent containers that
can be built and run identically on any machine (yours, a cloud VM, a free hosting
tier) with one command: `docker-compose up --build`. Not run yet, per your instruction
to prepare deployment but not execute it — but fully ready when you are.

### 2.10 CI/CD (`.github/workflows/ci.yml`)
**What it does:** On every `git push`, GitHub automatically: installs dependencies,
regenerates sample data, trains all models, and runs the full test suite. A green
checkmark on your repo means the entire pipeline — not just isolated code — actually
works, verified by a machine, not just by you saying so.

## 3. What did NOT change (intentionally)

- The Wells-Riley formula (`src/wells_riley.py`) — your core scientific contribution,
  untouched.
- The Fuzzy Decision Tree vs Neural Network comparison (`src/train_and_compare.py`) —
  still your headline research result, still comparable directly to your original V1
  findings.
- No new hardware, anywhere. V2 is 100% software, exactly as requested.

## 4. Suggested order for your viva/report narrative

1. Recap V1: the fuzzy-vs-neural-network comparison and the CO₂ limitation finding.
2. Introduce the Wells-Riley reframing (already in your V1 report).
3. Present V2 as the "from research result to usable system" layer: forecasting,
   explainability, alerting — each answers a specific "so what do I do" question a
   reviewer or your HOD is likely to ask.
4. Close with the engineering maturity signals: tests passing, CI badge, Docker-ready,
   API-documented — these read as "this could actually be deployed," which is a much
   stronger note to end on than "this is a prototype."

## 5. Honest limitations to state alongside this (don't oversell)

- The forecasting model's accuracy (MAE) depends entirely on how well your *real*
  occupancy/CO₂ dynamics resemble the training data — re-validate MAE on real data
  before quoting a number in a paper.
- The root-cause diagnosis is a simple heuristic on top of SHAP values, not a full
  causal/Bayesian inference model — described as such, it's defensible; described as
  "AI reasoning," it would be overselling a straightforward rule.
- The alerting "notification" is currently a log line, not a real email/SMS — clearly
  labeled as a placeholder in the code, and should stay described that way until
  you wire up a real channel.
