# V5 Upgrade Report: Fixing Honest Limitations, Adding the Last Big Research Idea

## 1. What V5 focused on

V4 gave the project its USP (the orchestrator). V5's job was different: **fix the two
things I was explicitly honest about being limitations in earlier reports**, and add
the one genuinely research-novel idea from the original brainstorm that was still
missing -- graph-based cross-room modeling.

This is a deliberately different kind of upgrade than V1-V4: less "add a new tool,"
more "make the existing tools actually correct and complete."

## 2. What changed, in detail

### 2.1 Multi-step Reinforcement Learning (fixes a stated V3/V4 limitation)
**The old problem:** the V3/V4 RL advisor trained on single 5-minute-ahead outcomes
only -- a bandit, not a real sequential decision process. This was stated explicitly
in both earlier reports rather than hidden.

**The fix:** `rl_advisor.py` now trains over genuine multi-step episodes -- each
training episode runs a full simulated trajectory (multiple decision points across a
longer time horizon) with properly discounted returns, so the agent learns to value
actions based on their actual longer-term consequences, not just the next 5 minutes.
The public interface (`recommend_action()`) didn't change, so nothing downstream (the
orchestrator, the dashboard, the API) needed to change -- verified by the full test
suite passing unchanged.

### 2.2 Graph-based cross-room risk propagation (`src/graph_propagation.py`)
**The idea, from the original brainstorm's Graph Neural Network cluster:** every
model in this project so far predicts each room's risk completely independently. In
a real building, that's not physically accurate -- Room_3 being overcrowded and
poorly ventilated realistically affects Room_4 next door through shared corridor air
and HVAC return ducts.

**What was actually built, described honestly:** a single-layer graph convolution --
each room's risk score is blended with a weighted average of its graph-neighbors'
risk scores. This is **not** a deep, multi-layer, learned-embedding GNN (that would
need PyTorch Geometric and far more training data than a 9-classroom deployment
realistically has). It's the simplest legitimate member of the GNN family, and it's
described that way in the code -- this honesty is worth keeping in your report rather
than calling it "a GNN" without qualification.

**Concrete, tested output:** `find_escalation_risks()` identifies rooms that look
safe in isolation but get pulled into a worse category once neighbors are accounted
for. Verified with a real scenario: a room sandwiched between two High-risk
neighbors gets escalated from Low to Medium, while an unaffected room elsewhere in
the building correctly stays unchanged.

**Honest caveat to state clearly:** the room-adjacency graph used here
(`build_building_graph()`) is a **placeholder 3x3 grid guess**, not PIEMR's real
floor plan. This is clearly labeled in both the code and the dashboard page --
replace it with real adjacency data before trusting the output for an actual building.

### 2.3 Building Health History + Trends (`db.py`, `backfill_health_history.py`, Trends page)
V4's Building Health Score was a snapshot -- one number, right now. V5 adds a new
database table (`BuildingHealthLog`) and logs a snapshot every time the monitoring
loop runs. A new backfill script (`backfill_health_history.py`) retroactively
populates this from your existing historical data too, so the new Trends dashboard
page has something meaningful to show immediately rather than requiring days of live
monitoring first. Verified: backfilling the full 10-day sample dataset correctly
logged 480 snapshots (one per timestamp).

### 2.4 Public status endpoint (`GET /public/status`)
Every other data endpoint requires the API key. This one deliberately does not --
it's meant to be the one thing shown to external stakeholders (a public status page,
a Smart City transparency dashboard) without exposing room-level detail, alert
history, or any model internals. Returns only the single aggregate Building Health
Score and grade. Verified live: reachable with zero authentication, while every other
endpoint still correctly rejects unauthenticated requests.

### 2.5 New API endpoint: `/building_graph`
Makes the cross-room propagation model callable directly -- send in each room's
independent prediction, get back the neighbor-adjusted scores and any escalations.
Verified live with a real 9-room scenario.

### 2.6 Two new dashboard pages
- **Trends** -- Building Health Score over time, average score, and a grade
  distribution chart for the whole logged period.
- **Cross-Room Risk** -- an interactive version of the graph propagation model, with
  an adjustable "neighbor influence weight" slider so you can see how sensitive the
  escalation detection is to that assumption.

## 3. Bugs found and fixed while building V5

1. **Missing import in `api/main.py`.** Added a call to `get_building_health_history()`
   inside the new `/public/status` endpoint without importing it -- the server failed
   to start. Caught immediately by actually starting the server and testing the
   endpoint with curl, not by just reading the code.
2. **`np.str_` leaking into API responses.** The graph propagation module's neighbor
   lists initially contained numpy string types instead of plain Python strings,
   which would have produced subtly malformed JSON in the API. Fixed by explicit
   `str()` casting, verified with an actual `json.dumps()` test.

Both are now covered by tests (`test_graph_propagation_json_serializable_neighbor_types`
specifically exists because of bug #2) so they can't silently regress.

## 4. Full project test count, for reference
- V1: 0 automated tests (manual verification only)
- V2: 10 tests
- V3: 21 tests
- V4: 31 tests
- **V5: 39 tests**, including the project's first genuine end-to-end integration test
  (`test_full_monitoring_cycle_integration`), which runs the entire pipeline -- every
  room, through the full orchestrator, aggregated into a building health score -- as
  a single automated check.

## 5. What honestly did NOT change
- The Wells-Riley formula and Fuzzy Tree vs Neural Network comparison -- still the
  V1 core result, untouched across all five versions.
- Still 100% software, no hardware, at every version.
- The RL advisor's action space (no_action / open_windows / reduce_occupancy) and
  cost structure are unchanged -- V5 made the *training* more rigorous, not the
  underlying problem formulation.

## 6. How to talk about V5 in a report/viva

**Do say:**
- "V5 was a maturity pass: I fixed the two limitations I explicitly flagged in
  earlier versions rather than leaving them and moving on to something flashier."
- "The graph propagation model is a single-layer graph convolution, the simplest
  legitimate member of the GNN family -- appropriate for a 9-classroom dataset, where
  a deep GNN would be overkill and undertrained."
- "The project now has a genuine end-to-end integration test, not just isolated unit
  tests per module."

**Don't oversell:**
- The room adjacency graph is a placeholder layout, not the real floor plan --
  say this explicitly if asked, and treat replacing it as a clear, concrete next step.
- "Multi-step RL" here means genuine sequential training, not a claim that the policy
  has been validated against real building behavior yet -- that still requires real
  data.

## 7. Natural V6 directions, if this continues
- Replace the placeholder room-adjacency graph with the real floor plan
- Validate the RL policy and graph propagation model against real sensor data once
  available (everything so far is validated on the sample generator's synthetic data)
- Federated learning across multiple institutions (from the original brainstorm's
  Cluster D) -- the last major untouched idea from the initial research brainstorm
- Per-user authentication for the API instead of a single shared key
