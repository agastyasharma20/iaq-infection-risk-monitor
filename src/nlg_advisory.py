"""
nlg_advisory.py -- Plain-English Advisory Generator (V4)
--------------------------------------------------------------
Turns the system's separate outputs (risk category, root cause, RL
recommendation, Digital Twin projection) into ONE plain-English sentence
a non-technical teacher or facilities officer can act on immediately --
no jargon, no separate charts to interpret.

This is template-based natural language generation (NLG), not a call to
an external LLM API -- deliberately, so it works fully offline, with zero
API cost, and with 100% predictable output (no hallucination risk) for a
safety-relevant message. This is the right engineering choice here even
though "LLM-generated" sounds more advanced: a wrong LLM-generated safety
instruction is a real risk, a wrong template is just a bug you can see
and fix by reading the code.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


ACTION_PHRASES = {
    "no_action": "no action is needed right now",
    "open_windows": "opening the windows/increasing ventilation",
    "reduce_occupancy": "reducing the number of students in the room for a while",
}


def generate_advisory(room_id: str, risk_category: str, root_cause: str,
                       recommended_action: str, projected_category: str = None) -> str:
    """
    Builds a single, plain-English advisory sentence from the system's
    structured outputs.
    """
    action_phrase = ACTION_PHRASES.get(recommended_action, recommended_action)

    if risk_category == "Low":
        return f"{room_id}: Air quality and infection risk are currently Low. No action needed."

    cause_phrase = {
        "Overcrowding — occupancy is the dominant risk driver": "too many students in the room relative to its ventilation",
        "Poor Ventilation Baseline — CO2 elevated independent of current headcount": "poor ventilation, independent of how many students are present",
        "Combined — both occupancy and poor ventilation are contributing": "a combination of overcrowding and poor ventilation",
        "Normal — no significant risk driver": "no single dominant cause",
    }.get(root_cause, root_cause)

    sentence = (
        f"{room_id} is currently at **{risk_category}** infection risk, mainly caused by "
        f"{cause_phrase}. Recommended action: **{action_phrase}**."
    )

    if projected_category and projected_category != risk_category:
        sentence += f" If this action is taken, risk is projected to improve to **{projected_category}**."
    elif projected_category:
        sentence += f" Even with this action, risk is projected to remain **{projected_category}** -- consider a stronger intervention."

    return sentence


if __name__ == "__main__":
    print(generate_advisory(
        room_id="Room_4",
        risk_category="High",
        root_cause="Overcrowding — occupancy is the dominant risk driver",
        recommended_action="reduce_occupancy",
        projected_category="Medium",
    ))
    print()
    print(generate_advisory(
        room_id="Room_1",
        risk_category="Low",
        root_cause="Normal — no significant risk driver",
        recommended_action="no_action",
    ))
