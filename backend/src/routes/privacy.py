"""Blueprint providing privacy and LGPD related endpoints.

This module exposes a small API under the ``/api/privacy`` prefix for
collecting user/candidate consent, exporting personal data and performing
logical deletion/anonimization in compliance with privacy regulations
(such as Brazil's LGPD and the GDPR).  The endpoints are deliberately
minimal to avoid coupling with application‑specific models: they
identify the subject by type (``user`` or ``candidate``) and ID and
perform generic operations on those models.

If the relevant fields (e.g. ``consent_given`` or ``anonymize``) are
absent on a model, the handlers degrade gracefully: consent flags are
ignored if unavailable and anonymization falls back to marking the
record inactive by setting ``is_active`` to ``False``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from src.models import db
from src.models.user import User
from src.models.candidate import Candidate

privacy_bp = Blueprint("privacy", __name__, url_prefix="/api/privacy")


def _get_subject(subject_type: str, subject_id: int):
    """Helper to fetch a user or candidate by type and ID.

    Args:
        subject_type: either ``"user"`` or ``"candidate"``
        subject_id: primary key of the record

    Returns:
        The corresponding SQLAlchemy model instance or ``None`` if
        not found.
    """
    if subject_type == "user":
        return User.query.get(subject_id)
    if subject_type == "candidate":
        return Candidate.query.get(subject_id)
    return None


@privacy_bp.post("/consent")
def set_consent():
    """Record or revoke the consent of a subject.

    Expected JSON payload:
    ``{ "subject_type": "user"|"candidate", "subject_id": 42, "consent": true }``.

    If the underlying model has ``consent_given`` and ``consent_date`` fields,
    they are updated accordingly; otherwise the request is acknowledged
    without side effects.
    """
    data = request.get_json(silent=True) or {}
    subject_type = data.get("subject_type")
    subject_id = data.get("subject_id")
    consent = data.get("consent")
    if subject_type not in {"user", "candidate"} or subject_id is None:
        return {"error": "Invalid subject"}, 400
    model = _get_subject(subject_type, subject_id)
    if not model:
        return {"error": "Subject not found"}, 404
    # Update consent fields if present
    if hasattr(model, "consent_given"):
        setattr(model, "consent_given", bool(consent))
        if bool(consent):
            setattr(model, "consent_date", datetime.now(timezone.utc).replace(tzinfo=None))
        else:
            setattr(model, "consent_date", None)
        db.session.commit()
    # Always respond success to avoid leaking presence of consent fields
    return {"status": "ok"}, 200


@privacy_bp.get("/export/<string:subject_type>/<int:subject_id>")
def export_subject(subject_type: str, subject_id: int):
    """Export all available data for a given subject.

    The response contains the result of the model's ``to_dict`` method
    with ``include_sensitive=True`` to include any sensitive fields that
    might otherwise be omitted.
    """
    if subject_type not in {"user", "candidate"}:
        return {"error": "Invalid subject type"}, 400
    model = _get_subject(subject_type, subject_id)
    if not model:
        return {"error": "Subject not found"}, 404
    try:
        data = model.to_dict(include_sensitive=True)  # type: ignore[attr-defined]
    except Exception:
        # Fallback: return the instance's __dict__ excluding private attrs
        data = {k: v for k, v in model.__dict__.items() if not k.startswith('_')}
    return jsonify(data)


@privacy_bp.post("/delete/<string:subject_type>/<int:subject_id>")
def anonymize_subject(subject_type: str, subject_id: int):
    """Perform logical deletion or anonymization of a subject.

    If the model implements an ``anonymize`` method it will be invoked.
    Otherwise the record's ``is_active`` flag is set to ``False`` (if
    available).  A commit is always executed to persist changes.
    """
    if subject_type not in {"user", "candidate"}:
        return {"error": "Invalid subject type"}, 400
    model = _get_subject(subject_type, subject_id)
    if not model:
        return {"error": "Subject not found"}, 404
    if hasattr(model, "anonymize") and callable(getattr(model, "anonymize")):
        model.anonymize()  # type: ignore[attr-defined]
    elif hasattr(model, "is_active"):
        setattr(model, "is_active", False)
    db.session.commit()
    return {"status": "anonymized"}, 200
