"""Small LGPD helper used by services that manage candidate data."""

from datetime import datetime, timezone


class LGPDCompliance:
    """Centralizes lightweight anonymization and export helpers."""

    def anonymize_candidate_payload(self, payload):
        anonymized = dict(payload or {})
        for key in ("name", "email", "phone", "cpf", "linkedin_url"):
            if key in anonymized:
                anonymized[key] = None
        anonymized["anonymized_at"] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        return anonymized

    def build_data_export(self, candidate):
        if hasattr(candidate, "to_dict"):
            data = candidate.to_dict()
        elif isinstance(candidate, dict):
            data = dict(candidate)
        else:
            data = {
                key: value
                for key, value in vars(candidate).items()
                if not key.startswith("_")
            }

        return {
            "exported_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
            "legal_basis": "LGPD data portability request",
            "data": data,
        }
