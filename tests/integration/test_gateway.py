"""Gateway + WAF behaviour, as seen by a client. Each test maps to a curl line in the README."""
import pytest

from conftest import auth


def test_no_token_rejected_by_kong(client):
    assert client.get("/api/v1/patients/1").status_code == 401


def test_clinician_reads_own_facility_patient(client, tokens):
    resp = client.get("/api/v1/patients/1", headers=auth(tokens["dr.wanjiru"]))
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID")              # correlation-id plugin
    assert resp.headers.get("Cache-Control") == "no-store"
    assert "Server" not in resp.headers or "kong" not in resp.headers["Server"].lower()


def test_other_facility_patient_is_404(client, tokens):
    # patient 7 belongs to facility 2; dr.wanjiru is facility 1
    assert client.get("/api/v1/patients/7", headers=auth(tokens["dr.wanjiru"])).status_code == 404


def test_receptionist_cannot_read_patients(client, tokens):
    assert client.get("/api/v1/patients/1", headers=auth(tokens["reception.otieno"])).status_code == 403


def test_receptionist_can_list_appointments(client, tokens):
    assert client.get("/api/v1/appointments", headers=auth(tokens["reception.otieno"])).status_code == 200


def test_tampered_token_rejected(client, tokens):
    t = tokens["dr.wanjiru"]
    tampered = t[:-4] + ("AAAA" if not t.endswith("AAAA") else "BBBB")
    assert client.get("/api/v1/patients/1", headers=auth(tampered)).status_code == 401


@pytest.mark.parametrize(
    "query",
    [
        "?q=1' OR '1'='1",                                   # SQL injection  -> CRS 942xxx
        "?q=1 UNION SELECT username, password FROM users",   # SQL injection
        "?n=<script>alert(1)</script>",                      # XSS            -> CRS 941xxx
        "?file=../../../../etc/passwd",                      # path traversal -> CRS 930xxx
    ],
)
def test_waf_blocks_attacks(client, tokens, query):
    assert client.get(f"/api/v1/patients/1{query}", headers=auth(tokens["dr.wanjiru"])).status_code == 403


@pytest.mark.ratelimit
def test_rate_limit_returns_429(client, tokens):
    """Run last and on its own: it uses up this minute's quota. pytest -m ratelimit"""
    codes = [client.get("/api/v1/patients/1", headers=auth(tokens["dr.wanjiru"])).status_code for _ in range(70)]
    assert 429 in codes
