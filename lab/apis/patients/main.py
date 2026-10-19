"""SIL Patients API (sample API 1). Clinicians only, scoped to their own facility."""
import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from audit import audit
from auth import require_facility, require_role
from db import query

SERVICE = "patients-api"
app = FastAPI(
    title="SIL Patients API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/v1/patients/openapi.json",
)


class PatientIn(BaseModel):
    # extra="forbid": a client cannot smuggle in facility_id or created_by (mass assignment)
    model_config = ConfigDict(extra="forbid")
    full_name: str = Field(min_length=2, max_length=120)
    date_of_birth: datetime.date
    ward: str | None = Field(default=None, max_length=40)


class PatientOut(BaseModel):
    id: int
    full_name: str
    date_of_birth: datetime.date
    ward: str | None


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@app.get("/api/v1/patients", response_model=list[PatientOut])
def list_patients(user: dict = Depends(require_role("clinician"))):
    facility = require_facility(user)
    rows = query(
        "SELECT id, full_name, date_of_birth, ward FROM patients WHERE facility_id = %s ORDER BY id LIMIT 100",
        (facility,),
    )
    audit(SERVICE, user, "patient.list")
    return rows


@app.get("/api/v1/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, user: dict = Depends(require_role("clinician"))):
    facility = require_facility(user)
    row = query(
        "SELECT id, full_name, date_of_birth, ward FROM patients WHERE id = %s AND facility_id = %s",
        (patient_id, facility),
        one=True,
    )
    if row is None:
        audit(SERVICE, user, "patient.read", patient_id, outcome="not_found_or_denied")
        raise HTTPException(status_code=404, detail="not found")  # 404, not 403: don't confirm it exists
    audit(SERVICE, user, "patient.read", patient_id)
    return row


@app.post("/api/v1/patients", response_model=PatientOut, status_code=201)
def create_patient(body: PatientIn, user: dict = Depends(require_role("clinician"))):
    facility = require_facility(user)
    row = query(
        "INSERT INTO patients (facility_id, full_name, date_of_birth, ward, created_by) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id, full_name, date_of_birth, ward",
        (facility, body.full_name, body.date_of_birth, body.ward, user["username"]),
        one=True,
    )
    audit(SERVICE, user, "patient.create", row["id"])
    return row


# ---- Reviewed and fixed after the pipeline flagged the AI-generated version ----

@app.get("/api/v1/patients/search/by-name", response_model=list[PatientOut])
def search_patients(
    name: str = Query(min_length=2, max_length=60),
    user: dict = Depends(require_role("clinician")),
):
    facility = require_facility(user)
    rows = query(
        "SELECT id, full_name, date_of_birth, ward FROM patients "
        "WHERE facility_id = %s AND full_name ILIKE %s ORDER BY id LIMIT 50",
        (facility, f"%{name}%"),
    )
    audit(SERVICE, user, "patient.search")
    return rows


@app.get("/api/v1/patients/{patient_id}/summary", response_model=PatientOut)
def patient_summary(patient_id: int, user: dict = Depends(require_role("clinician"))):
    facility = require_facility(user)
    row = query(
        "SELECT id, full_name, date_of_birth, ward FROM patients WHERE id = %s AND facility_id = %s",
        (patient_id, facility),
        one=True,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    audit(SERVICE, user, "patient.summary", patient_id)
    return row


# The bulk export endpoint was removed: no clinician needs every patient record through the API.
