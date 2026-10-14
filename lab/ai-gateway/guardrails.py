"""AI input/output guardrails for the SIL lab.

Order of checks on the way IN (cheapest first):
  1. prompt-injection heuristics (regex, English + Swahili phrases)
  2. prompt-injection classifier (LLM Guard, optional: LLM_GUARD_ENABLED)
  3. secrets (regex for connection strings and keys, + LLM Guard Secrets scanner when enabled)
  4. hard identifiers (MRN, National ID, KRA PIN, card numbers) -> BLOCK, PHI never leaves
  5. softer personal data (names, phones, emails, places) -> MASK before the prompt leaves
On the way OUT: mask personal data in the model's answer.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

LLM_GUARD_ENABLED = os.environ.get("LLM_GUARD_ENABLED", "true").lower() == "true"
# en_core_web_lg finds names far better (the small model tagged "Summarise" as a PERSON in testing).
# The full image uses lg; the light CI image uses sm to save ~500 MB.
SPACY_MODEL = os.environ.get("SPACY_MODEL", "en_core_web_lg")
SCORE_THRESHOLD = 0.5   # an 8-digit number alone (0.3) is not enough; with "ID"/"national" nearby it is

INJECTION_HEURISTICS = re.compile(
    r"ignore\s+(all\s+|any\s+)?(previous|prior|above|earlier)?\s*(instructions|rules|prompts?)"
    r"|(reveal|print|show|repeat)\s+(your|the)\s+(system\s+prompt|instructions)"
    r"|system\s+prompt"
    r"|you\s+are\s+now\s+(dan|in\s+developer\s+mode)"
    r"|developer\s+mode|jailbreak|do\s+anything\s+now"
    r"|puuza\s+maagizo",                 # Swahili: "ignore the instructions"
    re.IGNORECASE,
)

SECRET_PATTERNS = re.compile(
    r"(?i)(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|mssql)://[^:\s/]+:[^@\s]+@\S+"   # DB connection strings
    r"|AKIA[0-9A-Z]{16}"                                                            # AWS access key ID
    r"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r"|gh[pousr]_[A-Za-z0-9]{36}"                                                   # GitHub tokens
    r"|(?:password|passwd|pwd|secret|api[_-]?key)\s*[:=]\s*\S{6,}"
)

BLOCK_ENTITIES = {"MEDICAL_RECORD_NUMBER", "KE_NATIONAL_ID", "KRA_PIN", "CREDIT_CARD", "US_SSN", "IBAN_CODE"}
MASK_ENTITIES = {"PERSON", "PHONE_NUMBER", "KE_PHONE", "EMAIL_ADDRESS", "LOCATION"}

_analyzer = None
_anonymizer = None
_llm_injection = None
_llm_secrets = None


def _engines():
    """Build the NLP engines once (spaCy + Presidio, and LLM Guard when enabled)."""
    global _analyzer, _anonymizer, _llm_injection, _llm_secrets
    if _analyzer is None:
        from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        from presidio_anonymizer import AnonymizerEngine

        nlp = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": SPACY_MODEL}],
            }
        ).create_engine()
        analyzer = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
        custom = [
            ("KE_PHONE", r"(?:\+254|\b0)(?:7|1)\d{8}\b", 0.7, []),
            ("KE_NATIONAL_ID", r"\b\d{7,8}\b", 0.3, ["id", "national", "idno", "identity"]),
            ("KRA_PIN", r"\b[AP]\d{9}[A-Z]\b", 0.8, []),
            ("MEDICAL_RECORD_NUMBER", r"\bMRN[-:\s]?\d{5,10}\b", 0.85, []),
        ]
        for entity, regex, score, context in custom:
            analyzer.registry.add_recognizer(
                PatternRecognizer(
                    supported_entity=entity,
                    patterns=[Pattern(name=entity.lower(), regex=regex, score=score)],
                    context=context,
                )
            )
        _analyzer = analyzer
        _anonymizer = AnonymizerEngine()
    if LLM_GUARD_ENABLED and _llm_injection is None:
        from llm_guard.input_scanners import PromptInjection, Secrets

        _llm_injection = PromptInjection(threshold=0.9)
        _llm_secrets = Secrets()
    return _analyzer, _anonymizer


def warm_up() -> None:
    """Called at image build time so models are downloaded into the image, not at runtime."""
    _engines()
    check_input("warm up the guardrails")


@dataclass
class Verdict:
    allowed: bool
    reason: str | None = None
    entities: list[str] = field(default_factory=list)
    text: str = ""
    masked: int = 0


def check_input(prompt: str) -> Verdict:
    analyzer, anonymizer = _engines()

    if INJECTION_HEURISTICS.search(prompt):
        return Verdict(False, "prompt_injection")
    if _llm_injection is not None and not _llm_injection.scan(prompt)[1]:
        return Verdict(False, "prompt_injection")

    if SECRET_PATTERNS.search(prompt):
        return Verdict(False, "secret_detected")
    if _llm_secrets is not None and not _llm_secrets.scan(prompt)[1]:
        return Verdict(False, "secret_detected")

    findings = analyzer.analyze(text=prompt, language="en", score_threshold=SCORE_THRESHOLD)
    hard = sorted({f.entity_type for f in findings if f.entity_type in BLOCK_ENTITIES})
    if hard:
        return Verdict(False, "phi_detected", entities=hard)

    soft = [f for f in findings if f.entity_type in MASK_ENTITIES]
    masked = anonymizer.anonymize(text=prompt, analyzer_results=soft).text if soft else prompt
    return Verdict(True, text=masked, masked=len(soft), entities=sorted({f.entity_type for f in soft}))


def clean_output(answer: str) -> tuple[str, int]:
    analyzer, anonymizer = _engines()
    found = [
        f
        for f in analyzer.analyze(text=answer, language="en", score_threshold=SCORE_THRESHOLD)
        if f.entity_type in MASK_ENTITIES | BLOCK_ENTITIES
    ]
    if not found:
        return answer, 0
    return anonymizer.anonymize(text=answer, analyzer_results=found).text, len(found)
