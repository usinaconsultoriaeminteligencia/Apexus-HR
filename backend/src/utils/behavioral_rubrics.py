"""Versioned behavioral rubric catalog for auditable candidate scoring."""

RUBRIC_VERSION = "2026.04-v1"


BEHAVIORAL_RUBRICS = {
    "version": RUBRIC_VERSION,
    "frameworks": {
        "disc": {
            "source": "DISC-inspired behavioral dimensions",
            "dimensions": {
                "dominance": {
                    "description": "Decisiveness, ownership, and comfort with conflict.",
                    "positive_signals": [
                        "takes responsibility for outcomes",
                        "makes decisions with incomplete information",
                        "handles conflict directly and respectfully",
                    ],
                    "risk_signals": [
                        "avoids accountability",
                        "escalates conflict without context",
                        "pushes decisions without listening",
                    ],
                },
                "influence": {
                    "description": "Persuasion, communication, and stakeholder energy.",
                    "positive_signals": [
                        "builds alignment with examples",
                        "adapts message to audience",
                        "creates trust in cross-functional work",
                    ],
                    "risk_signals": [
                        "overpromises without evidence",
                        "depends only on charisma",
                        "does not close communication loops",
                    ],
                },
                "steadiness": {
                    "description": "Consistency, patience, collaboration, and resilience.",
                    "positive_signals": [
                        "keeps quality under pressure",
                        "supports team continuity",
                        "responds calmly to change",
                    ],
                    "risk_signals": [
                        "struggles with ambiguity",
                        "delays hard conversations",
                        "resists necessary change",
                    ],
                },
                "conscientiousness_disc": {
                    "description": "Precision, standards, planning, and compliance discipline.",
                    "positive_signals": [
                        "uses clear acceptance criteria",
                        "documents decisions and tradeoffs",
                        "spots operational risks early",
                    ],
                    "risk_signals": [
                        "gets blocked by perfectionism",
                        "misses deadlines through over-analysis",
                        "applies process without business context",
                    ],
                },
            },
        },
        "big_five": {
            "source": "Big Five inspired workplace traits",
            "dimensions": {
                "openness": "Learning agility, curiosity, and adaptation to new ideas.",
                "conscientiousness": "Reliability, planning, follow-through, and quality orientation.",
                "extraversion": "Social energy, assertive communication, and external engagement.",
                "agreeableness": "Cooperation, empathy, trust, and constructive disagreement.",
                "emotional_stability": "Stress tolerance, impulse control, and recovery after setbacks.",
            },
        },
    },
    "competencies": {
        "customer_orientation": {
            "score_scale": "1-5",
            "evidence_required": ["situation", "action", "result", "learning"],
            "red_flags": ["generic answer", "no measurable result", "blames customer or team"],
        },
        "data_driven_decision": {
            "score_scale": "1-5",
            "evidence_required": ["metric", "decision context", "tradeoff", "business impact"],
            "red_flags": ["uses data only after decision", "no baseline", "confuses correlation with cause"],
        },
        "ethical_judgment": {
            "score_scale": "1-5",
            "evidence_required": ["stakeholders", "risk", "policy or principle", "escalation path"],
            "red_flags": ["ignores compliance", "normalizes bias", "optimizes only for speed"],
        },
    },
    "evidence_schema": {
        "answer_excerpt": "Short, candidate-authored evidence excerpt.",
        "rubric_dimension": "DISC, Big Five, or competency key.",
        "score": "Integer from 1 to 5.",
        "confidence": "Model confidence from 0 to 1.",
        "human_validation": "pending, approved, adjusted, or rejected.",
        "fairness_notes": "Observed fairness risk or mitigation.",
    },
}


def get_rubric_catalog():
    return BEHAVIORAL_RUBRICS
