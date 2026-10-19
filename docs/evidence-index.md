# Appendix: Evidence index

| # | Screenshot | Shows | Section |
| --- | --- | --- | --- |
| 01 | `01-docker-ps.png` | Lab and Wazuh containers running; SIEM ports bound to 127.0.0.1 | 1A(c) |
| 02 | `02-curl-gateway-tests.png` | 401 / 200 / 404 / 403 role / 403 WAF (SQL injection, cross-site scripting, traversal) | 1A(c) |
| 03 | `03-rate-limit-429.png` | 70-request burst: 200s then 429s | 1A(d) |
| 04 | `04-waf-audit-entry.png` | WAF audit entry: rule 942100 + 949110, body not logged | 1A(c, d) |
| 05 | `05-ai-allowed-answer.png` | Normal question answered by the local model | 1A(e) |
| 06 | `06-ai-injection-model.png` | Injection with no trigger words caught by the DeBERTa model | 1A(e) |
| 07 | `07-ai-phi-blocked.png` | Medical record number blocked before leaving the network | 1A(e) |
| 08 | `08-ai-phone-masked.png` | Kenyan phone number masked before the model sees it | 1A(e) |
| 09 | `09-guardrail-log.png` | Decision log: hashes and counts, never the prompt | 1A(d, e) |
| 10 | `10-integration-tests.png` | 26 integration tests + rate-limit test pass | 1A(c) |
| 11 | `11-wazuh-logtest-squid.png` | New log source decoded; rule 100101 fires | 1B(3) |
| 12 | `12-wazuh-agent-active.png` | Windows agent 001 active (v4.14.9) | 1B(3) |
| 13 | `13-sil-alerts-overview.png` | SIL alerts in the dashboard (119 hits) | 1B(3) |
| 14 | `14-alert-shadow-ai-100102.png` | Shadow AI threshold alert, ATT&CK T1567 | 1B(3) |
| 15 | `15-alert-guardrail-100112.png` | Prompt-injection block alert with user | 1B(3) |
| 16 | `16-alert-waf-100121.png` | WAF sustained-attack alert; oversized `previous_output` | 1B(3, 4) |
| 17 | `17-alert-ransomware-100200.png` | Mass file-change alert, T1486 | 1B(3) |
| 18 | `18-alert-ransomware-100201.png` | 57 `.locked` file alerts | 1B(3) |
| 19 | `19-alert-shadowcopy-100202.png` | Shadow-copy deletion command with parent process, T1490 | 1B(3) |
| 20 | `20-rule-count-summary.png` | Count of every SIL rule fired | 1B(3) |
| 21 | `21-ci-red-first-run.png` | First pipeline run: SAST and SCA fail | 1B(1, 2) |
| 22 | `22-ci-pip-audit-cryptography.png` | 10 vulnerabilities in `cryptography` 44.0.3 | 1B(2) |
| 23 | `23-ci-all-green.png` | All five jobs green | 1B(1) |
| 24 | `24-precommit-blocked.png` | Commit with a database connection string blocked | 1B(2) |
| 25 | `25-hallucinated-package.png` | Non-existent package fails the build | 1B(2) |
| 26 | `26-local-block.png` | AI-generated SQL injection blocked by pre-commit Bandit | 1B(6) |
| 27 | `27-pull-request-fail-SAST.png` | Pull request #1: SAST failing | 1B(6) |
| 28 | `28-rule-findings.png` | Three SIL custom-rule findings | 1B(6) |
| 29 | `29-pull-green.png` | Same pull request after the fix: all green | 1B(6) |

**Repository map**

| Path | Contents |
| --- | --- |
| `lab/` | Docker Compose lab: WAF, Kong, Keycloak, APIs, AI gateway, Squid, PostgreSQL |
| `siem/` | Wazuh setup script, custom rules, log collection config, agent snippet, sample logs |
| `.github/workflows/secure-pipeline.yml` | CI/CD security pipeline |
| `.pre-commit-config.yaml`, `.gitleaks.toml`, `.semgrep/`, `.zap/` | Scanner configuration and custom rules |
| `scripts/` | Build helpers, package-existence check, ransomware and Shadow AI simulations |
| `tests/` | Unit, integration and authorisation-matrix tests |
| `docs/` | This report's sources and the draw.io diagrams |
