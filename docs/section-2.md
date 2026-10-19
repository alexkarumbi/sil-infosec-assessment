# Section 2: Soft Skills and Policy Enforcement

## (a) The business refuses a recommended control because of cost

I treat a "no" on cost as information, not a defeat. Security exists to protect the business, and the business owns the risk decision. My job is to make sure it is an **informed** decision, recorded and revisited.

1. **Restate the risk in business terms, not tool names.** For example: "Without a WAF, one SQL injection in a patient endpoint could expose a whole facility's records. Under the Data Protection Act that means ODPC notification within 72 hours, possible penalties, and a client relationship at risk." I attach likelihood and impact from the risk register, and a comparable real incident where one exists.
2. **Offer options, not one price.** Usually there is a cheaper path to most of the risk reduction:
   - an open-source tool (this assessment's whole stack is open source: ModSecurity, Kong, Keycloak, Wazuh, ZAP and Semgrep);
   - a phased rollout starting with the highest-risk system;
   - compensating controls (stricter access, more monitoring) for the period without the control.
3. **Show the cost of not acting**, in the same units as the cost of acting: downtime hours, notification and legal effort, contract penalties, and lost tenders that require ISO 27001.
4. **If the answer is still no, record a formal risk acceptance:**
   - signed by the risk owner, not by me;
   - with the risk, the compensating controls, and a review date.

   I then monitor that risk more closely and bring it back with data if it changes (an incident, a new client requirement, an audit finding).
5. **Stay a partner.** I don't go around the decision-maker or let it sour the relationship. A good working relationship is what gets the next control approved.

## (b) Prioritising several simultaneous alerts

I triage on **impact × likelihood × time-sensitivity**, not arrival order.

| Order | Question | Example from my SIEM rules |
| --- | --- | --- |
| 1 | Is it **active and destructive right now**? | 100202 shadow-copy deletion + 100200 mass file changes on a file server: ransomware in progress. Contain first (isolate the host), investigate second |
| 2 | Does it involve **patient data or credentials leaving**? | 100111 PHI blocked at the AI gateway, or a confirmed secret leak: time matters for rotation and the 72-hour clock |
| 3 | Is a **critical asset** or **privileged account** involved? | WAF attacks (100121) against the patient API, or admin logins at odd hours |
| 4 | Is it **corroborated**? | A single 100101 Shadow AI attempt is low on its own; together with an endpoint alert from the same user it rises |
| 5 | Everything else | Queue, batch, tune |

**How I work it in practice:**
- **Spend a minute or two per alert on initial triage** to classify it (true positive, benign positive, false positive) before going deep on any one.
- **Group related alerts** by host, user and time: three alerts about one incident are one ticket.
- **Escalate early.** If two high-severity incidents are live, I call for help rather than serialising them.
- **Communicate:** short status updates so stakeholders know what is being handled and what waits.
- **Afterwards, tune.** Repeated false positives get a rule fix, so tomorrow's queue is smaller. At Metropolitan Hospital, running Wazuh across 50+ endpoints, tuning noisy rules was what made real alerts visible.

## (c) One-page incident report

See **[Incident Report INC-2026-014](incident-report.md)**: a developer accidentally pasted patient data into a public ChatGPT prompt.

## (d) Translating SIEM, DAST and SAST findings for business stakeholders

1. **Lead with the business impact, one sentence.** For example: "An attacker could have read any facility's patient records by changing a number in the web address." That beats "IDOR, CWE-639, CVSS 7.5."
2. **Answer the four questions leaders actually have:**
   - How bad is it?
   - Are we affected now?
   - What does it cost to fix?
   - When will it be fixed?
3. **Use their measures:** patients and facilities affected, hours of downtime, regulatory exposure (DPA, client contracts), money, reputation.
4. **Use trends, not raw counts.** "Critical findings open longer than 7 days: 12 → 3 this quarter" is meaningful; "4,312 SAST findings" is not.
5. **Use a consistent format:** a one-page monthly summary with a traffic-light status per system, the top three risks with owners and dates, and what we need from them (a decision, a budget, a priority call).
6. **Keep the technical detail available but separate**, for the engineers who will fix it.

**Example from this assessment.** For pip-audit's finding, I would not say "10 CVEs in cryptography 44.0.3". I would say: "A component inside our AI safety tool had known security holes. We replaced it the same day, at no cost, and our pipeline now catches this automatically."

## (e) Collaboration between DevOps and Security when rolling out SAST and DAST

The rollout fails if security is seen as the team that breaks the build. My approach:

1. **Co-design.** Before any tool goes in, I sit with the DevOps and development leads and agree on three things:
   - which findings block;
   - how long the pipeline may take (the pull request pipeline here runs in about 7 minutes);
   - who owns exceptions.
2. **Start in report-only mode** on one or two pilot repositories. Fix the false positives together before anything blocks.
   - **Example:** my first SQL Semgrep rule flagged harmless string formatting in the guardrail code. I narrowed it to database calls and added a test case, so it would not cry wolf again.
3. **Block only on high-confidence findings** (secrets, critical vulnerabilities with a fix, our custom rules, confirmed SQL injection). Everything else becomes a ticket with a deadline.
4. **Make findings easy to act on.** Results appear in the pull request with the line, the reason and the fix, not in a separate portal. Each custom rule message explains *why* (for example, "AI-generated handlers often omit this").
5. **Security does some of the work:**
   - I write the first rules, the reusable workflow and the fix examples;
   - I pair with developers on the first fixes;
   - I appoint a security champion in each team.
6. **Agree a fast exception path:** a reviewed, time-limited exception (like `.zap/rules.tsv`) so a release is never stuck on a false positive.
7. **Share the wins.** For example: "The pipeline caught a vulnerable library and an AI-written endpoint with no authentication before review." Credit the team.

## (f) Duty to Report (Safe Harbor): self-report versus cover-up

The policy exists to make **speed** possible. A leaked database string is a race against whoever finds it first, so the response to the person must reward telling us fast.

| | Developer **self-reports immediately** | Developer **tries to cover it up** |
| --- | --- | --- |
| Technical response | **Identical and immediate:** rotate the database credential within the hour, review database logs for use of the old credential since the paste, request deletion from the AI provider, check for other exposures | **Identical:** the credential is rotated the moment we know, however we learn of it (SIEM, proxy logs, a colleague, the provider) |
| Communication with the person | Thank them, and say so. Private, calm conversation focused on facts: what, when, which tool, what else was pasted. Confirm in writing that Safe Harbor applies | Factual and neutral; no accusations in the first conversation. Give them the chance to explain. Involve HR and their manager because it is now a conduct matter |
| Consequence | **No disciplinary action** for the mistake itself. Supportive coaching; they may help write the lessons learned if they wish | Safe Harbor **does not cover concealment**. Handled under the disciplinary process with HR, proportionate to intent and harm. Concealment is the offence; the original mistake still is not |
| Team-level message | Anonymised story shared: "someone reported this fast, and that let us fix it in an hour" | Anonymised lessons only; no public shaming, which would discourage future reports |
| Evidence | Normal incident record | Preserve evidence carefully (logs, chain of custody), because it may support HR or legal action |

**Why the difference matters.** Every self-report treated fairly builds trust, and the next person reports faster. If a self-reporter were punished, nobody would report again, and we would only find leaks after an attacker did. Concealment must have clear consequences, or the policy has no meaning. I would also check *why* concealment happened: fear of punishment usually means the policy has not been communicated well enough.

**Fix the system either way:**
- no long-lived database strings on laptops;
- secret scanning (Section 1B(2));
- the guardrail gateway, which blocks secrets in prompts.

## (g) Balancing user privacy and security monitoring

I aim for monitoring that is **necessary, proportionate, transparent and limited**, the same principles as the Data Protection Act.

1. **Monitor for a defined purpose.** Security monitoring targets threats (malware, data exfiltration, account takeover, Shadow AI). It does not target productivity or personal life. The purposes are written in an acceptable-use policy that staff have read.
2. **Minimise what is collected.** My AI gateway logs a **hash and the length of each prompt, never the text**. The WAF logs no bodies and no request headers. The Shadow AI rule logs the site and the source, not what was typed. The SIEM should never become a second copy of patient data or private conversations.
3. **Metadata first, content only with justification.** Investigations start from metadata (who, when, which system). Opening content needs a documented reason, and for sensitive cases approval from the DPO or HR.
4. **Restrict and audit access to the monitoring data itself.** Role-based access, every analyst search logged, retention limits (for example 12 months), and deletion afterwards.
5. **Do a data protection impact assessment** before new monitoring (for example endpoint web filtering or a keystroke-level tool), and consult staff representatives where appropriate.
6. **Respond educationally first.** A first Shadow AI alert leads to a conversation and a pointer to the sanctioned tool, not a disciplinary file.
7. **Be transparent.** Staff know what is monitored and why. Hidden monitoring destroys the trust that the Duty to Report policy depends on.

Security and privacy are not opposites here. Collecting less, and protecting what we collect, also reduces our own breach risk.
