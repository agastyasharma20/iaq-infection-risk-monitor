# Project Report: Classroom Air Quality & Infection Risk Monitor
### A Software-Only Extension of the Distributed Sensor-Based Fuzzy Decision Tree Model

---

## 1. Background & Problem Statement

Your original project deployed distributed sensors across 9 classrooms to monitor CO₂,
temperature, humidity, and thermal comfort (PMV), comparing a Fuzzy Decision Tree
against a Neural Network. Two key findings came out of that work:

1. The **Fuzzy Decision Tree outperformed the Neural Network** (9–12% vs 5–7% accuracy
   improvement over baseline).
2. **CO₂ alone is not sufficient to judge overall air quality** — a conclusion drawn
   directly from your 9-classroom data (CO₂ ranged 2000–2900 ppm during class hours).

Finding #2 is usually treated as a limitation. This project treats it as the starting
point for a new, more useful application of the exact same sensor data.

## 2. Core Idea

CO₂ is a poor *direct* indicator of general air pollution (it says nothing about dust,
VOCs, or particulates). But CO₂ **is** an excellent *indirect* indicator of something
else entirely: **how much of the air in a room has already been breathed by other
people.** This is precisely the quantity used in the well-established **Wells-Riley
model** of airborne infectious disease transmission (used in epidemiology since the
1970s, and prominently revalidated during COVID-19 for classroom/office risk
estimation).

So instead of asking *"is the air quality good?"* (a question your own data shows CO₂
can't answer alone), this project asks a **narrower, better-defined, and more
actionable question**: *"what is the relative risk of airborne infection spreading in
this room right now?"* — a question CO₂ answers very well.

## 3. What Was Built

A complete, runnable, software-only pipeline consisting of five components:

### 3.1 Data Layer (`data/`)
A sample dataset generator producing realistic 9-classroom sensor logs (CO₂,
temperature, humidity, occupancy) across 10 days, calibrated to match your own
observed CO₂ range (2000–2900 ppm during class). **This file is a stand-in** — swap
it for your real logged CSV (same column format) and everything downstream works
unchanged.

### 3.2 Risk Scoring Layer (`src/wells_riley.py`)
Implements the Wells-Riley / CO₂-rebreathed-fraction formula:

- **Rebreathed air fraction:** `f = (CO2_room − 420) / (38000 − 420)`
  (420 ppm = outdoor baseline, 38000 ppm ≈ CO₂ concentration in exhaled breath)
- **Risk score:** combines rebreathed fraction, exposure time, and a crowding factor
  (more occupants sharing the same air → higher relative risk) into a 0–1 score,
  bucketed into **Low / Medium / High**.

This is the *ground truth generator* — every sensor reading in the dataset gets
labeled with a risk category using this formula.

### 3.3 Two Predictive Models (comparison, as in your original project)

| Model | File | Role |
|---|---|---|
| Fuzzy Decision Tree | `src/fuzzy_model.py` + trained tree in `train_and_compare.py` | Predicts risk category instantly from raw sensor values, without recomputing the full formula each time — same philosophy as your original fuzzy system |
| Neural Network (MLP) | `train_and_compare.py` | Comparison baseline, as in your original study |

Both are trained on the same data and evaluated on an identical held-out test set for
a fair, direct comparison — continuing your original research question ("which model
family is better suited to this problem?") on a new target variable.

**Result on the sample dataset:** both models scored above 99% accuracy, because the
sample data's risk label is a clean mathematical function of CO₂ and occupancy. **This
is expected and is not the final result** — once you run this pipeline on your real
sensor logs (which have real-world noise, sensor drift, and irregular occupancy
patterns), you should expect to see a genuine accuracy gap between the two models,
most likely favoring the Fuzzy Tree again, consistent with your original finding.
Full classification reports and confusion matrices are saved automatically to
`reports/model_comparison.txt` and `reports/confusion_matrices.png`.

### 3.4 Live Dashboard (`dashboard/app.py`)
A Streamlit web dashboard showing all 9 classrooms simultaneously with color-coded
risk levels (🟢 Low / 🟡 Medium / 🔴 High), a time slider to scrub through logged
history, and per-room CO₂/risk trend charts. This is your demo-day deliverable — runs
in a browser with one command, no deployment infrastructure needed.

### 3.5 Documentation (`README.md`)
Step-by-step run instructions and exact guidance on swapping in your real data.

## 4. How the Pieces Connect

```
Real/Sample Sensor CSV
        │
        ▼
 wells_riley.py  ──────► labeled_data.csv (adds risk_score + risk_category)
        │
        ▼
 train_and_compare.py ──► trains Fuzzy Tree & Neural Network
        │                  saves: trained models, accuracy report, confusion matrices
        ▼
 dashboard/app.py ──────► loads trained Fuzzy Tree model, shows live risk per room
```

## 5. Why This Is a Genuine Research Contribution (Not Just a Demo)

- It **directly resolves the limitation your own data exposed** (CO₂ alone ≠ air
  quality) by re-purposing CO₂ for a use case where it is scientifically strong
  (infection risk), rather than discarding the finding.
- It **reuses a peer-reviewed, published epidemiological model** (Wells-Riley) rather
  than inventing an ad-hoc scoring system — this is defensible in a paper or viva.
- It **preserves your original research comparison** (Fuzzy vs Neural Network) so your
  new work is a continuation, not a restart — reviewers/HOD can see the throughline.
- It requires **zero new hardware**, meaning it can be deployed and validated on your
  existing 9-classroom installation immediately.

## 6. Suggested Next Steps

1. Replace the sample dataset with your real logged CSV and re-run
   `label_dataset.py` → `train_and_compare.py` to get your **real** accuracy comparison.
2. If your real Fuzzy Tree again beats the Neural Network, that becomes your headline
   result — the same finding, now validated on a second, independently meaningful
   target variable (infection risk, not just comfort).
3. For a stronger paper, add a short literature section citing the original
   Wells-Riley (1978) and Rudnick & Milton (2003) CO₂-based risk estimation papers —
   both are standard, widely cited references you can look up and cite properly.
4. Optionally extend the dashboard with an SMS/email alert when any room crosses into
   "High" risk — a small, low-effort addition with high demo impact.

## 7. Limitations to State Honestly (in your report/viva)

- The Wells-Riley model here uses simplified, literature-typical parameter values
  (quanta generation rate, exhaled CO₂ concentration) rather than disease-specific,
  measured values — it produces a **relative** risk index for comparing rooms/times,
  not a clinically validated absolute infection probability.
- Occupancy readings in the sample dataset are simulated; if your real deployment
  doesn't log occupancy directly, you'll need a proxy (e.g., timetable-based headcount
  or a simple manual entry) for this model to work on real data.
