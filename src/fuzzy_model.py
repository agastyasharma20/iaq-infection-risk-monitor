"""
fuzzy_model.py
--------------
Fuzzy Logic classifier that predicts risk_category directly from raw
sensor readings (co2_ppm, occupancy) WITHOUT needing to recompute the
full Wells-Riley formula every time. This is the same style of model
family that already outperformed the Neural Network in your original
project (fuzzy logic handles "vague/overlapping" categories like
Low/Medium/High better than hard thresholds).

Uses scikit-fuzzy to define membership functions and rules, mirroring
how your original PMV-based fuzzy decision tree worked, just retargeted
to predict infection risk category instead of thermal comfort.
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ---- Define fuzzy input variables ----
co2 = ctrl.Antecedent(np.arange(400, 3300, 10), 'co2')
occupancy = ctrl.Antecedent(np.arange(0, 65, 1), 'occupancy')

# ---- Define fuzzy output variable ----
risk = ctrl.Consequent(np.arange(0, 1.01, 0.01), 'risk')

# ---- Membership functions (based on ranges observed in your own data) ----
co2['low'] = fuzz.trimf(co2.universe, [400, 400, 1200])
co2['medium'] = fuzz.trimf(co2.universe, [800, 1800, 2600])
co2['high'] = fuzz.trimf(co2.universe, [2000, 3300, 3300])

occupancy['low'] = fuzz.trimf(occupancy.universe, [0, 0, 25])
occupancy['medium'] = fuzz.trimf(occupancy.universe, [15, 32, 48])
occupancy['high'] = fuzz.trimf(occupancy.universe, [38, 64, 64])

risk['low'] = fuzz.trimf(risk.universe, [0, 0, 0.35])
risk['medium'] = fuzz.trimf(risk.universe, [0.2, 0.45, 0.7])
risk['high'] = fuzz.trimf(risk.universe, [0.55, 1, 1])

# ---- Fuzzy rules (this IS the "decision tree" logic, expressed as rules) ----
rules = [
    ctrl.Rule(co2['low'] & occupancy['low'], risk['low']),
    ctrl.Rule(co2['low'] & occupancy['medium'], risk['low']),
    ctrl.Rule(co2['low'] & occupancy['high'], risk['medium']),
    ctrl.Rule(co2['medium'] & occupancy['low'], risk['low']),
    ctrl.Rule(co2['medium'] & occupancy['medium'], risk['medium']),
    ctrl.Rule(co2['medium'] & occupancy['high'], risk['high']),
    ctrl.Rule(co2['high'] & occupancy['low'], risk['medium']),
    ctrl.Rule(co2['high'] & occupancy['medium'], risk['high']),
    ctrl.Rule(co2['high'] & occupancy['high'], risk['high']),
]

risk_ctrl_system = ctrl.ControlSystem(rules)


def predict_risk_fuzzy(co2_ppm: float, occ: int) -> tuple:
    """
    Runs the fuzzy inference system on a single reading.
    Returns (risk_score, risk_category_string).
    """
    sim = ctrl.ControlSystemSimulation(risk_ctrl_system)
    sim.input['co2'] = float(np.clip(co2_ppm, 400, 3299))
    sim.input['occupancy'] = float(np.clip(occ, 0, 64))
    sim.compute()
    score = sim.output['risk']

    if score < 0.20:
        category = "Low"
    elif score < 0.45:
        category = "Medium"
    else:
        category = "High"
    return score, category


if __name__ == "__main__":
    for co2_val, occ_val in [(500, 30), (1500, 40), (2500, 45), (3000, 50)]:
        s, c = predict_risk_fuzzy(co2_val, occ_val)
        print(f"CO2={co2_val}, occ={occ_val} -> fuzzy risk={s:.3f} ({c})")
