# Incident Report INC-2026-014 (SIMULATED EXERCISE)

**Patient data pasted into a public AI chatbot** · Severity: **High** (sensitive personal data: health) · Status: Closed · Author: Alex Karumbi Muhia, Information Security Analyst · Classification: Confidential

| | |
| --- | --- |
| **Summary** | A developer debugging the discharge-summary feature pasted 14 rows from a **staging database export** into the free, public version of ChatGPT from a personal laptop at home, outside the corporate proxy. The rows held real patient data copied into staging months earlier. The developer **self-reported within 35 minutes** under the Duty to Report policy. The chat was deleted, no other exposure was found, and the client and the Office of the Data Protection Commissioner (ODPC) were notified within the legal deadlines. |
| **Data and people affected** | 14 patients at one client facility. Fields: full name, medical record number, date of birth, ward, diagnosis and discharge notes. Health data is **sensitive personal data** under the Kenya Data Protection Act 2019 (DPA). SIL acts as **data processor**; the facility is the **data controller**. No credentials were included. |
| **Detection** | 1) Self-report by the developer to the security channel (10:47). 2) The SIEM showed no proxy event, because the laptop was off-network. That gap was itself a finding. 3) Confirmed from the developer's screen recording and the ChatGPT conversation history. |

**Timeline (East Africa Time, simulated day 0)**

| Time | Event |
| --- | --- |
| 10:12 | Developer pastes the rows into ChatGPT asking why the summary template breaks |
| 10:47 | Developer realises and reports it in `#security-incidents` |
| 10:55 | Analyst acknowledges, opens INC-2026-014, informs the Data Protection Officer (DPO) and the Head of Engineering |
| 11:10 | Conversation deleted while the analyst watched; chat history export saved as evidence; "Improve the model" setting confirmed off from now on; OpenAI privacy deletion request filed |
| 11:30 | Staging database checked: **real data confirmed in staging**; staging access frozen |
| 12:15 | Scope confirmed: 14 records, one facility; no other pastes (developer interview + browser history with consent) |
| 15:00 | Real data purged from staging and replaced with synthetic data; staging credentials rotated as a precaution |
| Day 1, 09:30 | **Client (controller) notified in writing, about 23 hours after awareness** (DPA s.43: processor to notify controller within 48 hours) |
| Day 2, 14:00 | Controller, with SIL's support, notifies the **ODPC within 72 hours** of awareness; patient notification decided by the controller on the risk assessment |
| Day 7 | Post-incident review held (blameless) |

**Containment and recovery.**
- Conversation deleted and a provider deletion request filed.
- Staging frozen, then purged of real data.
- Credentials rotated.
- The developer's laptop checked for local copies of the export, which were deleted.

**Root cause (five whys).**
1. **Real patient data existed in staging.** It had been copied to reproduce a bug, against policy, and never removed.
2. **No sanctioned AI tool was available** for debugging, so the developer reached for a public one.
3. **Egress controls applied only on the office network.** The personal laptop at home bypassed the proxy and the SIEM rule 100101.
4. **Training covered phishing, but not AI data handling.**

**Corrective actions.**

| # | Action | Owner | Due |
| --- | --- | --- | --- |
| 1 | Synthetic-only data in all non-production environments; automated scan for real identifiers in staging | Head of Engineering | 30 days |
| 2 | Roll out the sanctioned AI assistant through the AI guardrail gateway (blocks identifiers, masks personal data) | Security | 45 days |
| 3 | Endpoint-based web filtering on all work devices, so Shadow AI controls apply off-network; no personal devices for production or staging access | IT | 60 days |
| 4 | 20-minute "AI and patient data" module for all engineers; add this case (anonymised) to onboarding | Security + HR | 30 days |
| 5 | Exercise this runbook, including the controller and ODPC notification path, every six months | Security + DPO | 6 months |

**Lessons learned.**
- **Self-reporting worked.** Thirty-five minutes from mistake to containment was only possible because the developer trusted the Safe Harbor policy. No disciplinary action was taken; the commitment was kept and communicated.
- **The technical control (proxy) had a blind spot that nobody had tested:** off-network devices. Controls must follow the device.
- **Providing a safe, sanctioned tool removes the reason for most Shadow AI.**
