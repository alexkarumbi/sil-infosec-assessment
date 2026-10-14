"""One test per row of authz_matrix.yaml: catches missing or wrong authorisation checks."""
import pathlib

import pytest
import yaml

from conftest import auth

MATRIX = yaml.safe_load((pathlib.Path(__file__).parent / "authz_matrix.yaml").read_text())


@pytest.mark.parametrize("case", MATRIX, ids=lambda c: f"{c['user']} {c['method']} {c['path']} -> {c['expect']}")
def test_authz(client, tokens, case):
    resp = client.request(case["method"], case["path"], headers=auth(tokens[case["user"]]), json=case.get("body"))
    assert resp.status_code == case["expect"], resp.text[:200]
