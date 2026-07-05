# V3 Upgrade Report: From Decision-Support System to Autonomous Building Intelligence

## 1. Where V3 sits in the project's arc

- **V1** answered: *"what is the infection risk right now?"* (Fuzzy Tree vs Neural
  Network, Wells-Riley based)
- **V2** answered: *"what should I do about it, and why?"* (forecasting,
  explainability, root-cause, alerting, API)
- **V3** answers: *"what happens if I act, which action is best, is my data even
  trustworthy, and can I prove this system is production-grade?"* — moving from a
  smart classifier into something closer to what your original brainstorm called an
  "Autonomous Building Brain."

## 2. New modules, in detail

### 2.1 Database layer (`db.py`)
**What it does:** Replaces V2's flat CSV alert log with a proper SQLite database
(via SQLAlchemy) holding three tables: `alerts`, `model_registry`, and
`sensor_anomalies`. Any of these can now be queried properly (e.g. "all High alerts
for Room_3 in the last 7 days") instead of loading and filtering an entire CSV.

**Why this matters:** This is the single biggest engineering-maturity signal in V3.
Moving from CSV to a real database — with a schema, and room to swap in
Postgres/MySQL later by changing one connection string — is exactly the kind of
change that separates "a script" from "a system."

### 2.2 Digital Twin simulator (`src/digital_twin.py`)
**What it does:** Given a room's current CO₂ and occupancy, projects its risk
trajectory forward in time under three interventions — no action, opening windows,
or reducing occupancy — reusing the same physics-style mass-balance model from your
sample data generator, now exposed as an interactive, parameterized function.

**A genuinely interesting finding it surfaced:** at extreme crowding (e.g. 50 students,
2800 ppm), opening windows alone barely helps — CO₂ generation from that many people
outpaces even a 3x ventilation boost. Only reducing occupancy meaningfully lowers
risk in that scenario. At moderate crowding (30 students, 1800 ppm), opening windows
works well on its own. **This is a real, defensible, reportable result** — it shows
the intervention that works depends on how crowded the room already is, which is
exactly the kind of nuance a static Wells-Riley score alone wouldn't surface.

### 2.3 RL Ventilation Advisor (`src/rl_advisor.py`)
**What it does:** A tabular Q-learning agent, trained inside the Digital Twin
environment, learns which action to recommend for a given (CO₂, occupancy) state —
balancing risk reduction against a simple cost for each action (opening windows costs
a little energy; reducing occupancy costs more, since it disrupts class time).

**Honest limitation (state this in your report/viva):** this is a **single-step
(bandit-style)** Q-learning setup — each training episode evaluates one action's
5-minute-ahead outcome, not a full multi-step trajectory. That's a legitimate,
defensible simplification for a first RL implementation (it trains in seconds and is
fully inspectable — you can print the whole Q-table), but it should be described as
"a demonstration of the RL concept applied to this problem," not "a fully validated
multi-step control policy." A natural next step (V4?) would be a proper multi-step
MDP with discounted returns over a full class period.

### 2.4 Sensor anomaly detection (`src/anomaly_detection.py`)
**What it does:** Two complementary layers:
1. **Hard physical bounds check** — instantly catches impossible values (CO₂ > 5000
   ppm, temperature outside 10–45°C, etc.)
2. **Isolation Forest** — catches subtler, multi-feature statistical outliers that
   are individually plausible but jointly unusual (e.g. a cold, dry room reporting
   high CO₂ and high occupancy simultaneously).

**A real bug I found and fixed while building this:** Isolation Forest alone missed
an obviously impossible CO₂ reading (9999 ppm) in initial testing. This is a
documented limitation of the algorithm — split thresholds are drawn from the training
data's observed range, so a point sitting at an extreme edge isn't always isolated
quickly. The fix was adding the hard-bounds layer as a safety net rather than relying
on the ML model alone. **This is worth mentioning in a viva** — it shows you
validated the system rather than assuming a published algorithm works perfectly out
of the box.

### 2.5 Model registry & versioning (integrated into `db.py` + `train_and_compare.py`)
**What it does:** Every time you train a model, it's logged with its accuracy and
timestamp. If it beats the current "champion" of its type, it's automatically
promoted. Over time, this builds a visible history of model improvement — genuinely
useful if you retrain periodically as you collect more real data.

### 2.6 API security (`api/main.py`)
**What it does:** All data endpoints now require a `X-API-Key` header matching the
value in `config.yaml`. Verified: requests without the correct key are rejected with
HTTP 401.

**Honest limitation:** this is a single shared static key, not per-user
authentication — adequate for a student project or internal tool, not for a
multi-tenant production service. Worth stating plainly if asked.

### 2.7 Five new API endpoints
- `POST /simulate` — Digital Twin projection for one action
- `POST /simulate/compare_all` — all three actions side by side
- `GET /recommend` — RL advisor's recommended action for a given state
- `GET /alerts` — recent alert history from the database
- `GET /model_history` — full model registry history

### 2.8 Automated PDF reports (`src/report_generator.py`)
**What it does:** Generates a two-page, professional PDF per room: a risk-level
breakdown table, a trend chart, the room's alert history, and an appendix showing
current model performance. Built with reportlab, verified visually (not just "it ran
without errors") before shipping.

### 2.9 Multi-page dashboard
The single-page V2 dashboard is now 7 focused pages (Home, Room Detail, Digital Twin,
RL Advisor, Sensor Health, Alerts & Models, Reports) — each independently testable
(all 7 verified with Streamlit's `AppTest` headless harness, zero exceptions) and
easier to navigate in a live demo than one long scrolling page.

## 3. What did NOT change (intentionally)

- The Wells-Riley formula and the Fuzzy Tree vs Neural Network comparison — still
  your core scientific result, untouched since V1.
- No new hardware, anywhere. V3 is still 100% software.

## 4. Bugs found and fixed during this build (worth knowing about)

1. **Digital Twin parameter naming inconsistency** — `simulate()` originally used
   `co2_now`/`occupancy_now` while the rest of the codebase uses `co2_ppm`/`occupancy`.
   Caught by the test suite, not by manual testing — a good example of why the tests
   exist.
2. **NumPy bool vs Python bool** — `check_reading_for_anomaly()` was returning
   `numpy.False_` instead of Python's `False`, which passed casual inspection
   (`print()` shows the same thing) but failed a strict `assert flagged is False`
   test. Fixed by explicit `bool()` casting.
3. **Isolation Forest missing an extreme univariate outlier** — described in 2.4
   above.

All three were caught because the test suite was run, not assumed to pass — a
genuinely useful thing to mention if asked "how do you know this works?"

## 5. Suggested viva/report narrative for V3

1. Recap V1 (core science) and V2 (decision support).
2. Present V3 as "from decision support to controllable, trustworthy system":
   - Digital Twin + RL advisor answer "what should I actually do?"
   - Anomaly detection answers "can I trust this data?"
   - Database + model registry + tests + CI answer "is this maintainable, not just a
     one-off script?"
3. Use the Digital Twin's crowding finding (section 2.2) as a concrete, novel result
   distinct from the V1 Fuzzy-vs-NN comparison.
4. Be upfront about the two honest limitations (RL is single-step; API auth is a
   shared key) — stating limitations you're aware of reads as more credible than
   claiming a finished production system.

## 6. Suggested V4 directions, if you continue further
- Multi-step RL (proper MDP over a full class period, not single-step)
- Federated learning across multiple classrooms/institutions (from your original
  brainstorm's Cluster D)
- Real email/SMS notification integration (currently a logged placeholder)
- Per-user API authentication instead of a shared key
- GNN-based cross-room pollutant propagation modeling (from Cluster E of your
  original brainstorm) — the most research-novel direction still untouched
