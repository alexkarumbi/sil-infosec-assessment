"""SIL Appointments API (sample API 2). Clinicians and receptionists, scoped to their facility."""
import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from audit import audit
from auth import require_facility, require_role
from db import query

SERVICE = "appointments-api"
app = FastAPI(
    title="SIL Appointments API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/v1/appointments/openapi.json",
)


class AppointmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patient_id: int = Field(gt=0)
    scheduled_for: datetime.datetime
    clinic: str = Field(min_length=2, max_length=60)
    reason: str | None = Field(default=None, max_length=200)


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    scheduled_for: datetime.datetime
    clinic: str
    reason: str | None


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@app.get("/api/v1/appointments", response_model=list[AppointmentOut])
def list_appointments(user: dict = Depends(require_role("clinician", "receptionist"))):
    facility = require_facility(user)
    rows = query(
        "SELECT id, patient_id, scheduled_for, clinic, reason FROM appointments "
        "WHERE facility_id = %s ORDER BY scheduled_for LIMIT 100",
        (facility,),
    )
    audit(SERVICE, user, "appointment.list")
    return rows


@app.post("/api/v1/appointments", response_model=AppointmentOut, status_code=201)
def create_appointment(body: AppointmentIn, user: dict = Depends(require_role("clinician", "receptionist"))):
    facility = require_facility(user)
    if body.scheduled_for.tzinfo is None:
        raise HTTPException(status_code=422, detail="scheduled_for must include a timezone")
    if body.scheduled_for < datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(status_code=422, detail="cannot book in the past")
    # Business-logic check AI-generated code often forgets: the patient must belong to the caller's facility.
    patient = query(
        "SELECT id FROM patients WHERE id = %s AND facility_id = %s", (body.patient_id, facility), one=True
    )
    if patient is None:
        audit(SERVICE, user, "appointment.create", body.patient_id, outcome="patient_not_found_or_denied")
        raise HTTPException(status_code=404, detail="patient not found")
    row = query(
        "INSERT INTO appointments (facility_id, patient_id, scheduled_for, clinic, reason, created_by) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, patient_id, scheduled_for, clinic, reason",
        (facility, body.patient_id, body.scheduled_for, body.clinic, body.reason, user["username"]),
        one=True,
    )
    audit(SERVICE, user, "appointment.create", row["id"])
    return row
