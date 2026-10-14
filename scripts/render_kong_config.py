#!/usr/bin/env python3
"""Write lab/kong/kong.yml from the template, pasting in Keycloak's current realm public key.

Run after Keycloak is up (scripts/lab_up.sh does this for you). Re-run whenever the realm
signing key rotates, then: docker compose restart kong
"""
import json
import pathlib
import sys
import textwrap
import time
import urllib.request

KC_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8081"
if not KC_URL.startswith(("http://", "https://")):
    sys.exit("Keycloak URL must start with http:// or https://")  # blocks file:// and other schemes
LAB = pathlib.Path(__file__).resolve().parent.parent / "lab" / "kong"

for attempt in range(60):
    try:
        # Bandit B310 reviewed: scheme checked above
        with urllib.request.urlopen(f"{KC_URL}/realms/sil", timeout=5) as resp:  # nosec B310
            key = json.load(resp)["public_key"]
        break
    except Exception:  # Keycloak still starting
        time.sleep(5)
else:
    sys.exit(f"Keycloak realm 'sil' not reachable at {KC_URL} after 5 minutes")

pem = "-----BEGIN PUBLIC KEY-----\n" + "\n".join(textwrap.wrap(key, 64)) + "\n-----END PUBLIC KEY-----"
indented = textwrap.indent(pem, " " * 10)
template = (LAB / "kong.yml.template").read_text()
(LAB / "kong.yml").write_text(template.replace("__KEYCLOAK_PUBLIC_KEY__", indented))
print(f"Wrote {LAB / 'kong.yml'} with the realm public key")
