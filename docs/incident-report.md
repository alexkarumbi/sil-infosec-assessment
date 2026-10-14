# Incident Report: INC-2026-014 (SIMULATED)

| Field | Entry |
| --- | --- |
| Severity | High (sensitive personal data: health) |
| Title | Patient data pasted into a public generative AI service |
| Detected | *date, time; how (self-report + SIEM rule 100101)* |
| Summary | *2-3 sentences* |
| Data and people affected | *number of records, fields, one facility; sensitive personal data under the Kenya Data Protection Act 2019* |
| Timeline | *detection, triage, containment, notifications (times)* |
| Containment | *chat deleted + provider deletion request, egress block, staging data removed, credentials rotated if any* |
| Root cause | *real data in staging, no sanctioned AI tool, egress in monitor-only mode* |
| Notifications | *DPO; client (controller) within 48 hours as processor; ODPC within 72 hours of awareness; patients if high risk* |
| Corrective actions | *action, owner, due date* |
| Lessons learned | *2-3 bullets* |
