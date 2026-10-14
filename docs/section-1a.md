# Section 1A: API Gateway and AI Guardrails

> Write each answer in your own words. Bullet prompts in *italics* are reminders; delete them as you write.
> Evidence lives in `../evidence/`; reference screenshots by file name.

## (a) Architecture
![Architecture](architecture.png)
*One or two lines per component; trust boundaries; production mapping (AWS WAF / Front Door, API Gateway / APIM, Cognito / Entra ID, managed firewall, private-endpoint LLM).*

## (b) Implementation plan
*Step-by-step: prerequisites, build order (scripts/lab_up.sh), configuration choices and why, cloud preference (Cape Town or South Africa North, Terraform), what changes for production.*

## (c) Two APIs behind the gateway and WAF
*Table of curl/pytest results: 401 no token, 200, 404 other facility, 403 receptionist, 403 SQLi/XSS/traversal (WAF rule IDs from audit.json), 429 rate limit.*

## (d) Rate limiting, authentication, secure data handling
*Tie each point to a line of kong.yml.template, realm-sil.json or auth.py.*

## (e) AI input/output guardrails
*Pipeline order and why; Kenyan identifiers; block vs mask; hashed logging; results table from tests/integration/test_ai_guardrails.py; known limits (probabilistic detection, small-model name misses, indirect injection).*

## (f) Risks and mitigations
| Risk | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |
