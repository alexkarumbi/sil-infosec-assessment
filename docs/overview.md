# Overview

**Candidate:** Alex Karumbi Muhia · **Role:** Information Security Analyst, Savannah Informatics · **Submitted:** 20 October 2026
**Repository:** https://github.com/alexkarumbi/sil-infosec-assessment

I answered the practical questions by **building and testing a working lab** rather than describing one. Every claim in this report links to code in the repository or a screenshot in `evidence/screenshots/`. All patient data is synthetic.

## What was built

| Brief | What exists | Proof |
| --- | --- | --- |
| 1A(a) Architecture | Trust-zoned design: WAF → API gateway → APIs → database, identity provider, AI guardrail gateway, egress proxy, SIEM | Diagram (draw.io source included) |
| 1A(b) Implementation plan | Scripted build (`scripts/lab_up.sh`, `siem/setup_wazuh.sh`); production mapping to AWS Cape Town | Section 1A(b) |
| 1A(c) Two APIs behind the gateway and WAF | Patients and Appointments APIs (FastAPI) behind Kong and ModSecurity + OWASP Core Rule Set | 26 integration tests + rate-limit test pass; screenshots 01–04, 10 |
| 1A(d) Rate limits, authentication, data handling | 60/min global, 10/min AI; Keycloak RS256 tokens verified twice; facility scoping; no bodies, headers or prompts in logs | Screenshots 02–04, 09; unit tests |
| 1A(e) AI guardrails | Injection (regex + DeBERTa model), secrets, Kenyan identifiers blocked, personal data masked in and out; hashed logging | Screenshots 05–09 |
| 1B(1–2) SIEM / SAST / DAST plan, secret scanning, hallucinated packages | Pre-commit + 5-job GitHub Actions pipeline; custom package-existence check | Screenshots 21–26 |
| 1B(3) SIEM | Wazuh with 12 custom rules: Shadow AI, AI guardrail, WAF, ransomware; new log source onboarded (Squid) | Screenshots 11–20 |
| 1B(6) DAST and AI logic flaws | ZAP baseline + active API scans; 3 custom Semgrep rules; planted AI-generated flaws caught and fixed | Screenshots 26–29 |
| Section 2 | Written answers and a one-page incident report | Section 2 |

## Problems I found in my own build, and fixed

These are the parts I learned most from, and each is written up where it belongs:

1. **A security tool brought in vulnerable code.** The pipeline's first run found 10 known vulnerabilities in `cryptography`, pulled in by LLM Guard. I replaced the dependency. (1A(e), 1B(2))
2. **The WAF audit log would have stored patient data, then bearer tokens.** Both were found and fixed; the second was caught by my own pre-commit secret scan. (1A(d))
3. **A custom SAST rule produced false positives.** I narrowed it and added a test case. (1B(6))
4. **The ransomware rules missed real Windows behaviour** (a rename is delete + add) **and Wazuh's static fields.** Both were fixed and re-tested against a simulation. (1B(3))
5. **A SIEM alert fired but never reached the dashboard**, because it was too large for the index. I diagnosed it and wrote it up as an incomplete-logs case. (1B(4))

## How to read this report

- **Section 1A:** gateway, WAF, authentication and AI guardrails.
- **Section 1B:** pipeline and SIEM.
- **Section 2:** soft skills and the incident report.
- **Appendix:** the evidence index.
