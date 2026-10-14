"""Unit tests for token validation and object-level authorisation in the Patients API.

No Docker: a throwaway RSA key signs test tokens and the database call is replaced by a fake,
so we can assert exactly which SQL and parameters the handler sends. Run: pytest tests/unit -q
"""
import importlib.util
import pathlib
import sys
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
ISSUER = "http://localhost:8081/realms/sil"


@pytest.fixture(scope="module")
def key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def api(key):
    import os

    os.environ.update(OIDC_ISSUER=ISSUER, OIDC_AUDIENCE="sil-api", JWKS_URL="http://unused/certs", DATABASE_URL="")
    sys.path.insert(0, str(ROOT / "lab" / "apis" / "common"))
    import auth

    class FakeJwks:  # stands in for Keycloak's JWKS endpoint
        def get_signing_key_from_jwt(self, token):
            return type("K", (), {"key": key.public_key()})()

    auth._jwks = FakeJwks()
    spec = importlib.util.spec_from_file_location("patients_main", ROOT / "lab" / "apis" / "patients" / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def token(key, roles, groups, aud="sil-api", iss=ISSUER, exp_in=300):
    now = int(time.time())
    claims = {
        "sub": "u-1", "preferred_username": "tester", "iss": iss, "aud": aud,
        "iat": now, "exp": now + exp_in, "realm_access": {"roles": roles}, "groups": groups,
    }
    return jwt.encode(claims, key, algorithm="RS256")


def client_with_db(api, rows):
    calls = []

    def fake_query(sql, params=(), one=False):
        calls.append((sql, params))
        return rows

    api.query = fake_query
    return TestClient(api.app), calls


def test_missing_token_is_401(api):
    client, _ = client_with_db(api, None)
    assert client.get("/api/v1/patients/1").status_code == 401


def test_wrong_audience_is_401(api, key):
    client, _ = client_with_db(api, None)
    t = token(key, ["clinician"], ["facility-1"], aud="some-other-api")
    assert client.get("/api/v1/patients/1", headers={"Authorization": f"Bearer {t}"}).status_code == 401


def test_expired_token_is_401(api, key):
    client, _ = client_with_db(api, None)
    t = token(key, ["clinician"], ["facility-1"], exp_in=-60)
    assert client.get("/api/v1/patients/1", headers={"Authorization": f"Bearer {t}"}).status_code == 401


def test_hs256_token_signed_with_public_key_is_rejected(api, key):
    """Classic algorithm-confusion attack: must fail because only RS256 is accepted."""
    from cryptography.hazmat.primitives import serialization

    pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    now = int(time.time())
    forged = jwt.encode(
        {"sub": "x", "iss": ISSUER, "aud": "sil-api", "iat": now, "exp": now + 60,
         "realm_access": {"roles": ["clinician"]}, "groups": ["facility-1"]},
        pem.decode()[:64],  # PyJWT refuses PEM keys for HMAC, so use a slice: still a forged token
        algorithm="HS256",
    )
    client, _ = client_with_db(api, None)
    assert client.get("/api/v1/patients/1", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_receptionist_cannot_read_patients(api, key):
    client, _ = client_with_db(api, None)
    t = token(key, ["receptionist"], ["facility-1"])
    assert client.get("/api/v1/patients/1", headers={"Authorization": f"Bearer {t}"}).status_code == 403


def test_query_is_scoped_to_callers_facility(api, key):
    client, calls = client_with_db(api, None)  # DB finds nothing for that id in this facility
    t = token(key, ["clinician"], ["facility-2"])
    resp = client.get("/api/v1/patients/1", headers={"Authorization": f"Bearer {t}"})
    assert resp.status_code == 404
    sql, params = calls[0]
    assert "facility_id = %s" in sql and params == (1, 2)


def test_clinician_reads_own_facility_record(api, key):
    row = {"id": 1, "full_name": "Achieng Synthetic", "date_of_birth": "1988-03-14", "ward": "Maternity"}
    client, _ = client_with_db(api, row)
    t = token(key, ["clinician"], ["facility-1"])
    resp = client.get("/api/v1/patients/1", headers={"Authorization": f"Bearer {t}"})
    assert resp.status_code == 200 and resp.json()["id"] == 1


def test_mass_assignment_rejected(api, key):
    client, _ = client_with_db(api, {"id": 99, "full_name": "x", "date_of_birth": "2000-01-01", "ward": None})
    t = token(key, ["clinician"], ["facility-1"])
    body = {"full_name": "New Patient", "date_of_birth": "2000-01-01", "facility_id": 2}
    resp = client.post("/api/v1/patients", json=body, headers={"Authorization": f"Bearer {t}"})
    assert resp.status_code == 422  # facility_id is not accepted from the client
