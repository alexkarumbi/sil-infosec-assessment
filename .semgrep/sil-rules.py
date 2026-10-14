# Test cases for sil-rules.yml. Run: semgrep --test .semgrep/
# This file is never imported; it holds deliberately vulnerable "AI-generated" examples.
from fastapi import Depends, FastAPI

from auth import require_role
from db import query

app = FastAPI()


# ruleid: fastapi-route-without-auth
@app.get("/api/v1/patients/search/{patient_id}")
def search_patient(patient_id: int):
    # ruleid: select-by-id-without-facility-scope
    return query("SELECT * FROM patients WHERE id = %s", (patient_id,), one=True)


# ok: fastapi-route-without-auth
@app.get("/api/v1/patients/{patient_id}")
def get_patient(patient_id: int, user: dict = Depends(require_role("clinician"))):
    # ok: select-by-id-without-facility-scope
    return query("SELECT * FROM patients WHERE id = %s AND facility_id = %s", (patient_id, user["facility_id"]), one=True)


# ruleid: fastapi-route-without-auth
@app.post("/api/v1/appointments")
async def create_appointment(body: dict):
    return body


# ok: fastapi-route-without-auth
@app.get("/health")
def health():
    return {"status": "ok"}


def unsafe(name):
    # ruleid: sql-built-with-fstring
    return query(f"SELECT * FROM patients WHERE full_name = '{name}'")


def not_sql(entity):
    out = []
    # ok: sql-built-with-fstring
    out.append(f"<{entity}>")
    return out
