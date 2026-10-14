# Section 1B: Security Testing, Event Management and Secure AI SDLC

## 1. SIEM, DAST and SAST deployment plan
*Tool table and integration points (laptop, PR, main, nightly, runtime); rollout phases; remediation deadlines.*

## 2. Pre-commit secret scanning and SCA for hallucinated dependencies
*.pre-commit-config.yaml + .gitleaks.toml (custom db-connection-string rule); screenshot of a blocked commit.*
*Be explicit: pre-commit protects the repository, not a chat box. Controls for Copilot/ChatGPT pastes: no long-lived secrets on laptops, Copilot Business content exclusions, in-editor scanner, egress blocking, push protection, training + Duty to Report.*
*scripts/check_packages_exist.py: screenshot of the failing run on a made-up package.*

## 3. SIEM: ransomware, Shadow AI, new log source
*Onboarding walkthrough for Squid: format (JSON at source) -> collection (localfile) -> decoding (built-in JSON) -> rules 100100-100102 -> wazuh-logtest -> dashboard. Screenshots of 100101/100102, 100111/100112, 100120/100121, 100200-100202.*

## 4. Handling incomplete logs
*Preserve, map the gap, treat the gap as evidence, corroborate, host artefacts, state confidence, fix the cause.*

## 5. Compliance reporting in a multi-cloud environment
*One control framework (ISO 27001:2022 Annex A) mapped to Kenya DPA 2019, HIPAA, GDPR; native posture tools + Prowler; central evidence store; reporting by audience.*

## 6. DAST in CI/CD and AI-generated logic flaws
*Passive baseline through the WAF on every PR; active API scans direct to services on main/nightly; report walkthrough (3-4 alerts: risk, confidence, CWE, evidence, decision).*
*Custom Semgrep rules (.semgrep/sil-rules.yml), authorisation matrix tests, multi-user IDOR checks, review of AI-assisted PRs. Screenshot: red pipeline on the ai-generated-endpoint branch, then green after the fix.*
