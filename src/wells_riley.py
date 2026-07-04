"""
wells_riley.py
--------------
Implements a simplified, well-established epidemiological model
(Wells-Riley, extended by Rudnick & Milton's CO2 rebreathed-fraction
method) that estimates airborne infection risk from indoor CO2 levels.

WHY THIS WORKS WITHOUT NEW HARDWARE:
CO2 in an occupied room is almost entirely produced by human breath.
So the CO2 ABOVE outdoor baseline (~420 ppm) is a direct proxy for
"what fraction of the air in this room has been breathed by someone
else" -- which is exactly the quantity the Wells-Riley model needs.
This is why your whiteboard's own finding ("CO2 alone can't judge
air quality, but CO2 IS useful for something else") makes sense:
CO2 is a poor DIRECT air-quality signal, but an excellent INDIRECT
infection-risk signal.

Reference formulas (standard, published, not invented here):
- Rebreathed fraction:      f = (CO2_room - CO2_outdoor) / (CO2_exhaled - CO2_outdoor)
- Infection probability:    P = 1 - exp( -f * q * p * t / breathing_rate_hint )
  (simplified proxy version used here for a classroom-scale, relative index)
"""

import numpy as np

CO2_OUTDOOR_PPM = 420.0      # typical fresh outdoor air CO2 level
CO2_EXHALED_PPM = 38000.0    # approx CO2 concentration in exhaled human breath


def rebreathed_air_fraction(co2_ppm: float) -> float:
    """
    Fraction of air in the room that has already been breathed by someone.
    0.0 = all fresh air. 1.0 = entirely rebreathed air (never happens in practice).
    """
    f = (co2_ppm - CO2_OUTDOOR_PPM) / (CO2_EXHALED_PPM - CO2_OUTDOOR_PPM)
    return float(np.clip(f, 0.0, 1.0))


def infection_risk_score(co2_ppm: float, occupancy: int, exposure_minutes: float = 60,
                          quanta_rate: float = 25.0) -> float:
    """
    Returns a relative infection-risk score between 0 and 1 for a classroom,
    based on Wells-Riley-style reasoning.

    co2_ppm          : current measured CO2 level in the room
    occupancy        : number of people currently in the room
    exposure_minutes : how long a susceptible person stays in the room (default 60 min)
    quanta_rate       : infectious "quanta" generated per hour by one infected
                        person (25 is a commonly used mid-range literature value
                        for respiratory illness -- adjustable per disease)
    """
    if occupancy <= 1:
        return 0.0  # no one else to catch anything from

    f = rebreathed_air_fraction(co2_ppm)
    exposure_hours = exposure_minutes / 60.0

    # Crowding multiplier: more occupants sharing the same rebreathed air
    # increases the chance one of them is infectious AND increases exposure
    # -- a simplified stand-in for the "probability an infector is present"
    # term in the full Wells-Riley equation.
    crowding_factor = occupancy / 30.0

    # Simplified relative risk index (not a literal clinical probability --
    # a defensible, published-methodology-based RELATIVE risk score
    # suitable for comparing rooms/times against each other)
    risk = 1 - np.exp(-f * quanta_rate * exposure_hours * crowding_factor / 4.0)
    return float(np.clip(risk, 0.0, 1.0))


def risk_category(risk_score: float) -> str:
    """Converts a numeric risk score into a human-readable category."""
    if risk_score < 0.20:
        return "Low"
    elif risk_score < 0.45:
        return "Medium"
    else:
        return "High"


if __name__ == "__main__":
    # Quick sanity check
    for co2, occ in [(500, 30), (1500, 40), (2500, 45), (3000, 50)]:
        r = infection_risk_score(co2, occ)
        print(f"CO2={co2}ppm, occupancy={occ} -> risk={r:.3f} ({risk_category(r)})")
